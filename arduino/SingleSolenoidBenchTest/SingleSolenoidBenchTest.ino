/*
  SingleSolenoidBenchTest

  Upload this sketch only when validating one solenoid/PCA9685/MOSFET channel.
  It repeatedly fires channel 0 at soft, medium, and hard strike PWM values so
  the team can confirm wiring, flyback protection, and safe force ranges before
  running the full Python-controlled runtime.
*/

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

static const uint8_t BENCH_PCA9685_I2C_ADDRESS = 0x40;
static const uint16_t BENCH_PCA9685_PWM_FREQUENCY_HZ = 250;
static const uint8_t SOLENOID_CHANNEL = 0;

// Start conservatively and tune upward only if the solenoid does not move reliably.
static const uint16_t SOFT_STRIKE_PWM = 2600;
static const uint16_t MEDIUM_STRIKE_PWM = 3200;
static const uint16_t HARD_STRIKE_PWM = 3800;
static const uint16_t HOLD_PWM = 1800;

static const uint16_t STRIKE_MS = 35;
static const uint16_t HOLD_MS = 180;
static const uint16_t RELEASE_MS = 500;

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(BENCH_PCA9685_I2C_ADDRESS);

void setSolenoidPwm(uint16_t pwmValue) {
  pwm.setPWM(SOLENOID_CHANNEL, 0, pwmValue);
}

void allOff() {
  setSolenoidPwm(0);
}

void playTestNote(uint16_t strikePwm, uint16_t strikeMs, uint16_t holdPwm, uint16_t holdMs, uint16_t releaseMs) {
  // Each note uses a strong strike, a lower hold, then a full release.
  setSolenoidPwm(strikePwm);
  delay(strikeMs);

  setSolenoidPwm(holdPwm);
  delay(holdMs);

  allOff();
  delay(releaseMs);
}

void setup() {
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(BENCH_PCA9685_PWM_FREQUENCY_HZ);
  delay(10);
  allOff();
}

void loop() {
  playTestNote(SOFT_STRIKE_PWM, STRIKE_MS, HOLD_PWM, HOLD_MS, RELEASE_MS);
  playTestNote(MEDIUM_STRIKE_PWM, STRIKE_MS, HOLD_PWM, HOLD_MS, RELEASE_MS);
  playTestNote(HARD_STRIKE_PWM, STRIKE_MS, HOLD_PWM, HOLD_MS, RELEASE_MS);

  delay(1500);
}
