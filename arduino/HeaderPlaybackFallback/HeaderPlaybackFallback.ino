/*
  HeaderPlaybackFallback

  Backup sketch for playing a generated song header directly from Arduino flash
  memory. The preferred workflow is the serial runtime in
  arduino/MusicBotOfficial/MusicBotOfficial.ino, but this fallback is useful if
  Python streaming is unavailable and a pre-generated song header already exists.

  The include below points at a tracked sample song so this sketch compiles from
  a fresh GitHub clone. To test a different exported header, change only this
  include line locally.
*/

#include <Arduino.h>
#include <Wire.h>
#include <avr/pgmspace.h>
#include <Adafruit_PWMServoDriver.h>

#include "../MusicBotOfficial/generated/CDE_Dynamics_Etude.h"

Adafruit_PWMServoDriver pwmBoards[SONG_PCA9685_MAX_BOARD_COUNT] = {
    Adafruit_PWMServoDriver(SONG_PCA9685_BOARD_ADDRESSES[0]),
    Adafruit_PWMServoDriver(SONG_PCA9685_BOARD_ADDRESSES[1]),
    Adafruit_PWMServoDriver(SONG_PCA9685_BOARD_ADDRESSES[2]),
    Adafruit_PWMServoDriver(SONG_PCA9685_BOARD_ADDRESSES[3]),
};

void setGlobalChannelPwm(uint8_t globalChannel, uint16_t pwmValue) {
  uint8_t boardIndex = globalChannel / 16;
  uint8_t localChannel = globalChannel % 16;
  if (boardIndex >= SONG_PCA9685_BOARD_COUNT) {
    return;
  }
  pwmBoards[boardIndex].setPWM(localChannel, 0, pwmValue);
}

void allChannelsOff() {
  for (uint8_t i = 0; i < SONG_CHANNEL_COUNT; i++) {
    setGlobalChannelPwm(SONG_CHANNELS[i], 0);
  }
}

void setup() {
  Wire.begin();
  for (uint8_t boardIndex = 0; boardIndex < SONG_PCA9685_BOARD_COUNT; boardIndex++) {
    pwmBoards[boardIndex].begin();
    pwmBoards[boardIndex].setPWMFreq(SONG_PCA9685_PWM_FREQUENCY_HZ);
  }
  delay(10);
  allChannelsOff();
}

void playSongOnce() {
  uint32_t i = 0;

  while (i < SONG_EVENT_COUNT) {
    SolenoidEvent e;
    // SONG lives in flash/PROGMEM, so copy each event into RAM before using it.
    memcpy_P(&e, &SONG[i], sizeof(SolenoidEvent));

    delay(e.dt_ms);
    setGlobalChannelPwm(e.channel, e.pwm);
    i++;

    while (i < SONG_EVENT_COUNT) {
      SolenoidEvent simultaneousEvent;
      memcpy_P(&simultaneousEvent, &SONG[i], sizeof(SolenoidEvent));
      // Consecutive zero-delay events are simultaneous notes/chords.
      if (simultaneousEvent.dt_ms != 0) {
        break;
      }
      setGlobalChannelPwm(simultaneousEvent.channel, simultaneousEvent.pwm);
      i++;
    }
  }

  allChannelsOff();
}

void loop() {
  playSongOnce();
  delay(2000);
}
