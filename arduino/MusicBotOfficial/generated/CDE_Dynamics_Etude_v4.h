#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: CDE_Dynamics_Etude.mid
// Base tempo: 126.00 BPM
// Tempo override: original timing
// Effective output tempo: 126.00 BPM
// Detected MIDI note range: C3 to E3
// Active playable layout: 3 mapped notes from C3 to E3 (non-contiguous)
// Fit mode: strict (original pitches, skip out-of-range notes)
// Recognizability estimate: very likely recognizable
// Strict coverage: 48 of 48 note events playable (100.0%)
// Octave transpose coverage: 48 of 48 note events playable (100.0%)
// Mapping mode: explicit_note_map
// Forced retriggers: 0
// Delayed notes: 8
// Unmapped notes skipped: 0
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
  { 0u, 0u, 3495u },
  { 35u, 0u, 2167u },
  { 84u, 1u, 2847u },
  { 6u, 0u, 0u },
  { 29u, 1u, 1651u },
  { 84u, 2u, 2909u },
  { 6u, 1u, 0u },
  { 29u, 2u, 1687u },
  { 84u, 0u, 3495u },
  { 6u, 2u, 0u },
  { 25u, 2u, 2950u },
  { 4u, 0u, 2167u },
  { 31u, 2u, 1711u },
  { 119u, 0u, 0u },
  { 31u, 2u, 0u },
  { 23u, 1u, 2826u },
  { 35u, 1u, 1639u },
  { 84u, 0u, 3565u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2210u },
  { 84u, 1u, 2929u },
  { 6u, 0u, 0u },
  { 29u, 1u, 1699u },
  { 84u, 2u, 2991u },
  { 6u, 1u, 0u },
  { 29u, 2u, 1735u },
  { 84u, 0u, 3565u },
  { 6u, 2u, 0u },
  { 25u, 2u, 3033u },
  { 4u, 0u, 2210u },
  { 31u, 2u, 1759u },
  { 119u, 0u, 0u },
  { 31u, 2u, 0u },
  { 23u, 1u, 2909u },
  { 35u, 1u, 1687u },
  { 84u, 0u, 3634u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2253u },
  { 84u, 1u, 3012u },
  { 6u, 0u, 0u },
  { 29u, 1u, 1747u },
  { 84u, 2u, 3074u },
  { 6u, 1u, 0u },
  { 29u, 2u, 1783u },
  { 84u, 0u, 3634u },
  { 6u, 2u, 0u },
  { 25u, 2u, 3115u },
  { 4u, 0u, 2253u },
  { 31u, 2u, 1807u },
  { 119u, 0u, 0u },
  { 31u, 2u, 0u },
  { 23u, 1u, 2991u },
  { 35u, 1u, 1735u },
  { 84u, 0u, 3704u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2296u },
  { 84u, 1u, 3094u },
  { 6u, 0u, 0u },
  { 29u, 1u, 1795u },
  { 84u, 2u, 3156u },
  { 6u, 1u, 0u },
  { 29u, 2u, 1830u },
  { 84u, 0u, 3704u },
  { 6u, 2u, 0u },
  { 25u, 2u, 3198u },
  { 4u, 0u, 2296u },
  { 31u, 2u, 1855u },
  { 119u, 0u, 0u },
  { 31u, 2u, 0u },
  { 23u, 1u, 3074u },
  { 35u, 1u, 1783u },
  { 84u, 0u, 3773u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2339u },
  { 84u, 1u, 3177u },
  { 6u, 0u, 0u },
  { 29u, 1u, 1843u },
  { 84u, 2u, 3239u },
  { 6u, 1u, 0u },
  { 29u, 2u, 1879u },
  { 84u, 0u, 3773u },
  { 6u, 2u, 0u },
  { 25u, 2u, 3280u },
  { 4u, 0u, 2339u },
  { 31u, 2u, 1902u },
  { 119u, 0u, 0u },
  { 31u, 2u, 0u },
  { 23u, 1u, 3156u },
  { 35u, 1u, 1830u },
  { 84u, 0u, 3843u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2383u },
  { 84u, 1u, 3260u },
  { 6u, 0u, 0u },
  { 29u, 1u, 1891u },
  { 84u, 2u, 3321u },
  { 6u, 1u, 0u },
  { 29u, 2u, 1926u },
  { 84u, 0u, 3843u },
  { 6u, 2u, 0u },
  { 25u, 2u, 3363u },
  { 4u, 0u, 2383u },
  { 31u, 2u, 1951u },
  { 119u, 0u, 0u },
  { 31u, 2u, 0u },
  { 23u, 1u, 3239u },
  { 35u, 1u, 1879u },
  { 84u, 0u, 3912u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2425u },
  { 84u, 1u, 3342u },
  { 6u, 0u, 0u },
  { 29u, 1u, 1938u },
  { 84u, 2u, 3404u },
  { 6u, 1u, 0u },
  { 29u, 2u, 1974u },
  { 84u, 0u, 3912u },
  { 6u, 2u, 0u },
  { 25u, 2u, 3445u },
  { 4u, 0u, 2425u },
  { 31u, 2u, 1998u },
  { 119u, 0u, 0u },
  { 31u, 2u, 0u },
  { 23u, 1u, 3321u },
  { 35u, 1u, 1926u },
  { 84u, 0u, 3982u },
  { 6u, 1u, 0u },
  { 29u, 0u, 2469u },
  { 84u, 1u, 3425u },
  { 6u, 0u, 0u },
  { 29u, 1u, 1986u },
  { 84u, 2u, 3487u },
  { 6u, 1u, 0u },
  { 29u, 2u, 2022u },
  { 84u, 0u, 3982u },
  { 6u, 2u, 0u },
  { 25u, 2u, 3528u },
  { 4u, 0u, 2469u },
  { 31u, 2u, 2046u },
  { 119u, 0u, 0u },
  { 31u, 2u, 0u },
  { 23u, 1u, 3404u },
  { 35u, 1u, 1974u },
  { 90u, 1u, 0u },
};

const uint32_t SONG_EVENT_COUNT = sizeof(SONG) / sizeof(SONG[0]);
