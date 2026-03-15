#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: Hot Cross Buns.mid
// Base tempo: 110.00 BPM
// Tempo override: original timing
// Effective output tempo: 110.00 BPM
// Mapping mode: collapse_all_notes_to_single_channel
// Forced retriggers: 4
// Delayed notes: 7
// Unmapped notes skipped: 0
// Unmatched note_off events ignored: 0
// Dangling note_on events auto-closed: 0

// Piano actuator mapping used for this file:
//   Single-solenoid test mode
//   All MIDI notes collapse to PCA9685 channel 0 (5N test solenoid)
//   This is useful for force and timing tuning with one physical solenoid.

// Active hardware channels in this export:
//   PCA9685 channel 0: 5N test solenoid

// Actuation profile:
//   Strike PWM range: 2500 - 4095
//   Strike duration: 35 ms
//   Hold PWM range: 1450 - 2800
//   Hold ratio: 0.58
//   Release delay: 6 ms
//   Minimum rearm gap: 25 ms
//   Retrigger gap: 16 ms

const uint8_t SONG_PCA9685_I2C_ADDRESS = 0x40;
const uint16_t SONG_PCA9685_PWM_FREQUENCY_HZ = 250u;
const uint8_t SONG_CHANNEL_COUNT = 1u;
const uint8_t SONG_CHANNELS[] = {
  0u,
};

typedef struct {
  uint32_t dt_ms;   // delay BEFORE this event
  uint8_t  channel; // PCA9685 channel
  uint16_t pwm;     // 0-4095 duty cycle
} SolenoidEvent;

const SolenoidEvent SONG[] PROGMEM = {
  { 0u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 516u, 0u, 0u },
  { 25u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 485u, 0u, 0u },
  { 16u, 0u, 3120u },
  { 7u, 0u, 0u },
  { 16u, 0u, 3753u },
  { 35u, 0u, 2177u },
  { 516u, 0u, 0u },
  { 494u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 516u, 0u, 0u },
  { 25u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 485u, 0u, 0u },
  { 16u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 516u, 0u, 0u },
  { 517u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 107u, 0u, 0u },
  { 130u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 107u, 0u, 0u },
  { 130u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 107u, 0u, 0u },
  { 130u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 107u, 0u, 0u },
  { 130u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 107u, 0u, 0u },
  { 130u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 107u, 0u, 0u },
  { 130u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 107u, 0u, 0u },
  { 130u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 107u, 0u, 0u },
  { 130u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 516u, 0u, 0u },
  { 25u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 485u, 0u, 0u },
  { 16u, 0u, 3120u },
  { 35u, 0u, 1810u },
  { 516u, 0u, 0u },
};

const uint32_t SONG_EVENT_COUNT = sizeof(SONG) / sizeof(SONG[0]);
