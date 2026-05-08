#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: John Powell - Test Drive (How To Train Your Dragon)  (midi by Carlo Prato) (www.cprato.com).mid
// Base tempo: 111.00 BPM
// Tempo override: original timing
// Effective output tempo: 111.00 BPM
// Detected MIDI note range: D2 to C#6
// Active playable layout: 61 mapped notes from C1 to C6
// Fit mode: strict (original pitches, skip out-of-range notes)
// Recognizability estimate: very likely recognizable
// Strict coverage: 133 of 137 note events playable (97.1%)
// Octave transpose coverage: 137 of 137 note events playable (100.0%)
// Octave transpose remap summary: no octave remapping was applied
// Performance feel: disabled
// Auto measure sustain: disabled
// Mapping mode: explicit_note_map
// Forced retriggers: 27
// Delayed notes: 35
// Sustain pedal events: 0
// Unmapped notes skipped: 4
// Unmatched note_off events ignored: 0
// Dangling note_on events auto-closed: 0
// Percussion note events ignored: 176

// Piano actuator mapping used for this file:
//   Explicit note-to-channel mode
//   MIDI note 24 (C1) -> global channel 1 (PCA9685 0x60 channel 1) (PCA9685 0x60 channel 1)
//   MIDI note 25 (C#1) -> global channel 3 (PCA9685 0x60 channel 3) (PCA9685 0x60 channel 3)
//   MIDI note 26 (D1) -> global channel 0 (PCA9685 0x60 channel 0) (PCA9685 0x60 channel 0)
//   MIDI note 27 (D#1) -> global channel 2 (PCA9685 0x60 channel 2) (PCA9685 0x60 channel 2)
//   MIDI note 28 (E1) -> global channel 11 (PCA9685 0x60 channel 11) (PCA9685 0x60 channel 11)
//   MIDI note 29 (F1) -> global channel 10 (PCA9685 0x60 channel 10) (PCA9685 0x60 channel 10)
//   MIDI note 30 (F#1) -> global channel 7 (PCA9685 0x60 channel 7) (PCA9685 0x60 channel 7)
//   MIDI note 31 (G1) -> global channel 9 (PCA9685 0x60 channel 9) (PCA9685 0x60 channel 9)
//   MIDI note 32 (G#1) -> global channel 6 (PCA9685 0x60 channel 6) (PCA9685 0x60 channel 6)
//   MIDI note 33 (A1) -> global channel 8 (PCA9685 0x60 channel 8) (PCA9685 0x60 channel 8)
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
//   MIDI note 60 (C4) -> global channel 37 (PCA9685 0x48 channel 5) (PCA9685 0x48 channel 5)
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
//   Sustain pedal -> global channel 61 (PCA9685 0x40 channel 13) (Sustain pedal (PCA9685 0x40 channel 13))

// Active hardware channels in this export:
//   global channel 12 (PCA9685 0x60 channel 12): PCA9685 0x60 channel 12
//   global channel 16 (PCA9685 0x50 channel 0): PCA9685 0x50 channel 0
//   global channel 19 (PCA9685 0x50 channel 3): PCA9685 0x50 channel 3
//   global channel 20 (PCA9685 0x50 channel 4): PCA9685 0x50 channel 4
//   global channel 21 (PCA9685 0x50 channel 5): PCA9685 0x50 channel 5
//   global channel 23 (PCA9685 0x50 channel 7): PCA9685 0x50 channel 7
//   global channel 24 (PCA9685 0x50 channel 8): PCA9685 0x50 channel 8
//   global channel 27 (PCA9685 0x50 channel 11): PCA9685 0x50 channel 11
//   global channel 28 (PCA9685 0x50 channel 12): PCA9685 0x50 channel 12
//   global channel 31 (PCA9685 0x50 channel 15): PCA9685 0x50 channel 15
//   global channel 32 (PCA9685 0x48 channel 0): PCA9685 0x48 channel 0
//   global channel 33 (PCA9685 0x48 channel 1): PCA9685 0x48 channel 1
//   global channel 35 (PCA9685 0x48 channel 3): PCA9685 0x48 channel 3
//   global channel 36 (PCA9685 0x48 channel 4): PCA9685 0x48 channel 4
//   global channel 39 (PCA9685 0x48 channel 7): PCA9685 0x48 channel 7
//   global channel 40 (PCA9685 0x48 channel 8): PCA9685 0x48 channel 8
//   global channel 44 (PCA9685 0x48 channel 12): PCA9685 0x48 channel 12
//   global channel 48 (PCA9685 0x40 channel 0): PCA9685 0x40 channel 0
//   global channel 51 (PCA9685 0x40 channel 3): PCA9685 0x40 channel 3
//   global channel 52 (PCA9685 0x40 channel 4): PCA9685 0x40 channel 4
//   global channel 54 (PCA9685 0x40 channel 6): PCA9685 0x40 channel 6
//   global channel 55 (PCA9685 0x40 channel 7): PCA9685 0x40 channel 7
//   global channel 56 (PCA9685 0x40 channel 8): PCA9685 0x40 channel 8
//   global channel 59 (PCA9685 0x40 channel 11): PCA9685 0x40 channel 11

// Actuation profile:
//   Black key override: hold_max_pwm 2800, hold_min_pwm 2400, hold_ratio 0.72
//   Channel 12: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 16: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 19: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 20: strike 2900-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 21: strike 2900-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 23: strike 2900-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 24: strike 2900-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 27: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 28: strike 3350-4050, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 60 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 31: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 32: strike 2900-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 33: strike 2900-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 35: strike 2900-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 36: strike 2900-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 39: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 40: strike 2900-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 44: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 48: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 51: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 52: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 54: strike 2900-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 55: strike 2900-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 56: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 59: strike 2900-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms

// Most skipped notes in this export:
//   C#6 (85): 4

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
const uint8_t SONG_CHANNEL_COUNT = 24u;
const uint8_t SONG_CHANNELS[] = {
  12u,
  16u,
  19u,
  20u,
  21u,
  23u,
  24u,
  27u,
  28u,
  31u,
  32u,
  33u,
  35u,
  36u,
  39u,
  40u,
  44u,
  48u,
  51u,
  52u,
  54u,
  55u,
  56u,
  59u,
};

typedef struct {
  uint32_t dt_ms;   // delay BEFORE this event
  uint8_t  channel; // global channel across every PCA9685 board
  uint16_t pwm;     // 0-4095 duty cycle
} SolenoidEvent;

const SolenoidEvent SONG[] PROGMEM = {
  { 0u, 16u, 3686u },
  { 0u, 28u, 3900u },
  { 0u, 31u, 3686u },
  { 0u, 51u, 3686u },
  { 21u, 16u, 0u },
  { 16u, 16u, 3686u },
  { 8u, 31u, 2654u },
  { 0u, 51u, 1843u },
  { 15u, 28u, 2574u },
  { 22u, 16u, 1843u },
  { 952u, 51u, 0u },
  { 48u, 21u, 3686u },
  { 0u, 24u, 3686u },
  { 0u, 51u, 3686u },
  { 20u, 28u, 0u },
  { 0u, 31u, 0u },
  { 1u, 21u, 0u },
  { 16u, 21u, 3686u },
  { 8u, 24u, 2433u },
  { 0u, 28u, 3900u },
  { 0u, 51u, 1843u },
  { 12u, 16u, 0u },
  { 25u, 21u, 2433u },
  { 23u, 28u, 2574u },
  { 929u, 51u, 0u },
  { 48u, 20u, 3686u },
  { 0u, 32u, 3686u },
  { 0u, 35u, 3686u },
  { 0u, 52u, 3686u },
  { 20u, 24u, 0u },
  { 1u, 20u, 0u },
  { 16u, 20u, 3686u },
  { 8u, 32u, 2433u },
  { 0u, 35u, 2433u },
  { 0u, 52u, 1843u },
  { 12u, 21u, 0u },
  { 8u, 28u, 0u },
  { 17u, 20u, 2433u },
  { 682u, 52u, 0u },
  { 48u, 59u, 3686u },
  { 45u, 59u, 2654u },
  { 178u, 59u, 0u },
  { 48u, 24u, 3686u },
  { 0u, 31u, 3686u },
  { 0u, 36u, 3686u },
  { 0u, 59u, 3686u },
  { 20u, 32u, 0u },
  { 0u, 35u, 0u },
  { 1u, 24u, 0u },
  { 16u, 24u, 3686u },
  { 8u, 31u, 2654u },
  { 0u, 36u, 2433u },
  { 0u, 59u, 2654u },
  { 12u, 20u, 0u },
  { 25u, 24u, 2433u },
  { 459u, 27u, 3686u },
  { 0u, 35u, 3686u },
  { 0u, 39u, 3686u },
  { 20u, 31u, 0u },
  { 0u, 36u, 0u },
  { 1u, 27u, 0u },
  { 16u, 27u, 3686u },
  { 8u, 35u, 2433u },
  { 0u, 39u, 2654u },
  { 12u, 24u, 0u },
  { 25u, 27u, 2654u },
  { 459u, 16u, 3686u },
  { 0u, 28u, 3900u },
  { 0u, 31u, 3686u },
  { 20u, 35u, 0u },
  { 0u, 39u, 0u },
  { 1u, 16u, 0u },
  { 16u, 16u, 3686u },
  { 8u, 31u, 2654u },
  { 12u, 27u, 0u },
  { 3u, 28u, 2574u },
  { 22u, 16u, 1843u },
  { 208u, 59u, 0u },
  { 250u, 40u, 3686u },
  { 45u, 40u, 2433u },
  { 495u, 21u, 3686u },
  { 0u, 24u, 3686u },
  { 0u, 59u, 3686u },
  { 20u, 28u, 0u },
  { 0u, 31u, 0u },
  { 0u, 40u, 0u },
  { 1u, 21u, 0u },
  { 16u, 21u, 3686u },
  { 8u, 24u, 2433u },
  { 0u, 28u, 3900u },
  { 0u, 59u, 2654u },
  { 12u, 16u, 0u },
  { 25u, 21u, 2433u },
  { 23u, 28u, 2574u },
  { 435u, 55u, 3686u },
  { 20u, 59u, 0u },
  { 25u, 55u, 2433u },
  { 496u, 20u, 3686u },
  { 0u, 32u, 3686u },
  { 0u, 35u, 3686u },
  { 0u, 52u, 3686u },
  { 20u, 24u, 0u },
  { 0u, 55u, 0u },
  { 1u, 20u, 0u },
  { 16u, 20u, 3686u },
  { 8u, 32u, 2433u },
  { 0u, 35u, 2433u },
  { 0u, 52u, 1843u },
  { 12u, 21u, 0u },
  { 8u, 28u, 0u },
  { 17u, 20u, 2433u },
  { 479u, 52u, 0u },
  { 250u, 59u, 3686u },
  { 45u, 59u, 2654u },
  { 178u, 59u, 0u },
  { 48u, 24u, 3686u },
  { 0u, 31u, 3686u },
  { 0u, 36u, 3686u },
  { 0u, 59u, 3686u },
  { 20u, 32u, 0u },
  { 0u, 35u, 0u },
  { 1u, 24u, 0u },
  { 16u, 24u, 3686u },
  { 8u, 31u, 2654u },
  { 0u, 36u, 2433u },
  { 0u, 59u, 2654u },
  { 12u, 20u, 0u },
  { 25u, 24u, 2433u },
  { 459u, 27u, 3686u },
  { 0u, 35u, 3686u },
  { 0u, 39u, 3686u },
  { 20u, 31u, 0u },
  { 0u, 36u, 0u },
  { 1u, 27u, 0u },
  { 16u, 27u, 3686u },
  { 8u, 35u, 2433u },
  { 0u, 39u, 2654u },
  { 12u, 24u, 0u },
  { 25u, 27u, 2654u },
  { 208u, 59u, 0u },
  { 250u, 16u, 3686u },
  { 0u, 28u, 3900u },
  { 0u, 31u, 3686u },
  { 0u, 59u, 3686u },
  { 20u, 35u, 0u },
  { 0u, 39u, 0u },
  { 1u, 16u, 0u },
  { 16u, 16u, 3686u },
  { 8u, 31u, 2654u },
  { 0u, 59u, 2654u },
  { 12u, 27u, 0u },
  { 3u, 28u, 2574u },
  { 22u, 16u, 1843u },
  { 188u, 44u, 3686u },
  { 20u, 59u, 0u },
  { 25u, 44u, 1843u },
  { 225u, 56u, 3686u },
  { 20u, 44u, 0u },
  { 25u, 56u, 1843u },
  { 225u, 55u, 3686u },
  { 20u, 56u, 0u },
  { 25u, 55u, 2433u },
  { 225u, 19u, 3686u },
  { 0u, 27u, 3686u },
  { 0u, 59u, 3686u },
  { 20u, 28u, 0u },
  { 0u, 31u, 0u },
  { 0u, 55u, 0u },
  { 1u, 19u, 0u },
  { 16u, 19u, 3686u },
  { 8u, 27u, 2654u },
  { 0u, 31u, 3686u },
  { 0u, 59u, 2654u },
  { 12u, 16u, 0u },
  { 25u, 19u, 2654u },
  { 8u, 31u, 2654u },
  { 721u, 52u, 3686u },
  { 20u, 59u, 0u },
  { 25u, 52u, 1843u },
  { 178u, 52u, 0u },
  { 48u, 20u, 3686u },
  { 0u, 32u, 3686u },
  { 0u, 35u, 3686u },
  { 0u, 52u, 3686u },
  { 20u, 27u, 0u },
  { 1u, 20u, 0u },
  { 16u, 20u, 3686u },
  { 8u, 32u, 2433u },
  { 0u, 35u, 2433u },
  { 0u, 52u, 1843u },
  { 12u, 19u, 0u },
  { 8u, 31u, 0u },
  { 17u, 20u, 2433u },
  { 729u, 59u, 3686u },
  { 20u, 52u, 0u },
  { 25u, 59u, 2654u },
  { 225u, 16u, 3686u },
  { 0u, 23u, 3686u },
  { 0u, 44u, 3686u },
  { 20u, 32u, 0u },
  { 0u, 35u, 0u },
  { 0u, 59u, 0u },
  { 1u, 23u, 0u },
  { 16u, 23u, 3686u },
  { 8u, 16u, 1843u },
  { 0u, 35u, 3686u },
  { 0u, 44u, 1843u },
  { 12u, 20u, 0u },
  { 25u, 23u, 2433u },
  { 8u, 35u, 2433u },
  { 403u, 44u, 0u },
  { 48u, 44u, 3686u },
  { 45u, 44u, 1843u },
  { 225u, 48u, 3686u },
  { 20u, 44u, 0u },
  { 25u, 48u, 2654u },
  { 225u, 21u, 3686u },
  { 0u, 24u, 3686u },
  { 0u, 33u, 3686u },
  { 0u, 51u, 3686u },
  { 20u, 16u, 0u },
  { 0u, 48u, 0u },
  { 1u, 21u, 0u },
  { 16u, 21u, 3686u },
  { 8u, 24u, 2433u },
  { 0u, 33u, 2433u },
  { 0u, 51u, 1843u },
  { 12u, 23u, 0u },
  { 8u, 35u, 0u },
  { 17u, 21u, 2433u },
  { 411u, 51u, 0u },
  { 48u, 51u, 3686u },
  { 45u, 51u, 1843u },
  { 225u, 52u, 3686u },
  { 20u, 51u, 0u },
  { 25u, 52u, 1843u },
  { 225u, 51u, 3686u },
  { 20u, 52u, 0u },
  { 25u, 51u, 1843u },
  { 225u, 48u, 3686u },
  { 20u, 51u, 0u },
  { 25u, 48u, 2654u },
  { 225u, 44u, 3686u },
  { 20u, 48u, 0u },
  { 25u, 44u, 1843u },
  { 225u, 40u, 3686u },
  { 20u, 44u, 0u },
  { 25u, 40u, 2433u },
  { 225u, 16u, 3686u },
  { 0u, 23u, 3686u },
  { 0u, 35u, 3686u },
  { 0u, 44u, 3686u },
  { 20u, 24u, 0u },
  { 0u, 33u, 0u },
  { 0u, 40u, 0u },
  { 1u, 23u, 0u },
  { 16u, 23u, 3686u },
  { 8u, 16u, 1843u },
  { 0u, 35u, 2433u },
  { 0u, 44u, 1843u },
  { 12u, 21u, 0u },
  { 25u, 23u, 2433u },
  { 1019u, 44u, 0u },
  { 1062u, 12u, 3686u },
  { 0u, 20u, 3686u },
  { 0u, 24u, 3686u },
  { 0u, 59u, 3686u },
  { 20u, 16u, 0u },
  { 0u, 35u, 0u },
  { 1u, 12u, 0u },
  { 16u, 12u, 3686u },
  { 8u, 20u, 2433u },
  { 0u, 24u, 2433u },
  { 0u, 59u, 2654u },
  { 12u, 23u, 0u },
  { 25u, 12u, 1843u },
  { 884u, 59u, 0u },
  { 115u, 54u, 3686u },
  { 45u, 54u, 2433u },
  { 921u, 54u, 0u },
  { 115u, 52u, 3686u },
  { 45u, 52u, 1843u },
  { 496u, 54u, 3686u },
  { 20u, 52u, 0u },
  { 25u, 54u, 2433u },
  { 225u, 59u, 3686u },
  { 20u, 54u, 0u },
  { 25u, 59u, 2654u },
  { 245u, 59u, 0u },
  { 25u, 59u, 3686u },
  { 45u, 59u, 2654u },
  { 1012u, 12u, 0u },
  { 0u, 20u, 0u },
  { 0u, 24u, 0u },
  { 16u, 12u, 3686u },
  { 9u, 20u, 3686u },
  { 0u, 24u, 3686u },
  { 12u, 12u, 0u },
  { 8u, 59u, 0u },
  { 8u, 12u, 3686u },
  { 17u, 20u, 2433u },
  { 0u, 24u, 2433u },
  { 28u, 12u, 1843u },
  { 423u, 59u, 3686u },
  { 45u, 59u, 2654u },
  { 495u, 54u, 3686u },
  { 20u, 59u, 0u },
  { 25u, 54u, 2433u },
  { 766u, 59u, 3686u },
  { 20u, 54u, 0u },
  { 25u, 59u, 2654u },
  { 225u, 52u, 3686u },
  { 20u, 59u, 0u },
  { 25u, 52u, 1843u },
  { 225u, 59u, 3686u },
  { 20u, 52u, 0u },
  { 25u, 59u, 2654u },
  { 225u, 54u, 3686u },
  { 20u, 59u, 0u },
  { 25u, 54u, 2433u },
  { 225u, 59u, 3686u },
  { 20u, 54u, 0u },
  { 25u, 59u, 2654u },
  { 245u, 59u, 0u },
  { 25u, 59u, 3686u },
  { 45u, 59u, 2654u },
  { 1012u, 12u, 0u },
  { 0u, 20u, 0u },
  { 0u, 24u, 0u },
  { 16u, 12u, 3686u },
  { 0u, 20u, 3686u },
  { 0u, 24u, 3686u },
  { 21u, 12u, 0u },
  { 8u, 59u, 0u },
  { 8u, 12u, 3686u },
  { 8u, 20u, 2433u },
  { 0u, 24u, 2433u },
  { 37u, 12u, 1843u },
  { 423u, 56u, 3686u },
  { 45u, 56u, 1843u },
  { 448u, 56u, 0u },
  { 48u, 56u, 3686u },
  { 45u, 56u, 1843u },
  { 448u, 56u, 0u },
  { 1130u, 55u, 3686u },
  { 45u, 55u, 2433u },
  { 448u, 55u, 0u },
  { 48u, 59u, 3686u },
  { 45u, 59u, 2654u },
  { 448u, 59u, 0u },
  { 609u, 12u, 0u },
  { 0u, 20u, 0u },
  { 0u, 24u, 0u },
  { 16u, 12u, 3686u },
  { 0u, 20u, 3686u },
  { 0u, 24u, 3686u },
  { 21u, 12u, 0u },
  { 16u, 12u, 3686u },
  { 8u, 20u, 2433u },
  { 0u, 24u, 2433u },
  { 37u, 12u, 1843u },
  { 423u, 56u, 3686u },
  { 45u, 56u, 1843u },
  { 448u, 56u, 0u },
  { 48u, 56u, 3686u },
  { 45u, 56u, 1843u },
  { 448u, 56u, 0u },
  { 1130u, 56u, 3686u },
  { 45u, 56u, 1843u },
  { 225u, 55u, 3686u },
  { 20u, 56u, 0u },
  { 25u, 55u, 2433u },
  { 178u, 55u, 0u },
  { 48u, 55u, 3686u },
  { 45u, 55u, 2433u },
  { 786u, 55u, 0u },
  { 306u, 20u, 0u },
  { 0u, 24u, 0u },
  { 37u, 12u, 0u },
};

const uint32_t SONG_EVENT_COUNT = sizeof(SONG) / sizeof(SONG[0]);
