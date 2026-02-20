import mido
from mido import merge_tracks, tick2second
import csv
from pathlib import Path

# Load a MIDI file
mid = mido.MidiFile('MusicBotOfficial/basic_pitch_transcription.mid')

# --- Arduino-friendly export (events.h + events.csv) ---
midi_path = Path('MusicBotOfficial/basic_pitch_transcription.mid')
mid = mido.MidiFile(midi_path)

# Merge all tracks so timing is correct across the whole file
msgs = merge_tracks(mid.tracks)

tempo = 500000  # default us/beat (120 BPM)
pending_ms = 0.0
events = []  # (dt_ms, on, note, vel, channel)

for msg in msgs:
    # Convert this message's delta-time (ticks) into ms using current tempo
    pending_ms += 1000.0 * tick2second(msg.time, mid.ticks_per_beat, tempo)

    if msg.type == 'set_tempo':
        tempo = msg.tempo
        continue

    if msg.type not in ('note_on', 'note_off'):
        continue

    on = 1
    if msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
        on = 0

    dt_ms = int(round(pending_ms))
    pending_ms = 0.0

    events.append((dt_ms, on, msg.note, msg.velocity, msg.channel))

out_dir = midi_path.parent
csv_path = out_dir / 'events.csv'
h_path   = out_dir / 'events.h'

# 1) CSV (easy to inspect)
with open(csv_path, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['dt_ms', 'on', 'note', 'vel', 'ch'])
    w.writerows(events)

# 2) C header (best “just include it” Arduino workflow)
with open(h_path, 'w') as f:
    f.write('#pragma once\n#include <Arduino.h>\n\n')
    f.write('typedef struct { uint32_t dt_ms; uint8_t on; uint8_t note; uint8_t vel; uint8_t ch; } MidiEvent;\n\n')
    f.write(f'const uint32_t SONG_LEN = {len(events)};\n')
    f.write('const MidiEvent SONG[] PROGMEM = {\n')
    for dt_ms, on, note, vel, ch in events:
        f.write(f'  {{{dt_ms}, {on}, {note}, {vel}, {ch}}},\n')
    f.write('};\n')

print(f"Wrote {len(events)} events:")
print(f" - {csv_path}")
print(f" - {h_path}")
