"""Legacy export prototype kept for reference.

Use scripts/convert_midi.py for the supported workflow.
"""

import csv
from pathlib import Path

import mido
from mido import merge_tracks, tick2second

REPO_ROOT = Path(__file__).resolve().parents[2]
MIDI_PATH = REPO_ROOT / "songs" / "midi" / "basic_pitch_transcription.mid"
CSV_PATH = REPO_ROOT / "songs" / "metadata" / "legacy_events.csv"
HEADER_PATH = REPO_ROOT / "arduino" / "MusicBotOfficial" / "generated" / "legacy_events.h"

mid = mido.MidiFile(MIDI_PATH)

msgs = merge_tracks(mid.tracks)
tempo = 500000  # default us/beat (120 BPM)
pending_ms = 0.0
events = []  # (dt_ms, on, note, vel, channel)

for msg in msgs:
    pending_ms += 1000.0 * tick2second(msg.time, mid.ticks_per_beat, tempo)

    if msg.type == "set_tempo":
        tempo = msg.tempo
        continue

    if msg.type not in ("note_on", "note_off"):
        continue

    on = 1
    if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
        on = 0

    dt_ms = int(round(pending_ms))
    pending_ms = 0.0

    events.append((dt_ms, on, msg.note, msg.velocity, msg.channel))

CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
HEADER_PATH.parent.mkdir(parents=True, exist_ok=True)

with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["dt_ms", "on", "note", "vel", "ch"])
    writer.writerows(events)

with HEADER_PATH.open("w", encoding="utf-8") as handle:
    handle.write("#pragma once\n#include <Arduino.h>\n\n")
    handle.write(
        "typedef struct { uint32_t dt_ms; uint8_t on; uint8_t note; uint8_t vel; uint8_t ch; } MidiEvent;\n\n"
    )
    handle.write(f"const uint32_t SONG_LEN = {len(events)};\n")
    handle.write("const MidiEvent SONG[] PROGMEM = {\n")
    for dt_ms, on, note, vel, ch in events:
        handle.write(f"  {{{dt_ms}, {on}, {note}, {vel}, {ch}}},\n")
    handle.write("};\n")

print(f"Wrote {len(events)} events:")
print(f" - {CSV_PATH}")
print(f" - {HEADER_PATH}")
