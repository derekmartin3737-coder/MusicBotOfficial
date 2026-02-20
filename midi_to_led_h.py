#!/usr/bin/env python3
import sys
from pathlib import Path
from collections import Counter
import mido

PIN_ORDER = [2, 3, 4, 5]  # red, green, blue, white (by your wiring)
COLOR_NAMES = ["RED(D2)", "GREEN(D3)", "BLUE(D4)", "WHITE(D5)"]

HEADER_TEMPLATE = """\
#pragma once
#include <Arduino.h>
#include <avr/pgmspace.h>

/*
  Auto-generated from: {src_name}

  Note -> LED mapping (MIDI note numbers):
{mapping_lines}
*/

typedef struct {{
  uint16_t dt_ms;  // delay BEFORE this event
  uint8_t  pin;    // Arduino digital pin (2,3,4,5)
  uint8_t  on;     // 1=LED ON, 0=LED OFF
}} LedEvent;

const LedEvent SONG[] PROGMEM = {{
{events}
}};

const uint32_t SONG_LEN = sizeof(SONG) / sizeof(SONG[0]);
"""

def next_version_path(out_path: Path) -> Path:
    if not out_path.exists():
        return out_path
    stem = out_path.stem
    suffix = out_path.suffix
    parent = out_path.parent
    v = 1
    while True:
        candidate = parent / f"{stem}_v{v}{suffix}"
        if not candidate.exists():
            return candidate
        v += 1

def collect_notes(mid: mido.MidiFile):
    merged = mido.merge_tracks(mid.tracks)
    counts = Counter()
    tempo = 500000  # default 120 BPM

    for msg in merged:
        if msg.type == "set_tempo":
            tempo = msg.tempo
            continue
        if msg.type == "note_on" and getattr(msg, "velocity", 0) > 0:
            counts[int(msg.note)] += 1

    return counts

def build_note_map(note_counts: Counter):
    # Choose up to 4 notes. If more, take the 4 most common (ties broken by pitch).
    notes = list(note_counts.items())
    notes.sort(key=lambda kv: (-kv[1], kv[0]))  # freq desc, then pitch asc
    chosen = [n for n, _ in notes[:len(PIN_ORDER)]]
    chosen.sort()  # deterministic: low pitch -> red, next -> green, etc.

    note_to_pin = {note: PIN_ORDER[i] for i, note in enumerate(chosen)}
    return note_to_pin, chosen, (len(note_counts) > len(PIN_ORDER))

def midi_to_led_events(mid: mido.MidiFile, note_to_pin: dict):
    merged = mido.merge_tracks(mid.tracks)
    tempo = 666667  # default 120 BPM


    events = []
    carry_dt_ms = 0  # accumulate time from skipped msgs so timing stays correct

    for msg in merged:
        dt_s = mido.tick2second(msg.time, mid.ticks_per_beat, tempo)
        carry_dt_ms += int(round(dt_s * 1000.0))

        if msg.type == "set_tempo":
            tempo = msg.tempo
            continue

        if msg.type not in ("note_on", "note_off"):
            continue

        note = int(msg.note)
        pin = note_to_pin.get(note)
        if pin is None:
            # Not mapped (e.g., song had >4 notes). We skip it but keep its time in carry_dt_ms.
            continue

        vel = int(getattr(msg, "velocity", 0))
        on = 1
        if msg.type == "note_off" or (msg.type == "note_on" and vel == 0):
            on = 0

        # Emit event using the accumulated delta-time
        events.append((carry_dt_ms, pin, on))
        carry_dt_ms = 0

    return events

def write_h(events, out_path: Path, src_name: str, mapping_lines: str):
    lines = [f"  {{ {dt}u, {pin}u, {on}u }}," for (dt, pin, on) in events]
    text = HEADER_TEMPLATE.format(
        src_name=src_name,
        mapping_lines=mapping_lines,
        events="\n".join(lines),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")

def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python midi_to_led_h.py <input.mid> [output_dir]")
        sys.exit(1)

    midi_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) == 3 else midi_path.parent

    mid = mido.MidiFile(str(midi_path))

    note_counts = collect_notes(mid)
    if not note_counts:
        print("No note_on events found. Is this MIDI empty or non-note data?")
        sys.exit(2)

    note_to_pin, chosen_notes, truncated = build_note_map(note_counts)

    mapping_lines = []
    for i, note in enumerate(chosen_notes):
        mapping_lines.append(f"  - {COLOR_NAMES[i]}  <- MIDI note {note}")
    mapping_lines = "\n".join(mapping_lines)

    events = midi_to_led_events(mid, note_to_pin)

    base_out = out_dir / f"{midi_path.stem}.h"
    out_path = next_version_path(base_out)

    write_h(events, out_path, midi_path.name, mapping_lines)

    print(f"Wrote: {out_path}")
    print(f"Mapped notes: {chosen_notes} -> pins {PIN_ORDER[:len(chosen_notes)]}")
    if truncated:
        print("WARNING: MIDI had more than 4 distinct notes; unmapped notes were skipped.")
    print(f"Events: {len(events)}")

if __name__ == "__main__":
    main()
