#include <Arduino.h>
#include <Servo.h>

/*
  PedalServoStrengthTest

  Simple bench sketch for one question only:
  can this servo push the sustain pedal down and release it cleanly?

  Behavior:
  - homes the servo to pedal-up
  - runs a few direct full-speed down/up cycles
  - leaves the servo at pedal-up when finished

  Serial monitor commands:
    r = run the full test again
    d = move and hold pedal-down
    u = move and hold pedal-up
    ? = print help
*/

static const uint8_t PEDAL_SERVO_PIN = 2;
static const uint8_t COMMAND_MARK_PIN = LED_BUILTIN;
static const uint32_t SERIAL_BAUD = 115200;

static const uint8_t PEDAL_UP_ANGLE_DEG = 0;
static const uint8_t PEDAL_DOWN_ANGLE_DEG = 180;

static const uint8_t TEST_CYCLE_COUNT = 6;
static const uint16_t STARTUP_SETTLE_MS = 1500;
static const uint16_t PEDAL_DOWN_HOLD_MS = 1200;
static const uint16_t PEDAL_UP_HOLD_MS = 1000;
static const uint16_t COMMAND_MARK_MS = 60;

Servo pedalServo;

void flashCommandMark() {
  digitalWrite(COMMAND_MARK_PIN, HIGH);
  delay(COMMAND_MARK_MS);
  digitalWrite(COMMAND_MARK_PIN, LOW);
}

void writeServoAngle(uint8_t angleDeg) {
  pedalServo.write(angleDeg);
}

void moveAndHold(const char *label, uint8_t angleDeg, uint16_t holdMs) {
  Serial.print("COMMAND ");
  Serial.print(label);
  Serial.print(" angle=");
  Serial.print(angleDeg);
  Serial.print(" hold_ms=");
  Serial.println(holdMs);

  flashCommandMark();
  writeServoAngle(angleDeg);
  delay(holdMs);
}

void printHelp() {
  Serial.println(F("READY PEDAL_SERVO_STRENGTH_TEST"));
  Serial.println(F("Commands:"));
  Serial.println(F("  r = run the strength test again"));
  Serial.println(F("  d = move and hold pedal-down"));
  Serial.println(F("  u = move and hold pedal-up"));
  Serial.println(F("  ? = print this help"));
  Serial.println(F("The automatic startup test runs direct full-speed down/up cycles."));
}

void homeServo() {
  writeServoAngle(PEDAL_UP_ANGLE_DEG);
  delay(STARTUP_SETTLE_MS);
}

void runStrengthCycles() {
  Serial.println();
  Serial.println(F("Starting pedal strength test."));
  Serial.print(F("Cycles: "));
  Serial.println(TEST_CYCLE_COUNT);
  Serial.print(F("Down hold: "));
  Serial.print(PEDAL_DOWN_HOLD_MS);
  Serial.println(F(" ms"));
  Serial.print(F("Up hold: "));
  Serial.print(PEDAL_UP_HOLD_MS);
  Serial.println(F(" ms"));

  for (uint8_t cycle = 1; cycle <= TEST_CYCLE_COUNT; cycle++) {
    Serial.println();
    Serial.print(F("Cycle "));
    Serial.print(cycle);
    Serial.print(F(" of "));
    Serial.println(TEST_CYCLE_COUNT);

    moveAndHold("DOWN", PEDAL_DOWN_ANGLE_DEG, PEDAL_DOWN_HOLD_MS);
    moveAndHold("UP", PEDAL_UP_ANGLE_DEG, PEDAL_UP_HOLD_MS);
  }

  Serial.println();
  Serial.println(F("Strength test complete. Servo left at pedal-up."));
}

void setup() {
  pinMode(COMMAND_MARK_PIN, OUTPUT);
  digitalWrite(COMMAND_MARK_PIN, LOW);

  Serial.begin(SERIAL_BAUD);
  delay(50);

  pedalServo.attach(PEDAL_SERVO_PIN);
  homeServo();
  printHelp();
  runStrengthCycles();
}

void loop() {
  if (Serial.available() <= 0) {
    return;
  }

  const char command = (char)Serial.read();
  if (command == 'r' || command == 'R') {
    runStrengthCycles();
    return;
  }
  if (command == 'd' || command == 'D') {
    moveAndHold("DOWN", PEDAL_DOWN_ANGLE_DEG, PEDAL_DOWN_HOLD_MS);
    return;
  }
  if (command == 'u' || command == 'U') {
    moveAndHold("UP", PEDAL_UP_ANGLE_DEG, PEDAL_UP_HOLD_MS);
    return;
  }
  if (command == '?') {
    printHelp();
  }
}
