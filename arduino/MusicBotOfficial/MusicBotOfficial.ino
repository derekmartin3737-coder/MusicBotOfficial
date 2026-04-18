/*
  MusicBotOfficial Arduino runtime

  This is the sketch that should stay uploaded to the Arduino Uno during normal
  piano playback. Python sends it a stream of timestamped PCA9685 PWM events over
  USB serial. The sketch does not understand MIDI directly; it only receives
  already-converted commands such as BEGIN, EVENT, COMMIT, PLAY, FIRE, and
  ALL_OFF.

  Hardware path:
    Arduino Uno A4/A5 I2C -> PCA9685 PWM boards -> MOSFET driver board -> solenoids

  Safety note:
    ALL_OFF sets every PCA9685 output on every board to zero. Use it whenever a test is
    stopped, a serial error occurs, or a solenoid sounds like it is being held.
*/

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// PCA9685 addresses/frequency must match config/piano_config.json on the Python side.
static const uint8_t RUNTIME_PCA_BOARD_COUNT = 4;
static const uint8_t RUNTIME_PCA_CHANNELS_PER_BOARD = 16;
static const uint8_t RUNTIME_GLOBAL_CHANNEL_COUNT =
    RUNTIME_PCA_BOARD_COUNT * RUNTIME_PCA_CHANNELS_PER_BOARD;
static const uint8_t RUNTIME_PCA9685_I2C_ADDRESSES[RUNTIME_PCA_BOARD_COUNT] = {
    0x40,
    0x41,
    0x42,
    0x43,
};
static const uint16_t RUNTIME_PCA9685_PWM_FREQUENCY_HZ = 250;
static const uint32_t RUNTIME_SERIAL_BAUD = 115200;
static const uint8_t RUNTIME_PROTOCOL_VERSION = 4;

// Small RAM buffer for streamed events. Python keeps refilling this while
// playback is running so the Uno does not need to store an entire song.
static const uint8_t EVENT_BUFFER_CAPACITY = 48;
static const uint16_t LINE_BUFFER_SIZE = 96;

// One low-level actuator event: wait dt_ms, then set one global channel to pwm.
// Global channel 0-63 is translated into a PCA9685 board plus its local channel.
// pwm = 0 releases the solenoid, higher values create strike/hold force.
typedef struct {
  uint32_t dt_ms;
  uint8_t channel;
  uint16_t pwm;
} SolenoidEvent;

Adafruit_PWMServoDriver pwmBoards[RUNTIME_PCA_BOARD_COUNT] = {
    Adafruit_PWMServoDriver(RUNTIME_PCA9685_I2C_ADDRESSES[0]),
    Adafruit_PWMServoDriver(RUNTIME_PCA9685_I2C_ADDRESSES[1]),
    Adafruit_PWMServoDriver(RUNTIME_PCA9685_I2C_ADDRESSES[2]),
    Adafruit_PWMServoDriver(RUNTIME_PCA9685_I2C_ADDRESSES[3]),
};

// Circular queue used between serial loading and timed playback.
SolenoidEvent eventBuffer[EVENT_BUFFER_CAPACITY];
uint8_t bufferHead = 0;
uint8_t bufferTail = 0;
uint8_t bufferedEventCount = 0;

// Counters let Python ask STATUS and decide when to send more events.
uint32_t expectedSongEventCount = 0;
uint32_t receivedSongEventCount = 0;
uint32_t playedSongEventCount = 0;

// transferActive means Python is still loading a song. playbackActive means
// millis()-based timing is currently applying PWM events to the hardware.
bool transferActive = false;
bool playbackActive = false;
bool dueTimeArmed = false;

uint32_t nextEventDueAtMs = 0;
uint32_t lastEventDueAtMs = 0;

char lineBuffer[LINE_BUFFER_SIZE];
uint8_t lineLength = 0;

uint8_t freeEventSlots() {
  return EVENT_BUFFER_CAPACITY - bufferedEventCount;
}

void allChannelsOff() {
  // Turn every output off on every PCA9685 board, even if the current build
  // only wires some channels. This is the safest stop state.
  for (uint8_t boardIndex = 0; boardIndex < RUNTIME_PCA_BOARD_COUNT; boardIndex++) {
    for (uint8_t channel = 0; channel < RUNTIME_PCA_CHANNELS_PER_BOARD; channel++) {
      pwmBoards[boardIndex].setPWM(channel, 0, 0);
    }
  }
}

bool probeI2cAddress(uint8_t address) {
  Wire.beginTransmission(address);
  return Wire.endTransmission() == 0;
}

void printAddressList(const uint8_t *addresses, uint8_t count) {
  if (count == 0) {
    Serial.print(F("none"));
    return;
  }

  for (uint8_t index = 0; index < count; index++) {
    if (index > 0) {
      Serial.print(',');
    }
    if (addresses[index] < 0x10) {
      Serial.print(F("0x0"));
    } else {
      Serial.print(F("0x"));
    }
    Serial.print(addresses[index], HEX);
  }
}

void sendI2cStatus() {
  uint8_t detectedAddresses[RUNTIME_PCA_BOARD_COUNT];
  uint8_t missingAddresses[RUNTIME_PCA_BOARD_COUNT];
  uint8_t detectedCount = 0;
  uint8_t missingCount = 0;

  for (uint8_t boardIndex = 0; boardIndex < RUNTIME_PCA_BOARD_COUNT; boardIndex++) {
    uint8_t address = RUNTIME_PCA9685_I2C_ADDRESSES[boardIndex];
    if (probeI2cAddress(address)) {
      detectedAddresses[detectedCount++] = address;
    } else {
      missingAddresses[missingCount++] = address;
    }
  }

  Serial.print(F("I2C detected="));
  printAddressList(detectedAddresses, detectedCount);
  Serial.print(F(" expected="));
  printAddressList(RUNTIME_PCA9685_I2C_ADDRESSES, RUNTIME_PCA_BOARD_COUNT);
  Serial.print(F(" missing="));
  printAddressList(missingAddresses, missingCount);
  Serial.print(F(" count="));
  Serial.println(detectedCount);
}

void setGlobalChannelPwm(uint8_t globalChannel, uint16_t pwmValue) {
  if (globalChannel >= RUNTIME_GLOBAL_CHANNEL_COUNT) {
    return;
  }

  uint8_t boardIndex = globalChannel / RUNTIME_PCA_CHANNELS_PER_BOARD;
  uint8_t localChannel = globalChannel % RUNTIME_PCA_CHANNELS_PER_BOARD;
  pwmBoards[boardIndex].setPWM(localChannel, 0, pwmValue);
}

void resetEventQueue() {
  bufferHead = 0;
  bufferTail = 0;
  bufferedEventCount = 0;
}

void resetSongState(bool stopOutputs) {
  playbackActive = false;
  dueTimeArmed = false;
  transferActive = false;
  expectedSongEventCount = 0;
  receivedSongEventCount = 0;
  playedSongEventCount = 0;
  nextEventDueAtMs = 0;
  lastEventDueAtMs = 0;
  resetEventQueue();
  if (stopOutputs) {
    allChannelsOff();
  }
}

bool enqueueEvent(const SolenoidEvent &eventIn) {
  // Returns false instead of overwriting old events if Python sends too quickly.
  if (bufferedEventCount >= EVENT_BUFFER_CAPACITY) {
    return false;
  }

  eventBuffer[bufferTail] = eventIn;
  bufferTail = (uint8_t)((bufferTail + 1) % EVENT_BUFFER_CAPACITY);
  bufferedEventCount++;
  return true;
}

bool dequeueEvent(SolenoidEvent *eventOut) {
  if (bufferedEventCount == 0) {
    return false;
  }

  *eventOut = eventBuffer[bufferHead];
  bufferHead = (uint8_t)((bufferHead + 1) % EVENT_BUFFER_CAPACITY);
  bufferedEventCount--;
  return true;
}

bool peekEvent(SolenoidEvent *eventOut) {
  if (bufferedEventCount == 0) {
    return false;
  }

  *eventOut = eventBuffer[bufferHead];
  return true;
}

void sendReady() {
  Serial.print(F("READY "));
  Serial.print(RUNTIME_PROTOCOL_VERSION);
  Serial.print(F(" BUFFER "));
  Serial.println(EVENT_BUFFER_CAPACITY);
}

void sendOk(const __FlashStringHelper *message) {
  Serial.print(F("OK "));
  Serial.println(message);
}

void sendError(const __FlashStringHelper *message) {
  Serial.print(F("ERROR "));
  Serial.println(message);
}

const __FlashStringHelper *runtimeStateLabel() {
  if (playbackActive) {
    return F("PLAYING");
  }
  if (transferActive && receivedSongEventCount < expectedSongEventCount) {
    return F("LOADING");
  }
  if (expectedSongEventCount > 0 &&
      playedSongEventCount >= expectedSongEventCount &&
      bufferedEventCount == 0) {
    return F("DONE");
  }
  if (expectedSongEventCount > 0 || receivedSongEventCount > 0) {
    return F("READY");
  }
  return F("IDLE");
}

void sendStatus() {
  Serial.print(F("STATUS "));
  Serial.print(runtimeStateLabel());
  Serial.print(F(" recv="));
  Serial.print(receivedSongEventCount);
  Serial.print(F(" played="));
  Serial.print(playedSongEventCount);
  Serial.print(F(" buffered="));
  Serial.print(bufferedEventCount);
  Serial.print(F(" free="));
  Serial.print(freeEventSlots());
  Serial.print(F(" total="));
  Serial.println(expectedSongEventCount);
}

bool parseEventLine(const char *line, SolenoidEvent *eventOut) {
  // EVENT lines come from Python in the form: EVENT <dt_ms> <global_channel> <pwm>.
  unsigned long dtValue = 0;
  unsigned int channelValue = 0;
  unsigned int pwmValue = 0;
  int parsed = sscanf(line, "EVENT %lu %u %u", &dtValue, &channelValue, &pwmValue);
  if (parsed != 3) {
    return false;
  }
  if (channelValue >= RUNTIME_GLOBAL_CHANNEL_COUNT || pwmValue > 4095) {
    return false;
  }

  eventOut->dt_ms = (uint32_t)dtValue;
  eventOut->channel = (uint8_t)channelValue;
  eventOut->pwm = (uint16_t)pwmValue;
  return true;
}

bool parseFireLine(
    const char *line,
    uint8_t *channelOut,
    uint16_t *strikePwmOut,
    uint16_t *holdPwmOut,
    uint16_t *strikeMsOut,
    uint16_t *holdMsOut,
    uint16_t *releaseMsOut) {
  unsigned int channelValue = 0;
  unsigned int strikePwmValue = 0;
  unsigned int holdPwmValue = 0;
  unsigned int strikeMsValue = 0;
  unsigned int holdMsValue = 0;
  unsigned int releaseMsValue = 0;

  // FIRE is a calibration-only helper used by scripts/piano_tools.py.
  // It performs one strike/hold/release pulse without loading a song.
  int parsed = sscanf(
      line,
      "FIRE %u %u %u %u %u %u",
      &channelValue,
      &strikePwmValue,
      &holdPwmValue,
      &strikeMsValue,
      &holdMsValue,
      &releaseMsValue);

  if (parsed != 6) {
    return false;
  }
  if (channelValue >= RUNTIME_GLOBAL_CHANNEL_COUNT || strikePwmValue > 4095 ||
      holdPwmValue > 4095) {
    return false;
  }

  *channelOut = (uint8_t)channelValue;
  *strikePwmOut = (uint16_t)strikePwmValue;
  *holdPwmOut = (uint16_t)holdPwmValue;
  *strikeMsOut = (uint16_t)strikeMsValue;
  *holdMsOut = (uint16_t)holdMsValue;
  *releaseMsOut = (uint16_t)releaseMsValue;
  return true;
}

void performCalibrationFire(
    uint8_t channel,
    uint16_t strikePwm,
    uint16_t holdPwm,
    uint16_t strikeMs,
    uint16_t holdMs,
    uint16_t releaseMs) {
  // A test pulse is intentionally blocking. It is only used outside playback
  // while a person is listening/watching one channel at a time.
  setGlobalChannelPwm(channel, strikePwm);
  delay(strikeMs);

  if (holdMs > 0 && holdPwm > 0) {
    setGlobalChannelPwm(channel, holdPwm);
    delay(holdMs);
  }

  setGlobalChannelPwm(channel, 0);
  if (releaseMs > 0) {
    delay(releaseMs);
  }
}

void armDueTimeFromBufferedHead() {
  // The queue stores relative delays. Once an event reaches the head of the
  // queue, convert that delay into an absolute millis() deadline.
  if (!playbackActive || dueTimeArmed || bufferedEventCount == 0) {
    return;
  }

  SolenoidEvent nextEvent;
  if (!peekEvent(&nextEvent)) {
    return;
  }

  if (playedSongEventCount == 0) {
    nextEventDueAtMs = millis() + nextEvent.dt_ms;
  } else {
    nextEventDueAtMs = lastEventDueAtMs + nextEvent.dt_ms;
  }
  dueTimeArmed = true;
}

void finishPlayback() {
  playbackActive = false;
  dueTimeArmed = false;
  allChannelsOff();
  sendOk(F("PLAYBACK_DONE"));
}

void beginPlayback() {
  if (receivedSongEventCount == 0 || bufferedEventCount == 0) {
    sendError(F("NO_SONG"));
    return;
  }

  playbackActive = true;
  dueTimeArmed = false;
  armDueTimeFromBufferedHead();
  sendOk(F("PLAYING"));
}

void handleCommand(const char *line) {
  // Text protocol used by Python:
  // HELLO/STATUS inspect the runtime, BEGIN/EVENT/COMMIT load events,
  // PLAY starts timed output, and STOP/CLEAR/ALL_OFF recover to a safe state.
  if (strcmp(line, "PING") == 0) {
    Serial.println(F("PONG"));
    return;
  }

  if (strcmp(line, "HELLO") == 0) {
    sendReady();
    return;
  }

  if (strcmp(line, "HELP") == 0) {
    Serial.println(
        F("OK COMMANDS HELLO PING STATUS I2C BEGIN EVENT COMMIT PLAY STOP CLEAR FIRE ALL_OFF"));
    return;
  }

  if (strcmp(line, "I2C") == 0) {
    sendI2cStatus();
    return;
  }

  if (strcmp(line, "ALL_OFF") == 0) {
    allChannelsOff();
    sendOk(F("ALL_OFF"));
    return;
  }

  if (strcmp(line, "STOP") == 0) {
    playbackActive = false;
    dueTimeArmed = false;
    allChannelsOff();
    sendOk(F("STOPPED"));
    return;
  }

  if (strcmp(line, "CLEAR") == 0) {
    resetSongState(true);
    sendOk(F("CLEARED"));
    return;
  }

  if (strcmp(line, "STATUS") == 0) {
    sendStatus();
    return;
  }

  unsigned long requestedCount = 0;
  if (sscanf(line, "BEGIN %lu", &requestedCount) == 1) {
    resetSongState(true);
    if (requestedCount == 0) {
      sendError(F("EMPTY_SONG"));
      return;
    }
    transferActive = true;
    expectedSongEventCount = (uint32_t)requestedCount;
    Serial.print(F("OK BEGIN capacity="));
    Serial.print(EVENT_BUFFER_CAPACITY);
    Serial.print(F(" total="));
    Serial.println(expectedSongEventCount);
    return;
  }

  if (strncmp(line, "EVENT ", 6) == 0) {
    if (!transferActive) {
      sendError(F("BEGIN_REQUIRED"));
      return;
    }
    if (receivedSongEventCount >= expectedSongEventCount) {
      sendError(F("EVENT_OVERFLOW"));
      return;
    }
    if (bufferedEventCount >= EVENT_BUFFER_CAPACITY) {
      sendError(F("BUFFER_FULL"));
      return;
    }

    SolenoidEvent parsedEvent;
    if (!parseEventLine(line, &parsedEvent)) {
      sendError(F("BAD_EVENT"));
      return;
    }

    if (!enqueueEvent(parsedEvent)) {
      sendError(F("BUFFER_FULL"));
      return;
    }
    receivedSongEventCount++;
    armDueTimeFromBufferedHead();
    return;
  }

  if (strcmp(line, "COMMIT") == 0) {
    Serial.print(F("OK ACCEPTED recv="));
    Serial.print(receivedSongEventCount);
    Serial.print(F(" free="));
    Serial.print(freeEventSlots());
    Serial.print(F(" total="));
    Serial.println(expectedSongEventCount);
    return;
  }

  if (strcmp(line, "PLAY") == 0) {
    beginPlayback();
    return;
  }

  if (strncmp(line, "FIRE ", 5) == 0) {
    if (playbackActive) {
      sendError(F("BUSY"));
      return;
    }

    uint8_t channel = 0;
    uint16_t strikePwm = 0;
    uint16_t holdPwm = 0;
    uint16_t strikeMs = 0;
    uint16_t holdMs = 0;
    uint16_t releaseMs = 0;
    if (!parseFireLine(
            line,
            &channel,
            &strikePwm,
            &holdPwm,
            &strikeMs,
            &holdMs,
            &releaseMs)) {
      sendError(F("BAD_FIRE"));
      return;
    }

    performCalibrationFire(channel, strikePwm, holdPwm, strikeMs, holdMs, releaseMs);
    sendOk(F("FIRED"));
    return;
  }

  sendError(F("UNKNOWN_COMMAND"));
}

void pollSerial() {
  // Build one newline-terminated command at a time without using dynamic String
  // allocation. That keeps RAM use predictable on the Uno.
  while (Serial.available() > 0) {
    char incoming = (char)Serial.read();
    if (incoming == '\r') {
      continue;
    }

    if (incoming == '\n') {
      lineBuffer[lineLength] = '\0';
      if (lineLength > 0) {
        handleCommand(lineBuffer);
      }
      lineLength = 0;
      continue;
    }

    if (lineLength < LINE_BUFFER_SIZE - 1) {
      lineBuffer[lineLength++] = incoming;
    } else {
      lineLength = 0;
      sendError(F("LINE_TOO_LONG"));
    }
  }
}

void servicePlayback() {
  // Called continuously from loop(). It applies every event whose scheduled time
  // has arrived, including multiple zero-delay events for simultaneous notes.
  if (!playbackActive) {
    return;
  }

  armDueTimeFromBufferedHead();
  if (!dueTimeArmed) {
    if (expectedSongEventCount > 0 &&
        playedSongEventCount >= expectedSongEventCount &&
        bufferedEventCount == 0) {
      finishPlayback();
    }
    return;
  }

  uint32_t now = millis();
  if ((int32_t)(now - nextEventDueAtMs) < 0) {
    return;
  }

  while (playbackActive) {
    SolenoidEvent event;
    if (!dequeueEvent(&event)) {
      dueTimeArmed = false;
      return;
    }

    setGlobalChannelPwm(event.channel, event.pwm);
    playedSongEventCount++;
    lastEventDueAtMs = nextEventDueAtMs;
    dueTimeArmed = false;

    if (expectedSongEventCount > 0 &&
        playedSongEventCount >= expectedSongEventCount &&
        bufferedEventCount == 0 &&
        receivedSongEventCount >= expectedSongEventCount) {
      finishPlayback();
      return;
    }

    armDueTimeFromBufferedHead();
    if (!dueTimeArmed) {
      return;
    }
    if ((int32_t)(now - nextEventDueAtMs) < 0) {
      return;
    }
  }
}

void setup() {
  // The runtime starts with all outputs off before it announces READY.
  Wire.begin();
  for (uint8_t boardIndex = 0; boardIndex < RUNTIME_PCA_BOARD_COUNT; boardIndex++) {
    pwmBoards[boardIndex].begin();
    pwmBoards[boardIndex].setPWMFreq(RUNTIME_PCA9685_PWM_FREQUENCY_HZ);
  }
  allChannelsOff();

  Serial.begin(RUNTIME_SERIAL_BAUD);
  while (!Serial) {
    ;  // Wait for native USB boards; no-op on Uno after startup.
  }
  delay(50);
  sendReady();
}

void loop() {
  // Serial loading and timed playback are both non-blocking during normal songs.
  pollSerial();
  servicePlayback();
}
