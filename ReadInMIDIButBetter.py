import json
import mido
from mido import MidiFile

# ----------------------------
# Config: your 61-key mapping
# ----------------------------
NUM_KEYS = 61

# Common 61-key keyboard range is C2..C7 = MIDI 36..96 (61 keys).
# If your lowest physical key is different, change ONLY this number.
LOWEST_MIDI_NOTE = 36
HIGHEST_MIDI_NOTE = LOWEST_MIDI_NOTE + (NUM_KEYS - 1)

MIDI_PATH = "MusicBotOfficial/basic_pitch_transcription.mid"

# ----------------------------
# Load MIDI
# ----------------------------
mid = MidiFile(MIDI_PATH)

print(f"Type: {mid.type}")
print(f"Ticks per beat: {mid.ticks_per_beat}")
print(f"Number of tracks: {len(mid.tracks)}")
print(f"61-key range: MIDI {LOWEST_MIDI_NOTE}..{HIGHEST_MIDI_NOTE} (keys 0..{NUM_KEYS-1})")

# ----------------------------
# Build actuator event list (tempo-aware)
# ----------------------------
merged = mido.merge_tracks(mid.tracks)

tempo = 500000  # default: 120 BPM (microseconds per beat) if no set_tempo events exist
t_sec = 0.0

# Track active notes to compute durations:
# key: (channel, midi_note) -> list of (start_time_sec, velocity)
active = {}

events = []  # each: {t_ms, key, vel, dur_ms, channel, midi_note}

for msg in merged:
    # Convert delta ticks -> delta seconds using current tempo
    if msg.time:
        t_sec += mido.tick2second(msg.time, mid.ticks_per_beat, tempo)

    # Tempo change affects conversion going forward
    if msg.type == "set_tempo":
        tempo = msg.tempo
        continue

    # MIDI convention: note_on with velocity 0 == note_off
    is_note_on = (msg.type == "note_on" and msg.velocity > 0)
    is_note_off = (msg.type == "note_off") or (msg.type == "note_on" and msg.velocity == 0)

    if is_note_on:
        note = int(msg.note)

        # Ignore notes outside your physical 61-key range
        if note < LOWEST_MIDI_NOTE or note > HIGHEST_MIDI_NOTE:
            continue

        key = (msg.channel, note)
        active.setdefault(key, []).append((t_sec, int(msg.velocity)))

    elif is_note_off:
        note = int(msg.note)

        # If note is outside range, ignore (we never tracked its note_on)
        if note < LOWEST_MIDI_NOTE or note > HIGHEST_MIDI_NOTE:
            continue

        key = (msg.channel, note)

        # Unmatched note_off can happen in messy files; ignore safely
        if key not in active or not active[key]:
            continue

        start_t, start_vel = active[key].pop()
        dur_sec = max(0.0, t_sec - start_t)

        key_index = note - LOWEST_MIDI_NOTE  # 0..60

        events.append({
            "t_ms": int(round(start_t * 1000)),
            "key": int(key_index),          # 0..60 for your actuators
            "vel": int(start_vel),          # 1..127
            "dur_ms": int(round(dur_sec * 1000)),
            "channel": int(msg.channel),
            "midi_note": int(note),         # keep for debugging/verification
        })

# Ensure chronological order
events.sort(key=lambda e: e["t_ms"])

print(f"\nBuilt {len(events)} actuator note events.")
print("First 10 events:")
for e in events[:10]:
    print(e)

with open("actuator_events.json", "w") as f:
    json.dump(events, f, indent=2)

print("\nWrote actuator_events.json")
