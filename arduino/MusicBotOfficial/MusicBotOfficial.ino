#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

static const uint8_t RUNTIME_PCA9685_I2C_ADDRESS = 0x40;
static const uint16_t RUNTIME_PCA9685_PWM_FREQUENCY_HZ = 250;
static const uint32_t RUNTIME_SERIAL_BAUD = 115200;
static const uint8_t RUNTIME_PROTOCOL_VERSION = 2;
static const uint8_t EVENT_BUFFER_CAPACITY = 48;
static const uint16_t LINE_BUFFER_SIZE = 96;

typedef struct {
  uint32_t dt_ms;
  uint8_t channel;
  uint16_t pwm;
} SolenoidEvent;

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(RUNTIME_PCA9685_I2C_ADDRESS);

SolenoidEvent eventBuffer[EVENT_BUFFER_CAPACITY];
uint8_t bufferHead = 0;
uint8_t bufferTail = 0;
uint8_t bufferedEventCount = 0;

uint32_t expectedSongEventCount = 0;
uint32_t receivedSongEventCount = 0;
uint32_t playedSongEventCount = 0;

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
  for (uint8_t channel = 0; channel < 16; channel++) {
    pwm.setPWM(channel, 0, 0);
  }
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
  unsigned long dtValue = 0;
  unsigned int channelValue = 0;
  unsigned int pwmValue = 0;
  int parsed = sscanf(line, "EVENT %lu %u %u", &dtValue, &channelValue, &pwmValue);
  if (parsed != 3) {
    return false;
  }
  if (channelValue > 15 || pwmValue > 4095) {
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
  if (channelValue > 15 || strikePwmValue > 4095 || holdPwmValue > 4095) {
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
  pwm.setPWM(channel, 0, strikePwm);
  delay(strikeMs);

  if (holdMs > 0 && holdPwm > 0) {
    pwm.setPWM(channel, 0, holdPwm);
    delay(holdMs);
  }

  pwm.setPWM(channel, 0, 0);
  if (releaseMs > 0) {
    delay(releaseMs);
  }
}

void armDueTimeFromBufferedHead() {
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
        F("OK COMMANDS HELLO PING STATUS BEGIN EVENT COMMIT PLAY STOP CLEAR FIRE ALL_OFF"));
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

    pwm.setPWM(event.channel, 0, event.pwm);
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
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(RUNTIME_PCA9685_PWM_FREQUENCY_HZ);
  allChannelsOff();

  Serial.begin(RUNTIME_SERIAL_BAUD);
  while (!Serial) {
    ;  // Wait for native USB boards; no-op on Uno after startup.
  }
  delay(50);
  sendReady();
}

void loop() {
  pollSerial();
  servicePlayback();
}
