import mido

# Load a MIDI file
mid = mido.MidiFile('basic_pitch_transcription.mid')

# Basic file info
print(f"Type: {mid.type}")
print(f"Ticks per beat: {mid.ticks_per_beat}")
print(f"Number of tracks: {len(mid.tracks)}")

# Iterate through tracks and messages
for i, track in enumerate(mid.tracks):
    print(f"\nTrack {i}: {track.name}")
    for msg in track:
        print(msg)