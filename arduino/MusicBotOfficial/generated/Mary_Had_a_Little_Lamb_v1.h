#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: Mary Had a Little Lamb.mid
// Base tempo: 55.00 BPM
// Tempo override: original timing
// Effective output tempo: 55.00 BPM
// Forced retriggers: 0
// Minimum OFF gap between repeated notes: 35 ms
// Unmapped note_on events skipped: 0
// Unmatched note_off events ignored: 0

// Note -> pin mapping used for this file:
//   RED(D2) <- MIDI note 48
//   GREEN(D3) <- MIDI note 50
//   BLUE(D4) <- MIDI note 52
//   WHITE(D5) <- MIDI note 55

typedef struct {
  uint32_t dt_ms;  // delay BEFORE this event
  uint8_t  pin;    // Arduino digital pin
  uint8_t  on;     // 1=ON, 0=OFF
} LedEvent;

const LedEvent SONG[] PROGMEM = {
  { 35u, 4u, 1u },
  { 238u, 4u, 0u },
  { 35u, 3u, 1u },
  { 238u, 3u, 0u },
  { 35u, 2u, 1u },
  { 238u, 2u, 0u },
  { 0u, 3u, 1u },
  { 273u, 3u, 0u },
  { 0u, 4u, 1u },
  { 273u, 4u, 0u },
  { 35u, 4u, 1u },
  { 238u, 4u, 0u },
  { 35u, 4u, 1u },
  { 238u, 4u, 0u },
  { 273u, 3u, 1u },
  { 273u, 3u, 0u },
  { 35u, 3u, 1u },
  { 238u, 3u, 0u },
  { 35u, 3u, 1u },
  { 238u, 3u, 0u },
  { 273u, 4u, 1u },
  { 273u, 4u, 0u },
  { 35u, 5u, 1u },
  { 238u, 5u, 0u },
  { 35u, 5u, 1u },
  { 238u, 5u, 0u },
  { 273u, 4u, 1u },
  { 273u, 4u, 0u },
  { 0u, 3u, 1u },
  { 273u, 3u, 0u },
  { 0u, 2u, 1u },
  { 273u, 2u, 0u },
  { 0u, 3u, 1u },
  { 273u, 3u, 0u },
  { 0u, 4u, 1u },
  { 273u, 4u, 0u },
  { 35u, 4u, 1u },
  { 238u, 4u, 0u },
  { 35u, 4u, 1u },
  { 238u, 4u, 0u },
  { 273u, 3u, 1u },
  { 273u, 3u, 0u },
  { 35u, 3u, 1u },
  { 238u, 3u, 0u },
  { 0u, 4u, 1u },
  { 273u, 4u, 0u },
  { 0u, 3u, 1u },
  { 273u, 3u, 0u },
  { 0u, 2u, 1u },
  { 273u, 2u, 0u },
};

const uint32_t SONG_LEN = sizeof(SONG) / sizeof(SONG[0]);
