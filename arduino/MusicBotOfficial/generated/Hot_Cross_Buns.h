#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

// Auto-generated from: Hot Cross Buns.mid
// Base tempo: 110.00 BPM
// Tempo override: original timing
// Effective output tempo: 110.00 BPM
// Forced retriggers: 1
// Minimum OFF gap between repeated notes: 35 ms
// Unmapped note_on events skipped: 0
// Unmatched note_off events ignored: 1

// Note -> pin mapping used for this file:
//   RED(D2) <- MIDI note 48
//   GREEN(D3) <- MIDI note 50
//   BLUE(D4) <- MIDI note 52

typedef struct {
  uint32_t dt_ms;  // delay BEFORE this event
  uint8_t  pin;    // Arduino digital pin
  uint8_t  on;     // 1=ON, 0=OFF
} LedEvent;

const LedEvent SONG[] PROGMEM = {
  { 35u, 4u, 1u },
  { 510u, 4u, 0u },
  { 35u, 3u, 1u },
  { 510u, 3u, 0u },
  { 0u, 2u, 0u },
  { 35u, 2u, 1u },
  { 0u, 2u, 1u },
  { 510u, 2u, 0u },
  { 545u, 4u, 1u },
  { 545u, 4u, 0u },
  { 0u, 3u, 1u },
  { 545u, 3u, 0u },
  { 0u, 2u, 1u },
  { 545u, 2u, 0u },
  { 545u, 2u, 1u },
  { 136u, 2u, 0u },
  { 136u, 2u, 1u },
  { 136u, 2u, 0u },
  { 136u, 2u, 1u },
  { 136u, 2u, 0u },
  { 136u, 2u, 1u },
  { 136u, 2u, 0u },
  { 136u, 3u, 1u },
  { 136u, 3u, 0u },
  { 136u, 3u, 1u },
  { 136u, 3u, 0u },
  { 136u, 3u, 1u },
  { 136u, 3u, 0u },
  { 136u, 3u, 1u },
  { 136u, 3u, 0u },
  { 136u, 4u, 1u },
  { 545u, 4u, 0u },
  { 0u, 3u, 1u },
  { 545u, 3u, 0u },
  { 0u, 2u, 1u },
  { 545u, 2u, 0u },
};

const uint32_t SONG_LEN = sizeof(SONG) / sizeof(SONG[0]);
