#include <Arduino.h>
#include <Servo.h>

// Bench test for the sustain-pedal servo.
// This sketch waits for serial commands from the Python reaction-time runner.
// The runner starts a move, you tap Space when the servo reaches the target,
// and the measured travel times are saved for pedal compensation later.

static const uint8_t PEDAL_SERVO_PIN = 2;
static const uint8_t COMMAND_MARK_PIN = LED_BUILTIN;
static const uint32_t SERIAL_BAUD = 115200;

// Default full-range test requested for the microservo.
// Reduce these if your linkage binds or the servo buzzes hard at the stops.
static const uint8_t PEDAL_UP_ANGLE_DEG = 0;
static const uint8_t PEDAL_DOWN_ANGLE_DEG = 180;

static const uint16_t STARTUP_SETTLE_MS = 1500;
static const uint16_t COMMAND_MARK_MS = 60;

Servo pedalServo;
bool isHomed = false;

void flashCommandMark() {
  digitalWrite(COMMAND_MARK_PIN, HIGH);
  delay(COMMAND_MARK_MS);
  digitalWrite(COMMAND_MARK_PIN, LOW);
}

void moveServoAndAcknowledge(const __FlashStringHelper *label, uint8_t angleDeg) {
  flashCommandMark();
  pedalServo.write(angleDeg);

  Serial.print(F("OK "));
  Serial.print(label);
  Serial.print(F(" angle="));
  Serial.print(angleDeg);
  Serial.print(F(" ms="));
  Serial.println(millis());
}

void homeServo() {
  pedalServo.write(PEDAL_UP_ANGLE_DEG);
  isHomed = true;
  delay(STARTUP_SETTLE_MS);
}

void handleCommand(const String &command) {
  if (command == "PING") {
    Serial.println(F("PONG"));
    return;
  }

  if (command == "STATUS") {
    Serial.print(F("STATUS homed="));
    Serial.print(isHomed ? F("yes") : F("no"));
    Serial.print(F(" up="));
    Serial.print(PEDAL_UP_ANGLE_DEG);
    Serial.print(F(" down="));
    Serial.println(PEDAL_DOWN_ANGLE_DEG);
    return;
  }

  if (command == "HOME") {
    homeServo();
    Serial.print(F("OK HOME angle="));
    Serial.println(PEDAL_UP_ANGLE_DEG);
    return;
  }

  if (command == "MOVE DOWN") {
    moveServoAndAcknowledge(F("MOVE_DOWN"), PEDAL_DOWN_ANGLE_DEG);
    return;
  }

  if (command == "MOVE UP") {
    moveServoAndAcknowledge(F("MOVE_UP"), PEDAL_UP_ANGLE_DEG);
    return;
  }

  if (command == "HELP") {
    Serial.println(F("OK COMMANDS PING STATUS HOME MOVE DOWN MOVE UP HELP"));
    return;
  }

  Serial.print(F("ERROR UNKNOWN_COMMAND "));
  Serial.println(command);
}

void setup() {
  pinMode(COMMAND_MARK_PIN, OUTPUT);
  digitalWrite(COMMAND_MARK_PIN, LOW);

  Serial.begin(SERIAL_BAUD);
  delay(50);

  pedalServo.attach(PEDAL_SERVO_PIN);
  homeServo();

  Serial.println(F("READY PEDAL_SERVO_TEST"));
  Serial.println(F("Use the Python reaction-time script to run 10 down/up trials."));
  Serial.print(F("INFO up_angle="));
  Serial.print(PEDAL_UP_ANGLE_DEG);
  Serial.print(F(" down_angle="));
  Serial.println(PEDAL_DOWN_ANGLE_DEG);
}

void loop() {
  if (Serial.available() <= 0) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();
  if (command.length() == 0) {
    return;
  }

  handleCommand(command);
}
