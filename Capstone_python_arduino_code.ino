#include <Arduino.h>
#include <avr/pgmspace.h>


// IMPORTANT: filename must match exactly (spaces included)
#include "Mary_Had_a_Little_Lamb_v3.h"


const uint8_t PINS[] = {2, 3, 4, 5};


void setup() {
  for (uint8_t i = 0; i < 4; i++) {
    pinMode(PINS[i], OUTPUT);
    digitalWrite(PINS[i], LOW);
  }
}


void playSongOnce() {
  for (uint32_t i = 0; i < SONG_LEN; i++) {
    LedEvent e;
    memcpy_P(&e, &SONG[i], sizeof(LedEvent));  // read from PROGMEM (flash)


    delay(e.dt_ms);
    digitalWrite(e.pin, e.on ? HIGH : LOW);
  }


  // make sure everyt1  WQERDhing ends OFF
  for (uint8_t i = 0; i < 4; i++) digitalWrite(PINS[i], LOW);
}


void loop() {
  playSongOnce();
  delay(2000); // pause between repeats
}
