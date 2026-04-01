#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

static const uint8_t RUNTIME_PCA9685_I2C_ADDRESS = 0x40;
static const uint16_t RUNTIME_PCA9685_PWM_FREQUENCY_HZ = 250;
static const uint32_t RUNTIME_SERIAL_BAUD = 115200;
static const uint16_t MAX_SONG_EVENTS = 160;
static const uint16_t LINE_BUFFER_SIZE = 64;

typedef struct {
  uint32_t dt_ms;
  uint8_t channel;
  uint16_t pwm;
} SolenoidEvent;

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(RUNTIME_PCA9685_I2C_ADDRESS);

SolenoidEvent songEvents[MAX_SONG_EVENTS];
uint16_t songEventCount = 0;
uint16_t expectedSongEventCount = 0;
bool songLoaded = false;
bool playbackActive = false;
uint16_t playbackIndex = 0;
uint32_t nextEventDueAtMs = 0;
char lineBuffer[LINE_BUFFER_SIZE];
uint8_t lineLength = 0;

void allChannelsOff() {
  for (uint8_t channel = 0; channel < 16; channel++) {
    pwm.setPWM(channel, 0, 0);
  }
}

void stopPlayback() {
  playbackActive = false;
  playbackIndex = 0;
  nextEventDueAtMs = 0;
  allChannelsOff();
}

void clearSongBuffer() {
  stopPlayback();
  songEventCount = 0;
  expectedSongEventCount = 0;
  songLoaded = false;
}

void sendReady() {
  Serial.println(F("READY 1"));
}

void sendOk(const __FlashStringHelper* message) {
  Serial.print(F("OK "));
  Serial.println(message);
}

void sendError(const __FlashStringHelper* message) {
  Serial.print(F("ERROR "));
  Serial.println(message);
}

bool parseEventLine(const char* line, SolenoidEvent* eventOut) {
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

  eventOut->dt_ms = dtValue;
  eventOut->channel = (uint8_t)channelValue;
  eventOut->pwm = (uint16_t)pwmValue;
  return true;
}

void beginPlayback() {
  if (!songLoaded || songEventCount == 0) {
    sendError(F("NO_SONG"));
    return;
  }

  playbackActive = true;
  playbackIndex = 0;
  nextEventDueAtMs = millis() + songEvents[0].dt_ms;
  sendOk(F("PLAYING"));
}

void handleCommand(const char* line) {
  if (strcmp(line, "PING") == 0) {
    Serial.println(F("PONG"));
    return;
  }

  if (strcmp(line, "HELLO") == 0) {
    sendReady();
    return;
  }

  if (strcmp(line, "STOP") == 0) {
    stopPlayback();
    sendOk(F("STOPPED"));
    return;
  }

  if (strcmp(line, "CLEAR") == 0) {
    clearSongBuffer();
    sendOk(F("CLEARED"));
    return;
  }

  unsigned int requestedCount = 0;
  if (sscanf(line, "BEGIN %u", &requestedCount) == 1) {
    clearSongBuffer();
    if (requestedCount == 0) {
      sendError(F("EMPTY_SONG"));
      return;
    }
    if (requestedCount > MAX_SONG_EVENTS) {
      sendError(F("TOO_MANY_EVENTS"));
      return;
    }
    expectedSongEventCount = (uint16_t)requestedCount;
    sendOk(F("BEGIN"));
    return;
  }

  if (strncmp(line, "EVENT ", 6) == 0) {
    if (expectedSongEventCount == 0) {
      sendError(F("BEGIN_REQUIRED"));
      return;
    }
    if (songEventCount >= expectedSongEventCount || songEventCount >= MAX_SONG_EVENTS) {
      sendError(F("EVENT_OVERFLOW"));
      return;
    }

    SolenoidEvent parsedEvent;
    if (!parseEventLine(line, &parsedEvent)) {
      sendError(F("BAD_EVENT"));
      return;
    }

    songEvents[songEventCount] = parsedEvent;
    songEventCount++;
    if (songEventCount == expectedSongEventCount) {
      songLoaded = true;
      sendOk(F("SONG_LOADED"));
    }
    return;
  }

  if (strcmp(line, "PLAY") == 0) {
    if (expectedSongEventCount == 0 || songEventCount != expectedSongEventCount) {
      sendError(F("SONG_INCOMPLETE"));
      return;
    }
    songLoaded = true;
    beginPlayback();
    return;
  }

  if (strcmp(line, "STATUS") == 0) {
    Serial.print(F("STATUS "));
    Serial.print(playbackActive ? F("PLAYING") : F("IDLE"));
    Serial.print(F(" "));
    Serial.print(songEventCount);
    Serial.print(F("/"));
    Serial.println(expectedSongEventCount);
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
  if (!playbackActive || playbackIndex >= songEventCount) {
    return;
  }

  uint32_t now = millis();
  if ((int32_t)(now - nextEventDueAtMs) < 0) {
    return;
  }

  while (playbackIndex < songEventCount) {
    SolenoidEvent event = songEvents[playbackIndex];
    pwm.setPWM(event.channel, 0, event.pwm);
    playbackIndex++;

    if (playbackIndex >= songEventCount) {
      playbackActive = false;
      allChannelsOff();
      sendOk(F("PLAYBACK_DONE"));
      return;
    }

    nextEventDueAtMs += songEvents[playbackIndex].dt_ms;
    if (songEvents[playbackIndex].dt_ms != 0) {
      break;
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
