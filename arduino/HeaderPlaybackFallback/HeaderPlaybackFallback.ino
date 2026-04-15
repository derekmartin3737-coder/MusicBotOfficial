/*
  HeaderPlaybackFallback

  Backup sketch for playing the generated current_song.h directly from Arduino
  flash memory. The preferred workflow is the serial runtime in
  arduino/MusicBotOfficial/MusicBotOfficial.ino, but this fallback is useful if
  Python streaming is unavailable and a pre-generated song header already exists.
*/

#include <Arduino.h>
#include <Wire.h>
#include <avr/pgmspace.h>
#include <Adafruit_PWMServoDriver.h>

#include "../MusicBotOfficial/generated/current_song.h"

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(SONG_PCA9685_I2C_ADDRESS);

void allChannelsOff() {
  for (uint8_t i = 0; i < SONG_CHANNEL_COUNT; i++) {
    pwm.setPWM(SONG_CHANNELS[i], 0, 0);
  }
}

void setup() {
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(SONG_PCA9685_PWM_FREQUENCY_HZ);
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
    pwm.setPWM(e.channel, 0, e.pwm);
    i++;

    while (i < SONG_EVENT_COUNT) {
      SolenoidEvent simultaneousEvent;
      memcpy_P(&simultaneousEvent, &SONG[i], sizeof(SolenoidEvent));
      // Consecutive zero-delay events are simultaneous notes/chords.
      if (simultaneousEvent.dt_ms != 0) {
        break;
      }
      pwm.setPWM(simultaneousEvent.channel, 0, simultaneousEvent.pwm);
      i++;
    }
  }

  allChannelsOff();
}

void loop() {
  playSongOnce();
  delay(2000);
}
