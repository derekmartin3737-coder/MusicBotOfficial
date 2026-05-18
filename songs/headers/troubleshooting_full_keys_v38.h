#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: troubleshooting_full_keys.mid
// Base tempo: 60.00 BPM
// Tempo override: original timing
// Effective output tempo: 60.00 BPM
// Detected MIDI note range: C1 to C6
// Active playable layout: 61 mapped notes from C1 to C6
// Fit mode: Full sweep troubleshooting sweep
// Recognizability estimate: diagnostic sequence
// Strict coverage: 61 of 61 note events playable (100.0%)
// Octave transpose coverage: 61 of 61 note events playable (100.0%)
// Octave transpose remap summary: not applicable for troubleshooting sequence
// Performance feel: disabled
// Auto measure sustain: disabled
// Mapping mode: explicit_note_map
// Forced retriggers: 0
// Delayed notes: 0
// Sustain pedal events: 0
// Unmapped notes skipped: 0
// Unmatched note_off events ignored: 0
// Dangling note_on events auto-closed: 0
// Percussion note events ignored: 0

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
//   global channel 0 (PCA9685 0x60 channel 0): PCA9685 0x60 channel 0
//   global channel 1 (PCA9685 0x60 channel 1): PCA9685 0x60 channel 1
//   global channel 2 (PCA9685 0x60 channel 2): PCA9685 0x60 channel 2
//   global channel 3 (PCA9685 0x60 channel 3): PCA9685 0x60 channel 3
//   global channel 4 (PCA9685 0x60 channel 4): PCA9685 0x60 channel 4
//   global channel 5 (PCA9685 0x60 channel 5): PCA9685 0x60 channel 5
//   global channel 6 (PCA9685 0x60 channel 6): PCA9685 0x60 channel 6
//   global channel 7 (PCA9685 0x60 channel 7): PCA9685 0x60 channel 7
//   global channel 8 (PCA9685 0x60 channel 8): PCA9685 0x60 channel 8
//   global channel 9 (PCA9685 0x60 channel 9): PCA9685 0x60 channel 9
//   global channel 10 (PCA9685 0x60 channel 10): PCA9685 0x60 channel 10
//   global channel 11 (PCA9685 0x60 channel 11): PCA9685 0x60 channel 11
//   global channel 12 (PCA9685 0x60 channel 12): PCA9685 0x60 channel 12
//   global channel 13 (PCA9685 0x60 channel 13): PCA9685 0x60 channel 13
//   global channel 14 (PCA9685 0x60 channel 14): PCA9685 0x60 channel 14
//   global channel 15 (PCA9685 0x60 channel 15): PCA9685 0x60 channel 15
//   global channel 16 (PCA9685 0x50 channel 0): PCA9685 0x50 channel 0
//   global channel 17 (PCA9685 0x50 channel 1): PCA9685 0x50 channel 1
//   global channel 18 (PCA9685 0x50 channel 2): PCA9685 0x50 channel 2
//   global channel 19 (PCA9685 0x50 channel 3): PCA9685 0x50 channel 3
//   global channel 20 (PCA9685 0x50 channel 4): PCA9685 0x50 channel 4
//   global channel 21 (PCA9685 0x50 channel 5): PCA9685 0x50 channel 5
//   global channel 22 (PCA9685 0x50 channel 6): PCA9685 0x50 channel 6
//   global channel 23 (PCA9685 0x50 channel 7): PCA9685 0x50 channel 7
//   global channel 24 (PCA9685 0x50 channel 8): PCA9685 0x50 channel 8
//   global channel 25 (PCA9685 0x50 channel 9): PCA9685 0x50 channel 9
//   global channel 26 (PCA9685 0x50 channel 10): PCA9685 0x50 channel 10
//   global channel 27 (PCA9685 0x50 channel 11): PCA9685 0x50 channel 11
//   global channel 28 (PCA9685 0x50 channel 12): PCA9685 0x50 channel 12
//   global channel 29 (PCA9685 0x50 channel 13): PCA9685 0x50 channel 13
//   global channel 30 (PCA9685 0x50 channel 14): PCA9685 0x50 channel 14
//   global channel 31 (PCA9685 0x50 channel 15): PCA9685 0x50 channel 15
//   global channel 32 (PCA9685 0x48 channel 0): PCA9685 0x48 channel 0
//   global channel 33 (PCA9685 0x48 channel 1): PCA9685 0x48 channel 1
//   global channel 34 (PCA9685 0x48 channel 2): PCA9685 0x48 channel 2
//   global channel 35 (PCA9685 0x48 channel 3): PCA9685 0x48 channel 3
//   global channel 36 (PCA9685 0x48 channel 4): PCA9685 0x48 channel 4
//   global channel 37 (PCA9685 0x48 channel 5): PCA9685 0x48 channel 5
//   global channel 38 (PCA9685 0x48 channel 6): PCA9685 0x48 channel 6
//   global channel 39 (PCA9685 0x48 channel 7): PCA9685 0x48 channel 7
//   global channel 40 (PCA9685 0x48 channel 8): PCA9685 0x48 channel 8
//   global channel 41 (PCA9685 0x48 channel 9): PCA9685 0x48 channel 9
//   global channel 42 (PCA9685 0x48 channel 10): PCA9685 0x48 channel 10
//   global channel 43 (PCA9685 0x48 channel 11): PCA9685 0x48 channel 11
//   global channel 44 (PCA9685 0x48 channel 12): PCA9685 0x48 channel 12
//   global channel 45 (PCA9685 0x48 channel 13): PCA9685 0x48 channel 13
//   global channel 46 (PCA9685 0x48 channel 14): PCA9685 0x48 channel 14
//   global channel 47 (PCA9685 0x48 channel 15): PCA9685 0x48 channel 15
//   global channel 48 (PCA9685 0x40 channel 0): PCA9685 0x40 channel 0
//   global channel 49 (PCA9685 0x40 channel 1): PCA9685 0x40 channel 1
//   global channel 50 (PCA9685 0x40 channel 2): PCA9685 0x40 channel 2
//   global channel 51 (PCA9685 0x40 channel 3): PCA9685 0x40 channel 3
//   global channel 52 (PCA9685 0x40 channel 4): PCA9685 0x40 channel 4
//   global channel 53 (PCA9685 0x40 channel 5): PCA9685 0x40 channel 5
//   global channel 54 (PCA9685 0x40 channel 6): PCA9685 0x40 channel 6
//   global channel 55 (PCA9685 0x40 channel 7): PCA9685 0x40 channel 7
//   global channel 56 (PCA9685 0x40 channel 8): PCA9685 0x40 channel 8
//   global channel 57 (PCA9685 0x40 channel 9): PCA9685 0x40 channel 9
//   global channel 58 (PCA9685 0x40 channel 10): PCA9685 0x40 channel 10
//   global channel 59 (PCA9685 0x40 channel 11): PCA9685 0x40 channel 11
//   global channel 60 (PCA9685 0x40 channel 12): PCA9685 0x40 channel 12

// Actuation profile:
//   Black key override: hold_max_pwm 2800, hold_min_pwm 2400, hold_ratio 0.72
//   Channel 0: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 20, minimum repeat period 94 ms
//   Channel 1: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 2: strike 3895-4095, velocity curve 1.0, hold 2600-2800, hold ratio 0.68, strike 250 ms, release delay 20 ms, rearm 40 ms, retrigger 25 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 3: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 4: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 5: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 40, minimum repeat period 94 ms
//   Channel 6: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 30, minimum repeat period 94 ms
//   Channel 7: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 8: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 40, minimum repeat period 94 ms
//   Channel 9: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 10: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 11: strike 2700-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 12: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 13: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 14: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 15: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 16: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 17: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 40, minimum repeat period 94 ms
//   Channel 18: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 19: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 20: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 21: strike 2700-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 50, minimum repeat period 94 ms
//   Channel 22: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 23: strike 2700-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 45, minimum repeat period 94 ms
//   Channel 24: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 25: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 26: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 27: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 28: strike 4095-4095, velocity curve 1.0, hold 3000-3200, hold ratio 0.78, strike 160 ms, release delay 20 ms, rearm 40 ms, retrigger 25 ms, velocity override 127, minimum repeat period 94 ms
//   Channel 29: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 40, minimum repeat period 94 ms
//   Channel 30: strike 4095-4095, velocity curve 1.0, hold 3000-3200, hold ratio 0.78, strike 160 ms, release delay 20 ms, rearm 40 ms, retrigger 25 ms, velocity override 127, minimum repeat period 94 ms
//   Channel 31: strike 4095-4095, velocity curve 1.0, hold 3000-3200, hold ratio 0.78, strike 160 ms, release delay 20 ms, rearm 40 ms, retrigger 25 ms, velocity override 127, minimum repeat period 94 ms
//   Channel 32: strike 2700-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 33: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 34: strike 2700-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 35: strike 2700-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 100, minimum repeat period 94 ms
//   Channel 36: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 37: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 38: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 39: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 40: strike 2700-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 10, minimum repeat period 94 ms
//   Channel 41: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 40, minimum repeat period 94 ms
//   Channel 42: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 43: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 20, minimum repeat period 94 ms
//   Channel 44: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 45: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 46: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 47: strike 3850-4095, velocity curve 1.0, hold 2700-2900, hold ratio 0.72, strike 95 ms, release delay 20 ms, rearm 40 ms, retrigger 25 ms, velocity override 85, minimum repeat period 94 ms
//   Channel 48: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 49: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 50: strike 2700-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 10, minimum repeat period 94 ms
//   Channel 51: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 52: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 5, minimum repeat period 94 ms
//   Channel 53: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 1, minimum repeat period 94 ms
//   Channel 54: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 55: strike 2700-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 70, minimum repeat period 94 ms
//   Channel 56: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 60, minimum repeat period 94 ms
//   Channel 57: strike 4095-4095, velocity curve 1.0, hold 3000-3200, hold ratio 0.78, strike 160 ms, release delay 20 ms, rearm 40 ms, retrigger 25 ms, velocity override 127, minimum repeat period 94 ms
//   Channel 58: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms
//   Channel 59: strike 2700-3900, velocity curve 1.0, hold 1200-2000, hold ratio 0.5, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 50, minimum repeat period 94 ms
//   Channel 60: strike 2700-3900, velocity curve 1.0, hold 2400-2600, hold ratio 0.66, strike 45 ms, release delay 20 ms, rearm 25 ms, retrigger 16 ms, velocity override 85, minimum repeat period 94 ms

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
const uint8_t SONG_CHANNEL_COUNT = 61u;
const uint8_t SONG_CHANNELS[] = {
  0u,
  1u,
  2u,
  3u,
  4u,
  5u,
  6u,
  7u,
  8u,
  9u,
  10u,
  11u,
  12u,
  13u,
  14u,
  15u,
  16u,
  17u,
  18u,
  19u,
  20u,
  21u,
  22u,
  23u,
  24u,
  25u,
  26u,
  27u,
  28u,
  29u,
  30u,
  31u,
  32u,
  33u,
  34u,
  35u,
  36u,
  37u,
  38u,
  39u,
  40u,
  41u,
  42u,
  43u,
  44u,
  45u,
  46u,
  47u,
  48u,
  49u,
  50u,
  51u,
  52u,
  53u,
  54u,
  55u,
  56u,
  57u,
  58u,
  59u,
  60u,
};

typedef struct {
  uint32_t dt_ms;   // delay BEFORE this event
  uint8_t  channel; // global channel across every PCA9685 board
  uint16_t pwm;     // 0-4095 duty cycle
} SolenoidEvent;

const SolenoidEvent SONG[] PROGMEM = {
  { 0u, 1u, 3500u },
  { 45u, 1u, 1750u },
  { 535u, 1u, 0u },
  { 140u, 3u, 3500u },
  { 45u, 3u, 2520u },
  { 535u, 3u, 0u },
  { 140u, 0u, 2881u },
  { 45u, 0u, 1440u },
  { 535u, 0u, 0u },
  { 140u, 2u, 4028u },
  { 250u, 2u, 2739u },
  { 330u, 2u, 0u },
  { 140u, 11u, 3500u },
  { 45u, 11u, 2400u },
  { 535u, 11u, 0u },
  { 140u, 10u, 3500u },
  { 45u, 10u, 1750u },
  { 535u, 10u, 0u },
  { 140u, 7u, 3500u },
  { 45u, 7u, 2520u },
  { 535u, 7u, 0u },
  { 140u, 9u, 3500u },
  { 45u, 9u, 1750u },
  { 535u, 9u, 0u },
  { 140u, 6u, 2976u },
  { 45u, 6u, 2400u },
  { 535u, 6u, 0u },
  { 140u, 8u, 3071u },
  { 45u, 8u, 1536u },
  { 535u, 8u, 0u },
  { 140u, 5u, 3071u },
  { 45u, 5u, 2400u },
  { 535u, 5u, 0u },
  { 140u, 4u, 3500u },
  { 45u, 4u, 1750u },
  { 535u, 4u, 0u },
  { 140u, 13u, 3500u },
  { 45u, 13u, 1750u },
  { 535u, 13u, 0u },
  { 140u, 15u, 3500u },
  { 45u, 15u, 2520u },
  { 535u, 15u, 0u },
  { 140u, 12u, 3500u },
  { 45u, 12u, 1750u },
  { 535u, 12u, 0u },
  { 140u, 14u, 3500u },
  { 45u, 14u, 2520u },
  { 535u, 14u, 0u },
  { 140u, 23u, 3119u },
  { 45u, 23u, 2400u },
  { 535u, 23u, 0u },
  { 140u, 22u, 3500u },
  { 45u, 22u, 1750u },
  { 535u, 22u, 0u },
  { 140u, 19u, 3500u },
  { 45u, 19u, 2520u },
  { 535u, 19u, 0u },
  { 140u, 21u, 3167u },
  { 45u, 21u, 2400u },
  { 535u, 21u, 0u },
  { 140u, 18u, 3500u },
  { 45u, 18u, 2520u },
  { 535u, 18u, 0u },
  { 140u, 20u, 3500u },
  { 45u, 20u, 1750u },
  { 535u, 20u, 0u },
  { 140u, 17u, 3071u },
  { 45u, 17u, 2400u },
  { 535u, 17u, 0u },
  { 140u, 16u, 3500u },
  { 45u, 16u, 1750u },
  { 535u, 16u, 0u },
  { 140u, 25u, 3500u },
  { 45u, 25u, 1750u },
  { 535u, 25u, 0u },
  { 140u, 27u, 3500u },
  { 45u, 27u, 2520u },
  { 535u, 27u, 0u },
  { 140u, 24u, 3500u },
  { 45u, 24u, 1750u },
  { 535u, 24u, 0u },
  { 140u, 26u, 3500u },
  { 45u, 26u, 2520u },
  { 535u, 26u, 0u },
  { 140u, 35u, 3643u },
  { 45u, 35u, 2404u },
  { 535u, 35u, 0u },
  { 140u, 34u, 3500u },
  { 45u, 34u, 2400u },
  { 535u, 34u, 0u },
  { 140u, 31u, 4095u },
  { 160u, 31u, 3194u },
  { 510u, 31u, 0u },
  { 50u, 33u, 3500u },
  { 45u, 33u, 1750u },
  { 535u, 33u, 0u },
  { 140u, 30u, 4095u },
  { 160u, 30u, 3194u },
  { 510u, 30u, 0u },
  { 50u, 32u, 3500u },
  { 45u, 32u, 2400u },
  { 535u, 32u, 0u },
  { 140u, 29u, 3071u },
  { 45u, 29u, 2400u },
  { 535u, 29u, 0u },
  { 140u, 28u, 4095u },
  { 160u, 28u, 3194u },
  { 510u, 28u, 0u },
  { 50u, 37u, 3500u },
  { 45u, 37u, 1750u },
  { 535u, 37u, 0u },
  { 140u, 39u, 3500u },
  { 45u, 39u, 2520u },
  { 535u, 39u, 0u },
  { 140u, 36u, 3500u },
  { 45u, 36u, 1750u },
  { 535u, 36u, 0u },
  { 140u, 38u, 3500u },
  { 45u, 38u, 2520u },
  { 535u, 38u, 0u },
  { 140u, 43u, 2881u },
  { 45u, 43u, 1440u },
  { 535u, 43u, 0u },
  { 140u, 42u, 3500u },
  { 45u, 42u, 1750u },
  { 535u, 42u, 0u },
  { 140u, 47u, 4013u },
  { 95u, 47u, 2889u },
  { 485u, 47u, 0u },
  { 140u, 41u, 3071u },
  { 45u, 41u, 1536u },
  { 535u, 41u, 0u },
  { 140u, 46u, 3500u },
  { 45u, 46u, 2520u },
  { 535u, 46u, 0u },
  { 140u, 40u, 2786u },
  { 45u, 40u, 2400u },
  { 535u, 40u, 0u },
  { 140u, 45u, 3500u },
  { 45u, 45u, 2520u },
  { 535u, 45u, 0u },
  { 140u, 44u, 3500u },
  { 45u, 44u, 1750u },
  { 535u, 44u, 0u },
  { 140u, 50u, 2786u },
  { 45u, 50u, 2400u },
  { 535u, 50u, 0u },
  { 140u, 48u, 3500u },
  { 45u, 48u, 2520u },
  { 535u, 48u, 0u },
  { 140u, 51u, 3500u },
  { 45u, 51u, 1750u },
  { 535u, 51u, 0u },
  { 140u, 49u, 3500u },
  { 45u, 49u, 2520u },
  { 535u, 49u, 0u },
  { 140u, 52u, 2738u },
  { 45u, 52u, 1369u },
  { 535u, 52u, 0u },
  { 140u, 53u, 2700u },
  { 45u, 53u, 1350u },
  { 535u, 53u, 0u },
  { 140u, 59u, 3167u },
  { 45u, 59u, 2400u },
  { 535u, 59u, 0u },
  { 140u, 54u, 3500u },
  { 45u, 54u, 1750u },
  { 535u, 54u, 0u },
  { 140u, 58u, 3500u },
  { 45u, 58u, 2520u },
  { 535u, 58u, 0u },
  { 140u, 55u, 3357u },
  { 45u, 55u, 2400u },
  { 535u, 55u, 0u },
  { 140u, 57u, 4095u },
  { 160u, 57u, 3194u },
  { 510u, 57u, 0u },
  { 50u, 56u, 3262u },
  { 45u, 56u, 1631u },
  { 535u, 56u, 0u },
  { 140u, 60u, 3500u },
  { 45u, 60u, 2400u },
  { 535u, 60u, 0u },
};

const uint32_t SONG_EVENT_COUNT = sizeof(SONG) / sizeof(SONG[0]);
