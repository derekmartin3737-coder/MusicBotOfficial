#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: troubleshooting_black_keys.mid
// Base tempo: 60.00 BPM
// Tempo override: original timing
// Effective output tempo: 60.00 BPM
// Detected MIDI note range: C#1 to A#5
// Active playable layout: 57 mapped notes from C1 to C6 (non-contiguous)
// Fit mode: Black troubleshooting pattern
// Recognizability estimate: diagnostic sequence
// Strict coverage: 88 of 88 note events playable (100.0%)
// Octave transpose coverage: 88 of 88 note events playable (100.0%)
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
//   global channel 3 (PCA9685 0x60 channel 3): PCA9685 0x60 channel 3
//   global channel 5 (PCA9685 0x60 channel 5): PCA9685 0x60 channel 5
//   global channel 6 (PCA9685 0x60 channel 6): PCA9685 0x60 channel 6
//   global channel 14 (PCA9685 0x60 channel 14): PCA9685 0x60 channel 14
//   global channel 15 (PCA9685 0x60 channel 15): PCA9685 0x60 channel 15
//   global channel 17 (PCA9685 0x50 channel 1): PCA9685 0x50 channel 1
//   global channel 18 (PCA9685 0x50 channel 2): PCA9685 0x50 channel 2
//   global channel 19 (PCA9685 0x50 channel 3): PCA9685 0x50 channel 3
//   global channel 26 (PCA9685 0x50 channel 10): PCA9685 0x50 channel 10
//   global channel 27 (PCA9685 0x50 channel 11): PCA9685 0x50 channel 11
//   global channel 29 (PCA9685 0x50 channel 13): PCA9685 0x50 channel 13
//   global channel 30 (PCA9685 0x50 channel 14): PCA9685 0x50 channel 14
//   global channel 31 (PCA9685 0x50 channel 15): PCA9685 0x50 channel 15
//   global channel 38 (PCA9685 0x48 channel 6): PCA9685 0x48 channel 6
//   global channel 39 (PCA9685 0x48 channel 7): PCA9685 0x48 channel 7
//   global channel 45 (PCA9685 0x48 channel 13): PCA9685 0x48 channel 13
//   global channel 46 (PCA9685 0x48 channel 14): PCA9685 0x48 channel 14
//   global channel 47 (PCA9685 0x48 channel 15): PCA9685 0x48 channel 15
//   global channel 48 (PCA9685 0x40 channel 0): PCA9685 0x40 channel 0
//   global channel 49 (PCA9685 0x40 channel 1): PCA9685 0x40 channel 1
//   global channel 57 (PCA9685 0x40 channel 9): PCA9685 0x40 channel 9
//   global channel 58 (PCA9685 0x40 channel 10): PCA9685 0x40 channel 10
//   global channel 59 (PCA9685 0x40 channel 11): PCA9685 0x40 channel 11

// Actuation profile:
//   Channel 3: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 5: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 6: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 14: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 15: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 17: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 18: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 19: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 26: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 27: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 29: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 30: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 31: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 38: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 39: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 45: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 46: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 47: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 48: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 49: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 57: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 58: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 59: strike 2900-3900, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms

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
const uint8_t SONG_CHANNEL_COUNT = 23u;
const uint8_t SONG_CHANNELS[] = {
  3u,
  5u,
  6u,
  14u,
  15u,
  17u,
  18u,
  19u,
  26u,
  27u,
  29u,
  30u,
  31u,
  38u,
  39u,
  45u,
  46u,
  47u,
  48u,
  49u,
  57u,
  58u,
  59u,
};

typedef struct {
  uint32_t dt_ms;   // delay BEFORE this event
  uint8_t  channel; // global channel across every PCA9685 board
  uint16_t pwm;     // 0-4095 duty cycle
} SolenoidEvent;

const SolenoidEvent SONG[] PROGMEM = {
  { 0u, 3u, 3686u },
  { 45u, 3u, 1843u },
  { 625u, 3u, 0u },
  { 330u, 6u, 3686u },
  { 45u, 6u, 1843u },
  { 625u, 6u, 0u },
  { 330u, 5u, 3686u },
  { 45u, 5u, 1843u },
  { 625u, 5u, 0u },
  { 330u, 15u, 3686u },
  { 45u, 15u, 1843u },
  { 625u, 15u, 0u },
  { 330u, 14u, 3686u },
  { 45u, 14u, 1843u },
  { 625u, 14u, 0u },
  { 330u, 19u, 3686u },
  { 45u, 19u, 1843u },
  { 625u, 19u, 0u },
  { 330u, 18u, 3686u },
  { 45u, 18u, 1843u },
  { 625u, 18u, 0u },
  { 330u, 17u, 3686u },
  { 45u, 17u, 1843u },
  { 625u, 17u, 0u },
  { 330u, 27u, 3686u },
  { 45u, 27u, 1843u },
  { 625u, 27u, 0u },
  { 330u, 26u, 3686u },
  { 45u, 26u, 1843u },
  { 625u, 26u, 0u },
  { 330u, 31u, 3686u },
  { 45u, 31u, 1843u },
  { 625u, 31u, 0u },
  { 330u, 30u, 3686u },
  { 45u, 30u, 1843u },
  { 625u, 30u, 0u },
  { 330u, 29u, 3686u },
  { 45u, 29u, 1843u },
  { 625u, 29u, 0u },
  { 330u, 39u, 3686u },
  { 45u, 39u, 1843u },
  { 625u, 39u, 0u },
  { 330u, 38u, 3686u },
  { 45u, 38u, 1843u },
  { 625u, 38u, 0u },
  { 330u, 47u, 3686u },
  { 45u, 47u, 1843u },
  { 625u, 47u, 0u },
  { 330u, 46u, 3686u },
  { 45u, 46u, 1843u },
  { 625u, 46u, 0u },
  { 330u, 45u, 3686u },
  { 45u, 45u, 1843u },
  { 625u, 45u, 0u },
  { 330u, 48u, 3686u },
  { 45u, 48u, 1843u },
  { 625u, 48u, 0u },
  { 330u, 49u, 3686u },
  { 45u, 49u, 1843u },
  { 625u, 49u, 0u },
  { 330u, 59u, 3686u },
  { 45u, 59u, 1843u },
  { 625u, 59u, 0u },
  { 330u, 58u, 3686u },
  { 45u, 58u, 1843u },
  { 625u, 58u, 0u },
  { 330u, 57u, 3686u },
  { 45u, 57u, 1843u },
  { 625u, 57u, 0u },
  { 1730u, 3u, 3686u },
  { 0u, 5u, 3686u },
  { 45u, 3u, 1843u },
  { 0u, 5u, 1843u },
  { 625u, 3u, 0u },
  { 0u, 5u, 0u },
  { 330u, 6u, 3686u },
  { 0u, 15u, 3686u },
  { 45u, 6u, 1843u },
  { 0u, 15u, 1843u },
  { 625u, 6u, 0u },
  { 0u, 15u, 0u },
  { 330u, 5u, 3686u },
  { 0u, 14u, 3686u },
  { 45u, 5u, 1843u },
  { 0u, 14u, 1843u },
  { 625u, 5u, 0u },
  { 0u, 14u, 0u },
  { 330u, 15u, 3686u },
  { 0u, 19u, 3686u },
  { 45u, 15u, 1843u },
  { 0u, 19u, 1843u },
  { 625u, 15u, 0u },
  { 0u, 19u, 0u },
  { 330u, 14u, 3686u },
  { 0u, 18u, 3686u },
  { 45u, 14u, 1843u },
  { 0u, 18u, 1843u },
  { 625u, 14u, 0u },
  { 0u, 18u, 0u },
  { 330u, 17u, 3686u },
  { 0u, 19u, 3686u },
  { 45u, 17u, 1843u },
  { 0u, 19u, 1843u },
  { 625u, 17u, 0u },
  { 0u, 19u, 0u },
  { 330u, 18u, 3686u },
  { 0u, 27u, 3686u },
  { 45u, 18u, 1843u },
  { 0u, 27u, 1843u },
  { 625u, 18u, 0u },
  { 0u, 27u, 0u },
  { 330u, 17u, 3686u },
  { 0u, 26u, 3686u },
  { 45u, 17u, 1843u },
  { 0u, 26u, 1843u },
  { 625u, 17u, 0u },
  { 0u, 26u, 0u },
  { 330u, 27u, 3686u },
  { 0u, 31u, 3686u },
  { 45u, 27u, 1843u },
  { 0u, 31u, 1843u },
  { 625u, 27u, 0u },
  { 0u, 31u, 0u },
  { 330u, 26u, 3686u },
  { 0u, 30u, 3686u },
  { 45u, 26u, 1843u },
  { 0u, 30u, 1843u },
  { 625u, 26u, 0u },
  { 0u, 30u, 0u },
  { 330u, 29u, 3686u },
  { 0u, 31u, 3686u },
  { 45u, 29u, 1843u },
  { 0u, 31u, 1843u },
  { 625u, 29u, 0u },
  { 0u, 31u, 0u },
  { 330u, 30u, 3686u },
  { 0u, 39u, 3686u },
  { 45u, 30u, 1843u },
  { 0u, 39u, 1843u },
  { 625u, 30u, 0u },
  { 0u, 39u, 0u },
  { 330u, 29u, 3686u },
  { 0u, 38u, 3686u },
  { 45u, 29u, 1843u },
  { 0u, 38u, 1843u },
  { 625u, 29u, 0u },
  { 0u, 38u, 0u },
  { 330u, 39u, 3686u },
  { 0u, 47u, 3686u },
  { 45u, 39u, 1843u },
  { 0u, 47u, 1843u },
  { 625u, 39u, 0u },
  { 0u, 47u, 0u },
  { 330u, 38u, 3686u },
  { 0u, 46u, 3686u },
  { 45u, 38u, 1843u },
  { 0u, 46u, 1843u },
  { 625u, 38u, 0u },
  { 0u, 46u, 0u },
  { 330u, 45u, 3686u },
  { 0u, 47u, 3686u },
  { 45u, 45u, 1843u },
  { 0u, 47u, 1843u },
  { 625u, 45u, 0u },
  { 0u, 47u, 0u },
  { 330u, 46u, 3686u },
  { 0u, 48u, 3686u },
  { 45u, 46u, 1843u },
  { 0u, 48u, 1843u },
  { 625u, 46u, 0u },
  { 0u, 48u, 0u },
  { 330u, 45u, 3686u },
  { 0u, 49u, 3686u },
  { 45u, 45u, 1843u },
  { 0u, 49u, 1843u },
  { 625u, 45u, 0u },
  { 0u, 49u, 0u },
  { 330u, 48u, 3686u },
  { 0u, 59u, 3686u },
  { 45u, 48u, 1843u },
  { 0u, 59u, 1843u },
  { 625u, 48u, 0u },
  { 0u, 59u, 0u },
  { 330u, 49u, 3686u },
  { 0u, 58u, 3686u },
  { 45u, 49u, 1843u },
  { 0u, 58u, 1843u },
  { 625u, 49u, 0u },
  { 0u, 58u, 0u },
  { 330u, 57u, 3686u },
  { 0u, 59u, 3686u },
  { 45u, 57u, 1843u },
  { 0u, 59u, 1843u },
  { 625u, 57u, 0u },
  { 0u, 59u, 0u },
  { 1730u, 3u, 3686u },
  { 0u, 57u, 3686u },
  { 45u, 3u, 1843u },
  { 0u, 57u, 1843u },
  { 625u, 3u, 0u },
  { 0u, 57u, 0u },
  { 330u, 6u, 3686u },
  { 0u, 58u, 3686u },
  { 45u, 6u, 1843u },
  { 0u, 58u, 1843u },
  { 625u, 6u, 0u },
  { 0u, 58u, 0u },
  { 330u, 5u, 3686u },
  { 0u, 59u, 3686u },
  { 45u, 5u, 1843u },
  { 0u, 59u, 1843u },
  { 625u, 5u, 0u },
  { 0u, 59u, 0u },
  { 330u, 15u, 3686u },
  { 0u, 49u, 3686u },
  { 45u, 15u, 1843u },
  { 0u, 49u, 1843u },
  { 625u, 15u, 0u },
  { 0u, 49u, 0u },
  { 330u, 14u, 3686u },
  { 0u, 48u, 3686u },
  { 45u, 14u, 1843u },
  { 0u, 48u, 1843u },
  { 625u, 14u, 0u },
  { 0u, 48u, 0u },
  { 330u, 19u, 3686u },
  { 0u, 45u, 3686u },
  { 45u, 19u, 1843u },
  { 0u, 45u, 1843u },
  { 625u, 19u, 0u },
  { 0u, 45u, 0u },
  { 330u, 18u, 3686u },
  { 0u, 46u, 3686u },
  { 45u, 18u, 1843u },
  { 0u, 46u, 1843u },
  { 625u, 18u, 0u },
  { 0u, 46u, 0u },
  { 330u, 17u, 3686u },
  { 0u, 47u, 3686u },
  { 45u, 17u, 1843u },
  { 0u, 47u, 1843u },
  { 625u, 17u, 0u },
  { 0u, 47u, 0u },
  { 330u, 27u, 3686u },
  { 0u, 38u, 3686u },
  { 45u, 27u, 1843u },
  { 0u, 38u, 1843u },
  { 625u, 27u, 0u },
  { 0u, 38u, 0u },
  { 330u, 26u, 3686u },
  { 0u, 39u, 3686u },
  { 45u, 26u, 1843u },
  { 0u, 39u, 1843u },
  { 625u, 26u, 0u },
  { 0u, 39u, 0u },
  { 330u, 29u, 3686u },
  { 0u, 31u, 3686u },
  { 45u, 29u, 1843u },
  { 0u, 31u, 1843u },
  { 625u, 29u, 0u },
  { 0u, 31u, 0u },
  { 330u, 30u, 3686u },
  { 45u, 30u, 1843u },
  { 625u, 30u, 0u },
};

const uint32_t SONG_EVENT_COUNT = sizeof(SONG) / sizeof(SONG[0]);
