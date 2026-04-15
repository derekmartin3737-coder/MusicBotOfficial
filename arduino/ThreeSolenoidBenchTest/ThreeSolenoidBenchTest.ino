/*
  ThreeSolenoidBenchTest

  Early hardware demo for C/D/E solenoids. This sketch does not use Python or
  MIDI; it loops through simple single notes and C+E chords to prove that
  multiple PCA9685 channels can be actuated with different strike strengths.
*/

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

static const uint8_t BENCH_PCA9685_I2C_ADDRESS = 0x40;
static const uint16_t BENCH_PCA9685_PWM_FREQUENCY_HZ = 250;

static const uint8_t CHANNEL_C = 0;  // 25N solenoid
static const uint8_t CHANNEL_D = 1;  // 5N solenoid
static const uint8_t CHANNEL_E = 2;  // 5N solenoid

static const uint16_t STRIKE_MS = 38;
static const uint16_t HOLD_MS = 130;
static const uint16_t RELEASE_MS = 220;

static const uint16_t C_SOFT = 3100;
static const uint16_t C_MEDIUM = 3600;
static const uint16_t C_HARD = 4095;
static const uint16_t C_HOLD = 2200;

static const uint16_t DE_SOFT = 2300;
static const uint16_t DE_MEDIUM = 2900;
static const uint16_t DE_HARD = 3500;
static const uint16_t DE_HOLD = 1650;

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(BENCH_PCA9685_I2C_ADDRESS);

void setChannelPwm(uint8_t channel, uint16_t pwmValue) {
  pwm.setPWM(channel, 0, pwmValue);
}

void allOff() {
  setChannelPwm(CHANNEL_C, 0);
  setChannelPwm(CHANNEL_D, 0);
  setChannelPwm(CHANNEL_E, 0);
}

void playSingle(uint8_t channel, uint16_t strikePwm, uint16_t holdPwm) {
  setChannelPwm(channel, strikePwm);
  delay(STRIKE_MS);
  setChannelPwm(channel, holdPwm);
  delay(HOLD_MS);
  setChannelPwm(channel, 0);
  delay(RELEASE_MS);
}

void playChordCE(uint16_t cStrike, uint16_t eStrike, uint16_t cHold, uint16_t eHold) {
  // Starting both channels before the delay makes the C and E strikes happen as
  // close together as possible for a simple Arduino loop demo.
  setChannelPwm(CHANNEL_C, cStrike);
  setChannelPwm(CHANNEL_E, eStrike);
  delay(STRIKE_MS);
  setChannelPwm(CHANNEL_C, cHold);
  setChannelPwm(CHANNEL_E, eHold);
  delay(HOLD_MS);
  setChannelPwm(CHANNEL_C, 0);
  setChannelPwm(CHANNEL_E, 0);
  delay(RELEASE_MS);
}

void setup() {
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(BENCH_PCA9685_PWM_FREQUENCY_HZ);
  delay(10);
  allOff();
}

void loop() {
  playSingle(CHANNEL_C, C_SOFT, C_HOLD);
  playSingle(CHANNEL_D, DE_MEDIUM, DE_HOLD);
  playSingle(CHANNEL_E, DE_HARD, DE_HOLD);

  playChordCE(C_MEDIUM, DE_MEDIUM, C_HOLD, DE_HOLD);
  playChordCE(C_HARD, DE_HARD, C_HOLD, DE_HOLD);

  playSingle(CHANNEL_E, DE_MEDIUM, DE_HOLD);
  playSingle(CHANNEL_D, DE_MEDIUM, DE_HOLD);
  playSingle(CHANNEL_C, C_MEDIUM, C_HOLD);

  delay(1200);
}
