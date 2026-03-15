#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: CDE_Sync_Showcase.mid
// Base tempo: 112.00 BPM
// Tempo override: original timing
// Effective output tempo: 112.00 BPM
// Mapping mode: explicit_note_map
// Forced retriggers: 0
// Delayed notes: 2
// Unmapped notes skipped: 0
// Unmatched note_off events ignored: 0
// Dangling note_on events auto-closed: 0

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
  { 0u, 2u, 3156u },
  { 35u, 2u, 1830u },
  { 233u, 1u, 3033u },
  { 6u, 2u, 0u },
  { 29u, 1u, 1759u },
  { 233u, 0u, 3582u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2221u },
  { 233u, 2u, 3280u },
  { 6u, 0u, 0u },
  { 29u, 2u, 1902u },
  { 233u, 1u, 3094u },
  { 6u, 2u, 0u },
  { 29u, 1u, 1795u },
  { 233u, 0u, 3617u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2243u },
  { 233u, 2u, 3198u },
  { 6u, 0u, 0u },
  { 25u, 0u, 3756u },
  { 4u, 2u, 1855u },
  { 31u, 0u, 2329u },
  { 342u, 2u, 0u },
  { 31u, 0u, 0u },
  { 97u, 1u, 2950u },
  { 35u, 1u, 1711u },
  { 233u, 0u, 3791u },
  { 0u, 2u, 3363u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2350u },
  { 0u, 2u, 1951u },
  { 507u, 0u, 0u },
  { 0u, 2u, 0u },
  { 128u, 2u, 3012u },
  { 35u, 2u, 1747u },
  { 99u, 1u, 3136u },
  { 6u, 2u, 0u },
  { 29u, 1u, 1819u },
  { 99u, 0u, 3826u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2372u },
  { 99u, 2u, 3425u },
  { 6u, 0u, 0u },
  { 25u, 0u, 3843u },
  { 4u, 2u, 1986u },
  { 31u, 0u, 2383u },
  { 476u, 2u, 0u },
  { 31u, 0u, 0u },
};

const uint32_t SONG_EVENT_COUNT = sizeof(SONG) / sizeof(SONG[0]);
