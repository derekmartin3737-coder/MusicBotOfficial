#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: hes_a_pirate_isolated_melody.mid
// Base tempo: 200.00 BPM
// Tempo override: 0.50 BPM
// Effective output tempo: 0.50 BPM
// Mapping mode: explicit_note_map
// Forced retriggers: 0
// Delayed notes: 0
// Unmapped notes skipped: 273
// Unmatched note_off events ignored: 0
// Dangling note_on events auto-closed: 0

// Piano actuator mapping used for this file:
//   Explicit note-to-channel mode
//   MIDI note 48 (C3) -> PCA9685 channel 0 (C3 key solenoid (25N))
//   MIDI note 50 (D3) -> PCA9685 channel 1 (D3 key solenoid (5N))
//   MIDI note 52 (E3) -> PCA9685 channel 2 (E3 key solenoid (5N))

// Active hardware channels in this export:

// Actuation profile:

const uint8_t SONG_PCA9685_I2C_ADDRESS = 0x40;
const uint16_t SONG_PCA9685_PWM_FREQUENCY_HZ = 250u;
const uint8_t SONG_CHANNEL_COUNT = 0u;
const uint8_t SONG_CHANNELS[] = {
};

typedef struct {
  uint32_t dt_ms;   // delay BEFORE this event
  uint8_t  channel; // PCA9685 channel
  uint16_t pwm;     // 0-4095 duty cycle
} SolenoidEvent;

const SolenoidEvent SONG[] PROGMEM = {
};

const uint32_t SONG_EVENT_COUNT = sizeof(SONG) / sizeof(SONG[0]);
