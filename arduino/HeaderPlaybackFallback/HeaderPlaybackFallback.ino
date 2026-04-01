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
    memcpy_P(&e, &SONG[i], sizeof(SolenoidEvent));

    delay(e.dt_ms);
    pwm.setPWM(e.channel, 0, e.pwm);
    i++;

    while (i < SONG_EVENT_COUNT) {
      SolenoidEvent simultaneousEvent;
      memcpy_P(&simultaneousEvent, &SONG[i], sizeof(SolenoidEvent));
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
