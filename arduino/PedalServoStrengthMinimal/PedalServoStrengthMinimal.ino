#include <Servo.h>

static const int PEDAL_SERVO_PIN = 2;
static const int PEDAL_UP_ANGLE_DEG = 0;
static const int PEDAL_DOWN_ANGLE_DEG = 180;
static const unsigned long PEDAL_DOWN_HOLD_MS = 1200;
static const unsigned long PEDAL_UP_HOLD_MS = 1000;

Servo pedalServo;

void setup() {
  pedalServo.attach(PEDAL_SERVO_PIN);
}

void loop() {
  pedalServo.write(PEDAL_DOWN_ANGLE_DEG);
  delay(PEDAL_DOWN_HOLD_MS);

  pedalServo.write(PEDAL_UP_ANGLE_DEG);
  delay(PEDAL_UP_HOLD_MS);
}
