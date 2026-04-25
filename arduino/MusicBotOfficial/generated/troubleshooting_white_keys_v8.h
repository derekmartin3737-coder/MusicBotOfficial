#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: troubleshooting_white_keys.mid
// Base tempo: 60.00 BPM
// Tempo override: original timing
// Effective output tempo: 60.00 BPM
// Detected MIDI note range: C1 to C6
// Active playable layout: 57 mapped notes from C1 to C6 (non-contiguous)
// Fit mode: White troubleshooting pattern
// Recognizability estimate: diagnostic sequence
// Strict coverage: 132 of 132 note events playable (100.0%)
// Octave transpose coverage: 132 of 132 note events playable (100.0%)
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
//   MIDI note 24 (C1) -> global channel 1 (PCA9685 0x60 channel 1) (PCA9685 0x60 channel 1)
//   MIDI note 25 (C#1) -> global channel 3 (PCA9685 0x60 channel 3) (PCA9685 0x60 channel 3)
//   MIDI note 26 (D1) -> global channel 0 (PCA9685 0x60 channel 0) (PCA9685 0x60 channel 0)
//   MIDI note 28 (E1) -> global channel 11 (PCA9685 0x60 channel 11) (PCA9685 0x60 channel 11)
//   MIDI note 29 (F1) -> global channel 10 (PCA9685 0x60 channel 10) (PCA9685 0x60 channel 10)
//   MIDI note 31 (G1) -> global channel 9 (PCA9685 0x60 channel 9) (PCA9685 0x60 channel 9)
//   MIDI note 32 (G#1) -> global channel 6 (PCA9685 0x60 channel 6) (PCA9685 0x60 channel 6)
//   MIDI note 34 (A#1) -> global channel 5 (PCA9685 0x60 channel 5) (PCA9685 0x60 channel 5)
//   MIDI note 35 (B1) -> global channel 4 (PCA9685 0x60 channel 4) (PCA9685 0x60 channel 4)
//   MIDI note 36 (C2) -> global channel 13 (PCA9685 0x60 channel 13) (PCA9685 0x60 channel 13)
//   MIDI note 37 (C#2) -> global channel 15 (PCA9685 0x60 channel 15) (PCA9685 0x60 channel 15)
//   MIDI note 38 (D2) -> global channel 12 (PCA9685 0x60 channel 12) (PCA9685 0x60 channel 12)
//   MIDI note 39 (D#2) -> global channel 14 (PCA9685 0x60 channel 14) (PCA9685 0x60 channel 14)
//   MIDI note 40 (E2) -> global channel 23 (PCA9685 0x50 channel 7) (PCA9685 0x50 channel 7)
//   MIDI note 41 (F2) -> global channel 22 (PCA9685 0x50 channel 6) (PCA9685 0x50 channel 6)
//   MIDI note 42 (F#2) -> global channel 19 (PCA9685 0x50 channel 3) (PCA9685 0x50 channel 3)
//   MIDI note 43 (G2) -> global channel 21 (PCA9685 0x50 channel 5) (PCA9685 0x50 channel 5)
//   MIDI note 44 (G#2) -> global channel 18 (PCA9685 0x50 channel 2) (PCA9685 0x50 channel 2)
//   MIDI note 45 (A2) -> global channel 20 (PCA9685 0x50 channel 4) (PCA9685 0x50 channel 4)
//   MIDI note 46 (A#2) -> global channel 17 (PCA9685 0x50 channel 1) (PCA9685 0x50 channel 1)
//   MIDI note 47 (B2) -> global channel 16 (PCA9685 0x50 channel 0) (PCA9685 0x50 channel 0)
//   MIDI note 48 (C3) -> global channel 25 (PCA9685 0x50 channel 9) (PCA9685 0x50 channel 9)
//   MIDI note 49 (C#3) -> global channel 27 (PCA9685 0x50 channel 11) (PCA9685 0x50 channel 11)
//   MIDI note 50 (D3) -> global channel 24 (PCA9685 0x50 channel 8) (PCA9685 0x50 channel 8)
//   MIDI note 51 (D#3) -> global channel 26 (PCA9685 0x50 channel 10) (PCA9685 0x50 channel 10)
//   MIDI note 52 (E3) -> global channel 35 (PCA9685 0x48 channel 3) (PCA9685 0x48 channel 3)
//   MIDI note 53 (F3) -> global channel 34 (PCA9685 0x48 channel 2) (PCA9685 0x48 channel 2)
//   MIDI note 54 (F#3) -> global channel 31 (PCA9685 0x50 channel 15) (PCA9685 0x50 channel 15)
//   MIDI note 55 (G3) -> global channel 33 (PCA9685 0x48 channel 1) (PCA9685 0x48 channel 1)
//   MIDI note 56 (G#3) -> global channel 30 (PCA9685 0x50 channel 14) (PCA9685 0x50 channel 14)
//   MIDI note 57 (A3) -> global channel 32 (PCA9685 0x48 channel 0) (PCA9685 0x48 channel 0)
//   MIDI note 58 (A#3) -> global channel 29 (PCA9685 0x50 channel 13) (PCA9685 0x50 channel 13)
//   MIDI note 59 (B3) -> global channel 28 (PCA9685 0x50 channel 12) (PCA9685 0x50 channel 12)
//   MIDI note 61 (C#4) -> global channel 39 (PCA9685 0x48 channel 7) (PCA9685 0x48 channel 7)
//   MIDI note 62 (D4) -> global channel 36 (PCA9685 0x48 channel 4) (PCA9685 0x48 channel 4)
//   MIDI note 63 (D#4) -> global channel 38 (PCA9685 0x48 channel 6) (PCA9685 0x48 channel 6)
//   MIDI note 64 (E4) -> global channel 43 (PCA9685 0x48 channel 11) (PCA9685 0x48 channel 11)
//   MIDI note 65 (F4) -> global channel 42 (PCA9685 0x48 channel 10) (PCA9685 0x48 channel 10)
//   MIDI note 66 (F#4) -> global channel 47 (PCA9685 0x48 channel 15) (PCA9685 0x48 channel 15)
//   MIDI note 67 (G4) -> global channel 41 (PCA9685 0x48 channel 9) (PCA9685 0x48 channel 9)
//   MIDI note 68 (G#4) -> global channel 46 (PCA9685 0x48 channel 14) (PCA9685 0x48 channel 14)
//   MIDI note 69 (A4) -> global channel 40 (PCA9685 0x48 channel 8) (PCA9685 0x48 channel 8)
//   MIDI note 70 (A#4) -> global channel 45 (PCA9685 0x48 channel 13) (PCA9685 0x48 channel 13)
//   MIDI note 71 (B4) -> global channel 44 (PCA9685 0x48 channel 12) (PCA9685 0x48 channel 12)
//   MIDI note 72 (C5) -> global channel 50 (PCA9685 0x40 channel 2) (PCA9685 0x40 channel 2)
//   MIDI note 73 (C#5) -> global channel 48 (PCA9685 0x40 channel 0) (PCA9685 0x40 channel 0)
//   MIDI note 74 (D5) -> global channel 51 (PCA9685 0x40 channel 3) (PCA9685 0x40 channel 3)
//   MIDI note 75 (D#5) -> global channel 49 (PCA9685 0x40 channel 1) (PCA9685 0x40 channel 1)
//   MIDI note 76 (E5) -> global channel 52 (PCA9685 0x40 channel 4) (PCA9685 0x40 channel 4)
//   MIDI note 77 (F5) -> global channel 53 (PCA9685 0x40 channel 5) (PCA9685 0x40 channel 5)
//   MIDI note 78 (F#5) -> global channel 59 (PCA9685 0x40 channel 11) (PCA9685 0x40 channel 11)
//   MIDI note 79 (G5) -> global channel 54 (PCA9685 0x40 channel 6) (PCA9685 0x40 channel 6)
//   MIDI note 80 (G#5) -> global channel 58 (PCA9685 0x40 channel 10) (PCA9685 0x40 channel 10)
//   MIDI note 81 (A5) -> global channel 55 (PCA9685 0x40 channel 7) (PCA9685 0x40 channel 7)
//   MIDI note 82 (A#5) -> global channel 57 (PCA9685 0x40 channel 9) (PCA9685 0x40 channel 9)
//   MIDI note 83 (B5) -> global channel 56 (PCA9685 0x40 channel 8) (PCA9685 0x40 channel 8)
//   MIDI note 84 (C6) -> global channel 60 (PCA9685 0x40 channel 12) (PCA9685 0x40 channel 12)

// Active hardware channels in this export:
//   global channel 0 (PCA9685 0x60 channel 0): PCA9685 0x60 channel 0
//   global channel 1 (PCA9685 0x60 channel 1): PCA9685 0x60 channel 1
//   global channel 4 (PCA9685 0x60 channel 4): PCA9685 0x60 channel 4
//   global channel 9 (PCA9685 0x60 channel 9): PCA9685 0x60 channel 9
//   global channel 10 (PCA9685 0x60 channel 10): PCA9685 0x60 channel 10
//   global channel 11 (PCA9685 0x60 channel 11): PCA9685 0x60 channel 11
//   global channel 12 (PCA9685 0x60 channel 12): PCA9685 0x60 channel 12
//   global channel 13 (PCA9685 0x60 channel 13): PCA9685 0x60 channel 13
//   global channel 16 (PCA9685 0x50 channel 0): PCA9685 0x50 channel 0
//   global channel 20 (PCA9685 0x50 channel 4): PCA9685 0x50 channel 4
//   global channel 21 (PCA9685 0x50 channel 5): PCA9685 0x50 channel 5
//   global channel 22 (PCA9685 0x50 channel 6): PCA9685 0x50 channel 6
//   global channel 23 (PCA9685 0x50 channel 7): PCA9685 0x50 channel 7
//   global channel 24 (PCA9685 0x50 channel 8): PCA9685 0x50 channel 8
//   global channel 25 (PCA9685 0x50 channel 9): PCA9685 0x50 channel 9
//   global channel 28 (PCA9685 0x50 channel 12): PCA9685 0x50 channel 12
//   global channel 32 (PCA9685 0x48 channel 0): PCA9685 0x48 channel 0
//   global channel 33 (PCA9685 0x48 channel 1): PCA9685 0x48 channel 1
//   global channel 34 (PCA9685 0x48 channel 2): PCA9685 0x48 channel 2
//   global channel 35 (PCA9685 0x48 channel 3): PCA9685 0x48 channel 3
//   global channel 36 (PCA9685 0x48 channel 4): PCA9685 0x48 channel 4
//   global channel 40 (PCA9685 0x48 channel 8): PCA9685 0x48 channel 8
//   global channel 41 (PCA9685 0x48 channel 9): PCA9685 0x48 channel 9
//   global channel 42 (PCA9685 0x48 channel 10): PCA9685 0x48 channel 10
//   global channel 43 (PCA9685 0x48 channel 11): PCA9685 0x48 channel 11
//   global channel 44 (PCA9685 0x48 channel 12): PCA9685 0x48 channel 12
//   global channel 50 (PCA9685 0x40 channel 2): PCA9685 0x40 channel 2
//   global channel 51 (PCA9685 0x40 channel 3): PCA9685 0x40 channel 3
//   global channel 52 (PCA9685 0x40 channel 4): PCA9685 0x40 channel 4
//   global channel 53 (PCA9685 0x40 channel 5): PCA9685 0x40 channel 5
//   global channel 54 (PCA9685 0x40 channel 6): PCA9685 0x40 channel 6
//   global channel 55 (PCA9685 0x40 channel 7): PCA9685 0x40 channel 7
//   global channel 56 (PCA9685 0x40 channel 8): PCA9685 0x40 channel 8
//   global channel 60 (PCA9685 0x40 channel 12): PCA9685 0x40 channel 12

// Actuation profile:
//   Channel 0: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 1: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 4: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 9: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 10: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 11: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 12: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 13: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 16: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 20: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 21: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 22: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 23: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 24: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 25: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 28: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 32: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 33: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 34: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 35: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 36: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 40: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 41: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 42: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 43: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 44: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 50: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 51: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 52: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 53: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 54: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 55: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 56: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 60: strike 2300-3600, hold 800-1400, hold ratio 0.35, strike 35 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms

const uint8_t SONG_PCA9685_BOARD_COUNT = 4u;
const uint8_t SONG_PCA9685_MAX_BOARD_COUNT = 4u;
const uint8_t SONG_PCA9685_BOARD_ADDRESSES[SONG_PCA9685_MAX_BOARD_COUNT] = {
  0x60,
  0x50,
  0x48,
  0x40,
};
const uint8_t SONG_PCA9685_I2C_ADDRESS = 0x60;
const uint16_t SONG_PCA9685_PWM_FREQUENCY_HZ = 250u;
const uint8_t SONG_CHANNEL_COUNT = 34u;
const uint8_t SONG_CHANNELS[] = {
  0u,
  1u,
  4u,
  9u,
  10u,
  11u,
  12u,
  13u,
  16u,
  20u,
  21u,
  22u,
  23u,
  24u,
  25u,
  28u,
  32u,
  33u,
  34u,
  35u,
  36u,
  40u,
  41u,
  42u,
  43u,
  44u,
  50u,
  51u,
  52u,
  53u,
  54u,
  55u,
  56u,
  60u,
};

typedef struct {
  uint32_t dt_ms;   // delay BEFORE this event
  uint8_t  channel; // global channel across every PCA9685 board
  uint16_t pwm;     // 0-4095 duty cycle
} SolenoidEvent;

const SolenoidEvent SONG[] PROGMEM = {
  { 0u, 1u, 3321u },
  { 35u, 1u, 1162u },
  { 635u, 1u, 0u },
  { 330u, 0u, 3321u },
  { 35u, 0u, 1162u },
  { 635u, 0u, 0u },
  { 330u, 11u, 3321u },
  { 35u, 11u, 1162u },
  { 635u, 11u, 0u },
  { 330u, 10u, 3321u },
  { 35u, 10u, 1162u },
  { 635u, 10u, 0u },
  { 330u, 9u, 3321u },
  { 35u, 9u, 1162u },
  { 635u, 9u, 0u },
  { 330u, 4u, 3321u },
  { 35u, 4u, 1162u },
  { 635u, 4u, 0u },
  { 330u, 13u, 3321u },
  { 35u, 13u, 1162u },
  { 635u, 13u, 0u },
  { 330u, 12u, 3321u },
  { 35u, 12u, 1162u },
  { 635u, 12u, 0u },
  { 330u, 23u, 3321u },
  { 35u, 23u, 1162u },
  { 635u, 23u, 0u },
  { 330u, 22u, 3321u },
  { 35u, 22u, 1162u },
  { 635u, 22u, 0u },
  { 330u, 21u, 3321u },
  { 35u, 21u, 1162u },
  { 635u, 21u, 0u },
  { 330u, 20u, 3321u },
  { 35u, 20u, 1162u },
  { 635u, 20u, 0u },
  { 330u, 16u, 3321u },
  { 35u, 16u, 1162u },
  { 635u, 16u, 0u },
  { 330u, 25u, 3321u },
  { 35u, 25u, 1162u },
  { 635u, 25u, 0u },
  { 330u, 24u, 3321u },
  { 35u, 24u, 1162u },
  { 635u, 24u, 0u },
  { 330u, 35u, 3321u },
  { 35u, 35u, 1162u },
  { 635u, 35u, 0u },
  { 330u, 34u, 3321u },
  { 35u, 34u, 1162u },
  { 635u, 34u, 0u },
  { 330u, 33u, 3321u },
  { 35u, 33u, 1162u },
  { 635u, 33u, 0u },
  { 330u, 32u, 3321u },
  { 35u, 32u, 1162u },
  { 635u, 32u, 0u },
  { 330u, 28u, 3321u },
  { 35u, 28u, 1162u },
  { 635u, 28u, 0u },
  { 330u, 36u, 3321u },
  { 35u, 36u, 1162u },
  { 635u, 36u, 0u },
  { 330u, 43u, 3321u },
  { 35u, 43u, 1162u },
  { 635u, 43u, 0u },
  { 330u, 42u, 3321u },
  { 35u, 42u, 1162u },
  { 635u, 42u, 0u },
  { 330u, 41u, 3321u },
  { 35u, 41u, 1162u },
  { 635u, 41u, 0u },
  { 330u, 40u, 3321u },
  { 35u, 40u, 1162u },
  { 635u, 40u, 0u },
  { 330u, 44u, 3321u },
  { 35u, 44u, 1162u },
  { 635u, 44u, 0u },
  { 330u, 50u, 3321u },
  { 35u, 50u, 1162u },
  { 635u, 50u, 0u },
  { 330u, 51u, 3321u },
  { 35u, 51u, 1162u },
  { 635u, 51u, 0u },
  { 330u, 52u, 3321u },
  { 35u, 52u, 1162u },
  { 635u, 52u, 0u },
  { 330u, 53u, 3321u },
  { 35u, 53u, 1162u },
  { 635u, 53u, 0u },
  { 330u, 54u, 3321u },
  { 35u, 54u, 1162u },
  { 635u, 54u, 0u },
  { 330u, 55u, 3321u },
  { 35u, 55u, 1162u },
  { 635u, 55u, 0u },
  { 330u, 56u, 3321u },
  { 35u, 56u, 1162u },
  { 635u, 56u, 0u },
  { 330u, 60u, 3321u },
  { 35u, 60u, 1162u },
  { 635u, 60u, 0u },
  { 1730u, 1u, 3321u },
  { 0u, 11u, 3321u },
  { 35u, 1u, 1162u },
  { 0u, 11u, 1162u },
  { 635u, 1u, 0u },
  { 0u, 11u, 0u },
  { 330u, 0u, 3321u },
  { 0u, 10u, 3321u },
  { 35u, 0u, 1162u },
  { 0u, 10u, 1162u },
  { 635u, 0u, 0u },
  { 0u, 10u, 0u },
  { 330u, 9u, 3321u },
  { 0u, 11u, 3321u },
  { 35u, 9u, 1162u },
  { 0u, 11u, 1162u },
  { 635u, 9u, 0u },
  { 0u, 11u, 0u },
  { 330u, 4u, 3321u },
  { 0u, 10u, 3321u },
  { 35u, 4u, 1162u },
  { 0u, 10u, 1162u },
  { 635u, 4u, 0u },
  { 0u, 10u, 0u },
  { 330u, 9u, 3321u },
  { 0u, 13u, 3321u },
  { 35u, 9u, 1162u },
  { 0u, 13u, 1162u },
  { 635u, 9u, 0u },
  { 0u, 13u, 0u },
  { 330u, 4u, 3321u },
  { 0u, 12u, 3321u },
  { 35u, 4u, 1162u },
  { 0u, 12u, 1162u },
  { 635u, 4u, 0u },
  { 0u, 12u, 0u },
  { 330u, 13u, 3321u },
  { 0u, 23u, 3321u },
  { 35u, 13u, 1162u },
  { 0u, 23u, 1162u },
  { 635u, 13u, 0u },
  { 0u, 23u, 0u },
  { 330u, 12u, 3321u },
  { 0u, 22u, 3321u },
  { 35u, 12u, 1162u },
  { 0u, 22u, 1162u },
  { 635u, 12u, 0u },
  { 0u, 22u, 0u },
  { 330u, 21u, 3321u },
  { 0u, 23u, 3321u },
  { 35u, 21u, 1162u },
  { 0u, 23u, 1162u },
  { 635u, 21u, 0u },
  { 0u, 23u, 0u },
  { 330u, 20u, 3321u },
  { 0u, 22u, 3321u },
  { 35u, 20u, 1162u },
  { 0u, 22u, 1162u },
  { 635u, 20u, 0u },
  { 0u, 22u, 0u },
  { 330u, 16u, 3321u },
  { 0u, 21u, 3321u },
  { 35u, 16u, 1162u },
  { 0u, 21u, 1162u },
  { 635u, 16u, 0u },
  { 0u, 21u, 0u },
  { 330u, 20u, 3321u },
  { 0u, 25u, 3321u },
  { 35u, 20u, 1162u },
  { 0u, 25u, 1162u },
  { 635u, 20u, 0u },
  { 0u, 25u, 0u },
  { 330u, 16u, 3321u },
  { 0u, 24u, 3321u },
  { 35u, 16u, 1162u },
  { 0u, 24u, 1162u },
  { 635u, 16u, 0u },
  { 0u, 24u, 0u },
  { 330u, 25u, 3321u },
  { 0u, 35u, 3321u },
  { 35u, 25u, 1162u },
  { 0u, 35u, 1162u },
  { 635u, 25u, 0u },
  { 0u, 35u, 0u },
  { 330u, 24u, 3321u },
  { 0u, 34u, 3321u },
  { 35u, 24u, 1162u },
  { 0u, 34u, 1162u },
  { 635u, 24u, 0u },
  { 0u, 34u, 0u },
  { 330u, 33u, 3321u },
  { 0u, 35u, 3321u },
  { 35u, 33u, 1162u },
  { 0u, 35u, 1162u },
  { 635u, 33u, 0u },
  { 0u, 35u, 0u },
  { 330u, 32u, 3321u },
  { 0u, 34u, 3321u },
  { 35u, 32u, 1162u },
  { 0u, 34u, 1162u },
  { 635u, 32u, 0u },
  { 0u, 34u, 0u },
  { 330u, 28u, 3321u },
  { 0u, 33u, 3321u },
  { 35u, 28u, 1162u },
  { 0u, 33u, 1162u },
  { 635u, 28u, 0u },
  { 0u, 33u, 0u },
  { 330u, 32u, 3321u },
  { 0u, 36u, 3321u },
  { 35u, 32u, 1162u },
  { 0u, 36u, 1162u },
  { 635u, 32u, 0u },
  { 0u, 36u, 0u },
  { 330u, 28u, 3321u },
  { 0u, 43u, 3321u },
  { 35u, 28u, 1162u },
  { 0u, 43u, 1162u },
  { 635u, 28u, 0u },
  { 0u, 43u, 0u },
  { 330u, 36u, 3321u },
  { 0u, 42u, 3321u },
  { 35u, 36u, 1162u },
  { 0u, 42u, 1162u },
  { 635u, 36u, 0u },
  { 0u, 42u, 0u },
  { 330u, 41u, 3321u },
  { 0u, 43u, 3321u },
  { 35u, 41u, 1162u },
  { 0u, 43u, 1162u },
  { 635u, 41u, 0u },
  { 0u, 43u, 0u },
  { 330u, 40u, 3321u },
  { 0u, 42u, 3321u },
  { 35u, 40u, 1162u },
  { 0u, 42u, 1162u },
  { 635u, 40u, 0u },
  { 0u, 42u, 0u },
  { 330u, 41u, 3321u },
  { 0u, 44u, 3321u },
  { 35u, 41u, 1162u },
  { 0u, 44u, 1162u },
  { 635u, 41u, 0u },
  { 0u, 44u, 0u },
  { 330u, 40u, 3321u },
  { 0u, 50u, 3321u },
  { 35u, 40u, 1162u },
  { 0u, 50u, 1162u },
  { 635u, 40u, 0u },
  { 0u, 50u, 0u },
  { 330u, 44u, 3321u },
  { 0u, 51u, 3321u },
  { 35u, 44u, 1162u },
  { 0u, 51u, 1162u },
  { 635u, 44u, 0u },
  { 0u, 51u, 0u },
  { 330u, 50u, 3321u },
  { 0u, 52u, 3321u },
  { 35u, 50u, 1162u },
  { 0u, 52u, 1162u },
  { 635u, 50u, 0u },
  { 0u, 52u, 0u },
  { 330u, 51u, 3321u },
  { 0u, 53u, 3321u },
  { 35u, 51u, 1162u },
  { 0u, 53u, 1162u },
  { 635u, 51u, 0u },
  { 0u, 53u, 0u },
  { 330u, 52u, 3321u },
  { 0u, 54u, 3321u },
  { 35u, 52u, 1162u },
  { 0u, 54u, 1162u },
  { 635u, 52u, 0u },
  { 0u, 54u, 0u },
  { 330u, 53u, 3321u },
  { 0u, 55u, 3321u },
  { 35u, 53u, 1162u },
  { 0u, 55u, 1162u },
  { 635u, 53u, 0u },
  { 0u, 55u, 0u },
  { 330u, 54u, 3321u },
  { 0u, 56u, 3321u },
  { 35u, 54u, 1162u },
  { 0u, 56u, 1162u },
  { 635u, 54u, 0u },
  { 0u, 56u, 0u },
  { 330u, 55u, 3321u },
  { 0u, 60u, 3321u },
  { 35u, 55u, 1162u },
  { 0u, 60u, 1162u },
  { 635u, 55u, 0u },
  { 0u, 60u, 0u },
  { 1730u, 1u, 3321u },
  { 0u, 60u, 3321u },
  { 35u, 1u, 1162u },
  { 0u, 60u, 1162u },
  { 635u, 1u, 0u },
  { 0u, 60u, 0u },
  { 330u, 0u, 3321u },
  { 0u, 56u, 3321u },
  { 35u, 0u, 1162u },
  { 0u, 56u, 1162u },
  { 635u, 0u, 0u },
  { 0u, 56u, 0u },
  { 330u, 11u, 3321u },
  { 0u, 55u, 3321u },
  { 35u, 11u, 1162u },
  { 0u, 55u, 1162u },
  { 635u, 11u, 0u },
  { 0u, 55u, 0u },
  { 330u, 10u, 3321u },
  { 0u, 54u, 3321u },
  { 35u, 10u, 1162u },
  { 0u, 54u, 1162u },
  { 635u, 10u, 0u },
  { 0u, 54u, 0u },
  { 330u, 9u, 3321u },
  { 0u, 53u, 3321u },
  { 35u, 9u, 1162u },
  { 0u, 53u, 1162u },
  { 635u, 9u, 0u },
  { 0u, 53u, 0u },
  { 330u, 4u, 3321u },
  { 0u, 52u, 3321u },
  { 35u, 4u, 1162u },
  { 0u, 52u, 1162u },
  { 635u, 4u, 0u },
  { 0u, 52u, 0u },
  { 330u, 13u, 3321u },
  { 0u, 51u, 3321u },
  { 35u, 13u, 1162u },
  { 0u, 51u, 1162u },
  { 635u, 13u, 0u },
  { 0u, 51u, 0u },
  { 330u, 12u, 3321u },
  { 0u, 50u, 3321u },
  { 35u, 12u, 1162u },
  { 0u, 50u, 1162u },
  { 635u, 12u, 0u },
  { 0u, 50u, 0u },
  { 330u, 23u, 3321u },
  { 0u, 44u, 3321u },
  { 35u, 23u, 1162u },
  { 0u, 44u, 1162u },
  { 635u, 23u, 0u },
  { 0u, 44u, 0u },
  { 330u, 22u, 3321u },
  { 0u, 40u, 3321u },
  { 35u, 22u, 1162u },
  { 0u, 40u, 1162u },
  { 635u, 22u, 0u },
  { 0u, 40u, 0u },
  { 330u, 21u, 3321u },
  { 0u, 41u, 3321u },
  { 35u, 21u, 1162u },
  { 0u, 41u, 1162u },
  { 635u, 21u, 0u },
  { 0u, 41u, 0u },
  { 330u, 20u, 3321u },
  { 0u, 42u, 3321u },
  { 35u, 20u, 1162u },
  { 0u, 42u, 1162u },
  { 635u, 20u, 0u },
  { 0u, 42u, 0u },
  { 330u, 16u, 3321u },
  { 0u, 43u, 3321u },
  { 35u, 16u, 1162u },
  { 0u, 43u, 1162u },
  { 635u, 16u, 0u },
  { 0u, 43u, 0u },
  { 330u, 25u, 3321u },
  { 0u, 36u, 3321u },
  { 35u, 25u, 1162u },
  { 0u, 36u, 1162u },
  { 635u, 25u, 0u },
  { 0u, 36u, 0u },
  { 330u, 24u, 3321u },
  { 0u, 28u, 3321u },
  { 35u, 24u, 1162u },
  { 0u, 28u, 1162u },
  { 635u, 24u, 0u },
  { 0u, 28u, 0u },
  { 330u, 32u, 3321u },
  { 0u, 35u, 3321u },
  { 35u, 32u, 1162u },
  { 0u, 35u, 1162u },
  { 635u, 32u, 0u },
  { 0u, 35u, 0u },
  { 330u, 33u, 3321u },
  { 0u, 34u, 3321u },
  { 35u, 33u, 1162u },
  { 0u, 34u, 1162u },
  { 635u, 33u, 0u },
  { 0u, 34u, 0u },
};

const uint32_t SONG_EVENT_COUNT = sizeof(SONG) / sizeof(SONG[0]);
