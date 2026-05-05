#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: Mary Had a Little Lamb.mid
// Base tempo: 55.00 BPM
// Tempo override: original timing
// Effective output tempo: 55.00 BPM
// Detected MIDI note range: C3 to G3
// Active playable layout: 3 mapped notes from C3 to E3 (non-contiguous)
// Fit mode: transpose by octave (best shift was 0 semitones)
// Strict coverage: 23 of 25 note events playable (92.0%)
// Octave transpose coverage: 23 of 25 note events playable (92.0%)
// Mapping mode: explicit_note_map
// Forced retriggers: 3
// Delayed notes: 7
// Unmapped notes skipped: 2
// Unmatched note_off events ignored: 0
// Dangling note_on events auto-closed: 0
// Percussion note events ignored: 0

// Piano actuator mapping used for this file:
//   Explicit note-to-channel mode
//   MIDI note 48 (C3) -> PCA9685 channel 0 (C3 key solenoid (25N))
//   MIDI note 50 (D3) -> PCA9685 channel 1 (D3 key solenoid (5N))
//   MIDI note 52 (E3) -> PCA9685 channel 2 (E3 key solenoid (5N))

// Active hardware channels in this export:
//   PCA9685 channel 0: C3 key solenoid (25N)
//   PCA9685 channel 1: D3 key solenoid (5N)
//   PCA9685 channel 2: E3 key solenoid (5N)

// Actuation profile:
//   Channel 0: strike 3000-4095, hold 1800-2800, hold ratio 0.62, strike 35 ms, release delay 6 ms, rearm 25 ms, retrigger 16 ms
//   Channel 1: strike 2300-3600, hold 1300-2200, hold ratio 0.58, strike 35 ms, release delay 6 ms, rearm 25 ms, retrigger 16 ms
//   Channel 2: strike 2300-3600, hold 1300-2200, hold ratio 0.58, strike 35 ms, release delay 6 ms, rearm 25 ms, retrigger 16 ms

const uint8_t SONG_PCA9685_I2C_ADDRESS = 0x40;
const uint16_t SONG_PCA9685_PWM_FREQUENCY_HZ = 250u;
const uint8_t SONG_CHANNEL_COUNT = 3u;
const uint8_t SONG_CHANNELS[] = {
  0u,
  1u,
  2u,
};

typedef struct {
  uint32_t dt_ms;   // delay BEFORE this event
  uint8_t  channel; // PCA9685 channel
  uint16_t pwm;     // 0-4095 duty cycle
} SolenoidEvent;

const SolenoidEvent SONG[] PROGMEM = {
  { 0u, 2u, 2806u },
  { 35u, 2u, 1627u },
  { 238u, 1u, 2806u },
  { 6u, 2u, 0u },
  { 29u, 1u, 1627u },
  { 238u, 0u, 3426u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2124u },
  { 238u, 1u, 2806u },
  { 6u, 0u, 0u },
  { 29u, 1u, 1627u },
  { 238u, 2u, 2806u },
  { 6u, 1u, 0u },
  { 29u, 2u, 1627u },
  { 244u, 2u, 0u },
  { 25u, 2u, 2806u },
  { 35u, 2u, 1627u },
  { 213u, 2u, 0u },
  { 16u, 2u, 2806u },
  { 35u, 2u, 1627u },
  { 244u, 2u, 0u },
  { 245u, 1u, 2806u },
  { 35u, 1u, 1627u },
  { 244u, 1u, 0u },
  { 25u, 1u, 2806u },
  { 35u, 1u, 1627u },
  { 213u, 1u, 0u },
  { 16u, 1u, 2806u },
  { 35u, 1u, 1627u },
  { 244u, 1u, 0u },
  { 245u, 2u, 2806u },
  { 35u, 2u, 1627u },
  { 244u, 2u, 0u },
  { 813u, 2u, 2806u },
  { 35u, 2u, 1627u },
  { 238u, 1u, 2806u },
  { 6u, 2u, 0u },
  { 29u, 1u, 1627u },
  { 238u, 0u, 3426u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2124u },
  { 238u, 1u, 2806u },
  { 6u, 0u, 0u },
  { 29u, 1u, 1627u },
  { 238u, 2u, 2806u },
  { 6u, 1u, 0u },
  { 29u, 2u, 1627u },
  { 244u, 2u, 0u },
  { 25u, 2u, 2806u },
  { 35u, 2u, 1627u },
  { 213u, 2u, 0u },
  { 16u, 2u, 2806u },
  { 35u, 2u, 1627u },
  { 244u, 2u, 0u },
  { 245u, 1u, 2806u },
  { 35u, 1u, 1627u },
  { 244u, 1u, 0u },
  { 25u, 1u, 2806u },
  { 35u, 1u, 1627u },
  { 207u, 2u, 2806u },
  { 35u, 2u, 1627u },
  { 2u, 1u, 0u },
  { 236u, 1u, 2806u },
  { 6u, 2u, 0u },
  { 29u, 1u, 1627u },
  { 238u, 0u, 3426u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2124u },
  { 244u, 0u, 0u },
};

const uint32_t SONG_EVENT_COUNT = sizeof(SONG) / sizeof(SONG[0]);
