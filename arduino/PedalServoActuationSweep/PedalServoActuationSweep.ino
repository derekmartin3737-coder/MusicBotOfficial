#include <Arduino.h>
#include <Servo.h>

/*
  PedalServoActuationSweep

  Quick bench sketch for watching the sustain-pedal servo press under a few
  different motion profiles. This uses the measured 0.5 inch horn geometry and
  the 2026-04-15 reaction-time characterization as the default "calibrated"
  profile.

  Important limitation:
  - A hobby servo ultimately chooses its own physical speed under load.
  - This sketch can slow the motion down by issuing intermediate angles, but it
    cannot force the servo to move faster than its real mechanical limit.
*/

static const uint8_t PEDAL_SERVO_PIN = 2;
static const uint8_t COMMAND_MARK_PIN = LED_BUILTIN;
static const uint32_t SERIAL_BAUD = 115200;

static const uint8_t PEDAL_UP_ANGLE_DEG = 0;
static const uint8_t PEDAL_DOWN_ANGLE_DEG = 180;

static const float SERVO_HORN_LENGTH_IN = 0.5f;
static const uint16_t MEASURED_DOWN_PROFILE_MS = 426;
static const uint16_t MEASURED_UP_PROFILE_MS = 442;

static const uint16_t PROFILE_HOLD_MS = 900;
static const uint16_t PROFILE_REST_MS = 1400;
static const uint16_t STARTUP_SETTLE_MS = 1500;
static const uint16_t STEP_INTERVAL_MS = 15;
static const uint16_t COMMAND_MARK_MS = 60;

struct SweepProfile {
  const char *name;
  uint16_t downTravelMs;
  uint16_t holdMs;
  uint16_t upTravelMs;
  uint16_t restMs;
  bool directMove;
};

static const SweepProfile PROFILES[] = {
  {"DIRECT_FULL_SPEED", 0, PROFILE_HOLD_MS, 0, PROFILE_REST_MS, true},
  {"CALIBRATED_MEDIAN", MEASURED_DOWN_PROFILE_MS, PROFILE_HOLD_MS, MEASURED_UP_PROFILE_MS, PROFILE_REST_MS, false},
  {"FIRM_PRESS", 325, PROFILE_HOLD_MS, 350, PROFILE_REST_MS, false},
  {"SOFT_PRESS", 575, PROFILE_HOLD_MS, 625, PROFILE_REST_MS, false},
};

static const size_t PROFILE_COUNT = sizeof(PROFILES) / sizeof(PROFILES[0]);

Servo pedalServo;
uint8_t currentAngleDeg = PEDAL_UP_ANGLE_DEG;
size_t currentProfileIndex = 0;
bool autoCycleEnabled = true;
unsigned long nextProfileAtMs = 0;

float computeArcLengthInches() {
  const float sweepRadians = radians(abs((int)PEDAL_DOWN_ANGLE_DEG - (int)PEDAL_UP_ANGLE_DEG));
  return SERVO_HORN_LENGTH_IN * sweepRadians;
}

float estimateTipSpeedInPerSecond(uint16_t durationMs) {
  if (durationMs == 0) {
    return 0.0f;
  }
  return computeArcLengthInches() / (durationMs / 1000.0f);
}

int interpolateAngle(int startAngleDeg, int deltaAngleDeg, uint16_t elapsedMs, uint16_t durationMs) {
  if (durationMs == 0) {
    return startAngleDeg + deltaAngleDeg;
  }

  // Keep this math simple so the sketch compiles cleanly across older Arduino
  // toolchains without depending on extra floating-point helpers.
  const long scaledDelta = ((long)deltaAngleDeg * (long)elapsedMs + (durationMs / 2)) / durationMs;
  return startAngleDeg + (int)scaledDelta;
}

void flashCommandMark() {
  digitalWrite(COMMAND_MARK_PIN, HIGH);
  delay(COMMAND_MARK_MS);
  digitalWrite(COMMAND_MARK_PIN, LOW);
}

void writeServoAngle(uint8_t angleDeg) {
  pedalServo.write(angleDeg);
  currentAngleDeg = angleDeg;
}

void moveDirect(uint8_t targetAngleDeg) {
  const char *direction = (targetAngleDeg == PEDAL_DOWN_ANGLE_DEG) ? "DOWN" : "UP";
  Serial.print(F("  >> COMMAND SENT: "));
  Serial.print(direction);
  Serial.print(F(" to "));
  Serial.print(targetAngleDeg);
  Serial.print(F(" deg @ t="));
  Serial.print(millis());
  Serial.println(F(" ms  (direct, full speed)"));

  flashCommandMark();
  writeServoAngle(targetAngleDeg);

  Serial.print(F("  << COMMAND DONE: "));
  Serial.print(direction);
  Serial.print(F(" @ t="));
  Serial.print(millis());
  Serial.println(F(" ms  (servo is now moving on its own)"));
}

void moveSmooth(uint8_t targetAngleDeg, uint16_t durationMs) {
  if (durationMs == 0 || currentAngleDeg == targetAngleDeg) {
    moveDirect(targetAngleDeg);
    return;
  }

  const char *direction = (targetAngleDeg == PEDAL_DOWN_ANGLE_DEG) ? "DOWN" : "UP";
  Serial.print(F("  >> COMMAND SENT: "));
  Serial.print(direction);
  Serial.print(F(" to "));
  Serial.print(targetAngleDeg);
  Serial.print(F(" deg @ t="));
  Serial.print(millis());
  Serial.print(F(" ms  (ramped, target travel "));
  Serial.print(durationMs);
  Serial.println(F(" ms)"));

  flashCommandMark();

  const int startAngleDeg = (int)currentAngleDeg;
  const int deltaAngleDeg = (int)targetAngleDeg - startAngleDeg;
  const unsigned long startMs = millis();

  while (true) {
    const unsigned long elapsedMs = millis() - startMs;
    if (elapsedMs >= durationMs) {
      break;
    }

    const int nextAngleDeg = constrain(
      interpolateAngle(startAngleDeg, deltaAngleDeg, (uint16_t)elapsedMs, durationMs),
      0,
      180
    );
    if (nextAngleDeg != currentAngleDeg) {
      writeServoAngle((uint8_t)nextAngleDeg);
    }
    delay(STEP_INTERVAL_MS);
  }

  writeServoAngle(targetAngleDeg);

  Serial.print(F("  << COMMAND DONE: "));
  Serial.print(direction);
  Serial.print(F(" @ t="));
  Serial.print(millis());
  Serial.print(F(" ms  (ramp elapsed "));
  Serial.print(millis() - startMs);
  Serial.println(F(" ms)"));
}

void printProfileSummary(size_t index) {
  const SweepProfile &profile = PROFILES[index];

  Serial.print(F("PROFILE "));
  Serial.print(index);
  Serial.print(F(": "));
  Serial.println(profile.name);

  if (profile.directMove) {
    Serial.println(F("  Uses one immediate angle command in each direction."));
    return;
  }

  Serial.print(F("  Down travel: "));
  Serial.print(profile.downTravelMs);
  Serial.print(F(" ms, est. tip speed "));
  Serial.print(estimateTipSpeedInPerSecond(profile.downTravelMs), 3);
  Serial.println(F(" in/s"));

  Serial.print(F("  Up travel: "));
  Serial.print(profile.upTravelMs);
  Serial.print(F(" ms, est. tip speed "));
  Serial.print(estimateTipSpeedInPerSecond(profile.upTravelMs), 3);
  Serial.println(F(" in/s"));
}

void printHelp() {
  Serial.println(F("READY PEDAL_SERVO_ACTUATION_SWEEP"));
  Serial.println(F("Auto-cycle is enabled at startup."));
  Serial.println(F("Commands:"));
  Serial.println(F("  n = run next profile now"));
  Serial.println(F("  r = repeat current profile"));
  Serial.println(F("  p = pause or resume auto-cycle"));
  Serial.println(F("  h = move the servo to pedal-up"));
  Serial.println(F("  ? = print this help"));
  Serial.println(F("Built-in profiles:"));
  for (size_t index = 0; index < PROFILE_COUNT; ++index) {
    printProfileSummary(index);
  }
}

void runProfile(size_t index) {
  const SweepProfile &profile = PROFILES[index];

  Serial.println();
  Serial.print(F("Running "));
  Serial.print(profile.name);
  Serial.print(F(" (profile "));
  Serial.print(index);
  Serial.println(F(")"));

  printProfileSummary(index);

  if (profile.directMove) {
    moveDirect(PEDAL_DOWN_ANGLE_DEG);
  } else {
    moveSmooth(PEDAL_DOWN_ANGLE_DEG, profile.downTravelMs);
  }

  delay(profile.holdMs);

  if (profile.directMove) {
    moveDirect(PEDAL_UP_ANGLE_DEG);
  } else {
    moveSmooth(PEDAL_UP_ANGLE_DEG, profile.upTravelMs);
  }

  delay(profile.restMs);
}

void handleSerialCommand(char command) {
  if (command == 'n' || command == 'N') {
    runProfile(currentProfileIndex);
    currentProfileIndex = (currentProfileIndex + 1) % PROFILE_COUNT;
    nextProfileAtMs = millis() + 300;
    return;
  }

  if (command == 'r' || command == 'R') {
    runProfile(currentProfileIndex);
    nextProfileAtMs = millis() + 300;
    return;
  }

  if (command == 'p' || command == 'P') {
    autoCycleEnabled = !autoCycleEnabled;
    Serial.print(F("Auto-cycle "));
    Serial.println(autoCycleEnabled ? F("enabled") : F("paused"));
    nextProfileAtMs = millis() + 300;
    return;
  }

  if (command == 'h' || command == 'H') {
    Serial.println(F("Moving to pedal-up home angle."));
    moveDirect(PEDAL_UP_ANGLE_DEG);
    nextProfileAtMs = millis() + 300;
    return;
  }

  if (command == '?' ) {
    printHelp();
    nextProfileAtMs = millis() + 300;
    return;
  }
}

void setup() {
  pinMode(COMMAND_MARK_PIN, OUTPUT);
  digitalWrite(COMMAND_MARK_PIN, LOW);

  Serial.begin(SERIAL_BAUD);
  delay(50);

  pedalServo.attach(PEDAL_SERVO_PIN);
  writeServoAngle(PEDAL_UP_ANGLE_DEG);
  delay(STARTUP_SETTLE_MS);

  Serial.print(F("Servo horn length: "));
  Serial.print(SERVO_HORN_LENGTH_IN, 3);
  Serial.println(F(" in"));
  Serial.print(F("180-degree arc length: "));
  Serial.print(computeArcLengthInches(), 4);
  Serial.println(F(" in"));
  printHelp();

  nextProfileAtMs = millis() + 1200;
}

void loop() {
  while (Serial.available() > 0) {
    const char command = (char)Serial.read();
    handleSerialCommand(command);
  }

  if (!autoCycleEnabled) {
    return;
  }

  if (millis() >= nextProfileAtMs) {
    runProfile(currentProfileIndex);
    currentProfileIndex = (currentProfileIndex + 1) % PROFILE_COUNT;
    nextProfileAtMs = millis() + 300;
  }
}
