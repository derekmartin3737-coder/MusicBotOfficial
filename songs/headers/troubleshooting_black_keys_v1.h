#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: troubleshooting_black_keys.mid
// Base tempo: 60.00 BPM
// Tempo override: original timing
// Effective output tempo: 60.00 BPM
// Detected MIDI note range: C#3 to A#3
// Active playable layout: 16 mapped notes from C3 to F4 (non-contiguous)
// Fit mode: Black troubleshooting pattern
// Recognizability estimate: diagnostic sequence
// Strict coverage: 16 of 16 note events playable (100.0%)
// Octave transpose coverage: 16 of 16 note events playable (100.0%)
// Octave transpose remap summary: not applicable for troubleshooting sequence
// Mapping mode: explicit_note_map
// Forced retriggers: 0
// Delayed notes: 0
// Unmapped notes skipped: 0
// Unmatched note_off events ignored: 0
// Dangling note_on events auto-closed: 0
// Percussion note events ignored: 0

// Piano actuator mapping used for this file:
//   Explicit note-to-channel mode
//   MIDI note 48 (C3) -> global channel 3 (PCA9685 0x40 channel 3) (D#3 key solenoid)
//   MIDI note 49 (C#3) -> global channel 7 (PCA9685 0x40 channel 7) (G3 key solenoid)
//   MIDI note 50 (D3) -> global channel 2 (PCA9685 0x40 channel 2) (D3 key solenoid)
//   MIDI note 51 (D#3) -> global channel 6 (PCA9685 0x40 channel 6) (F#3 key solenoid)
//   MIDI note 52 (E3) -> global channel 1 (PCA9685 0x40 channel 1) (C#3 key solenoid)
//   MIDI note 53 (F3) -> global channel 0 (PCA9685 0x40 channel 0) (C3 key solenoid)
//   MIDI note 54 (F#3) -> global channel 5 (PCA9685 0x40 channel 5) (F3 key solenoid)
//   MIDI note 55 (G3) -> global channel 11 (PCA9685 0x40 channel 11) (B3 key solenoid)
//   MIDI note 56 (G#3) -> global channel 4 (PCA9685 0x40 channel 4) (E3 key solenoid)
//   MIDI note 57 (A3) -> global channel 10 (PCA9685 0x40 channel 10) (A#3 key solenoid)
//   MIDI note 58 (A#3) -> global channel 9 (PCA9685 0x40 channel 9) (A3 key solenoid)
//   MIDI note 59 (B3) -> global channel 8 (PCA9685 0x40 channel 8) (G#3 key solenoid)
//   MIDI note 60 (C4) -> global channel 15 (PCA9685 0x40 channel 15) (Channel 15)
//   MIDI note 62 (D4) -> global channel 14 (PCA9685 0x40 channel 14) (Channel 14)
//   MIDI note 64 (E4) -> global channel 13 (PCA9685 0x40 channel 13) (Channel 13)
//   MIDI note 65 (F4) -> global channel 12 (PCA9685 0x40 channel 12) (Channel 12)

// Active hardware channels in this export:
//   global channel 4 (PCA9685 0x40 channel 4): E3 key solenoid
//   global channel 5 (PCA9685 0x40 channel 5): F3 key solenoid
//   global channel 6 (PCA9685 0x40 channel 6): F#3 key solenoid
//   global channel 7 (PCA9685 0x40 channel 7): G3 key solenoid
//   global channel 9 (PCA9685 0x40 channel 9): A3 key solenoid

// Actuation profile:
//   Channel 4: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 5: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 6: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 7: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 9: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms

const uint8_t SONG_PCA9685_BOARD_COUNT = 4u;
const uint8_t SONG_PCA9685_MAX_BOARD_COUNT = 4u;
const uint8_t SONG_PCA9685_BOARD_ADDRESSES[SONG_PCA9685_MAX_BOARD_COUNT] = {
  0x40,
  0x41,
  0x42,
  0x43,
};
const uint8_t SONG_PCA9685_I2C_ADDRESS = 0x40;
const uint16_t SONG_PCA9685_PWM_FREQUENCY_HZ = 250u;
const uint8_t SONG_CHANNEL_COUNT = 5u;
const uint8_t SONG_CHANNELS[] = {
  4u,
  5u,
  6u,
  7u,
  9u,
};

typedef struct {
  uint32_t dt_ms;   // delay BEFORE this event
  uint8_t  channel; // global channel across every PCA9685 board
  uint16_t pwm;     // 0-4095 duty cycle
} SolenoidEvent;

const SolenoidEvent SONG[] PROGMEM = {
  { 0u, 7u, 3321u },
  { 35u, 7u, 1162u },
  { 635u, 7u, 0u },
  { 330u, 6u, 3321u },
  { 35u, 6u, 1162u },
  { 635u, 6u, 0u },
  { 330u, 5u, 3321u },
  { 35u, 5u, 1162u },
  { 635u, 5u, 0u },
  { 330u, 4u, 3321u },
  { 35u, 4u, 1162u },
  { 635u, 4u, 0u },
  { 330u, 9u, 3321u },
  { 35u, 9u, 1162u },
  { 635u, 9u, 0u },
  { 1730u, 5u, 3321u },
  { 0u, 7u, 3321u },
  { 35u, 5u, 1162u },
  { 0u, 7u, 1162u },
  { 635u, 5u, 0u },
  { 0u, 7u, 0u },
  { 330u, 4u, 3321u },
  { 0u, 6u, 3321u },
  { 35u, 4u, 1162u },
  { 0u, 6u, 1162u },
  { 635u, 4u, 0u },
  { 0u, 6u, 0u },
  { 330u, 5u, 3321u },
  { 0u, 9u, 3321u },
  { 35u, 5u, 1162u },
  { 0u, 9u, 1162u },
  { 635u, 5u, 0u },
  { 0u, 9u, 0u },
  { 1730u, 7u, 3321u },
  { 0u, 9u, 3321u },
  { 35u, 7u, 1162u },
  { 0u, 9u, 1162u },
  { 635u, 7u, 0u },
  { 0u, 9u, 0u },
  { 330u, 4u, 3321u },
  { 0u, 6u, 3321u },
  { 35u, 4u, 1162u },
  { 0u, 6u, 1162u },
  { 635u, 4u, 0u },
  { 0u, 6u, 0u },
  { 330u, 5u, 3321u },
  { 35u, 5u, 1162u },
  { 635u, 5u, 0u },
};

const uint32_t SONG_EVENT_COUNT = sizeof(SONG) / sizeof(SONG[0]);
