#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

/*
  Auto-generated from: Mary Had a Little Lamb.mid

  Note -> LED mapping (MIDI note numbers):
  - RED(D2)  <- MIDI note 48
  - GREEN(D3)  <- MIDI note 50
  - BLUE(D4)  <- MIDI note 52
  - WHITE(D5)  <- MIDI note 55
*/

typedef struct {
  uint16_t dt_ms;  // delay BEFORE this event
  uint8_t  pin;    // Arduino digital pin (2,3,4,5)
  uint8_t  on;     // 1=LED ON, 0=LED OFF
} LedEvent;

const LedEvent SONG[] PROGMEM = {
  { 0u, 4u, 1u },
  { 273u, 4u, 0u },
  { 0u, 3u, 1u },
  { 273u, 3u, 0u },
  { 0u, 2u, 1u },
  { 273u, 2u, 0u },
  { 0u, 3u, 1u },
  { 273u, 3u, 0u },
  { 0u, 4u, 1u },
  { 273u, 4u, 0u },
  { 0u, 4u, 1u },
  { 273u, 4u, 0u },
  { 0u, 4u, 1u },
  { 273u, 4u, 0u },
  { 273u, 3u, 1u },
  { 273u, 3u, 0u },
  { 0u, 3u, 1u },
  { 273u, 3u, 0u },
  { 0u, 3u, 1u },
  { 273u, 3u, 0u },
  { 273u, 4u, 1u },
  { 273u, 4u, 0u },
  { 0u, 5u, 1u },
  { 273u, 5u, 0u },
  { 0u, 5u, 1u },
  { 273u, 5u, 0u },
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
  { 0u, 4u, 1u },
  { 273u, 4u, 0u },
  { 0u, 4u, 1u },
  { 273u, 4u, 0u },
  { 273u, 3u, 1u },
  { 273u, 3u, 0u },
  { 0u, 3u, 1u },
  { 273u, 3u, 0u },
  { 0u, 4u, 1u },
  { 273u, 4u, 0u },
  { 0u, 3u, 1u },
  { 273u, 3u, 0u },
  { 0u, 2u, 1u },
  { 273u, 2u, 0u },
};

const uint32_t SONG_LEN = sizeof(SONG) / sizeof(SONG[0]);
