import json
import re
from pathlib import Path

import mido
from mido import MidiFile

DEFAULT_TEMPO_US_PER_BEAT = 500000
RETRIGGER_GAP_MS = 10
MIN_DISTINCT_NOTE_GAP_MS = 35
PIN_ORDER = [2, 3, 4, 5]
COLOR_NAMES = ["RED(D2)", "GREEN(D3)", "BLUE(D4)", "WHITE(D5)"]

VERSION_RE = re.compile(r"^(?P<name>.+?)(?:_v(?P<version>\d+))?$")


def sanitize_name(name: str) -> str:
    return name.replace(" ", "_")


def parse_versioned_stem(stem: str):
    match = VERSION_RE.match(stem)
    if not match:
        return stem, 0
    version = int(match.group("version") or 0)
    return match.group("name"), version


def collect_midis(directory: Path):
    return sorted(directory.glob("*.mid"), key=lambda path: path.name.lower())


def prompt_for_song(midi_files):
    if not midi_files:
        raise FileNotFoundError("No .mid files found in the current directory.")

    print("Available songs:")
    for index, midi_path in enumerate(midi_files, start=1):
        print(f"  {index}. {midi_path.name}")

    while True:
        choice = input("\nChoose a song number: ").strip()
        if not choice.isdigit():
            print("Enter a valid song number.")
            continue

        index = int(choice)
        if 1 <= index <= len(midi_files):
            return midi_files[index - 1]

        print("Song number out of range.")


def scan_tempo_info(mid: MidiFile):
    merged = mido.merge_tracks(mid.tracks)
    tempos = []

    for msg in merged:
        if msg.type == "set_tempo":
            tempos.append(msg.tempo)

    first_tempo = tempos[0] if tempos else DEFAULT_TEMPO_US_PER_BEAT
    return {
        "first_tempo_us_per_beat": first_tempo,
        "first_bpm": mido.tempo2bpm(first_tempo),
        "tempo_change_count": len(tempos),
    }


def collect_note_counts(mid: MidiFile):
    merged = mido.merge_tracks(mid.tracks)
    counts = {}

    for msg in merged:
        if msg.type == "note_on" and int(getattr(msg, "velocity", 0)) > 0:
            note = int(msg.note)
            counts[note] = counts.get(note, 0) + 1

    return counts


def build_note_map(note_counts):
    notes = sorted(note_counts.items(), key=lambda item: (-item[1], item[0]))
    chosen_notes = [note for note, _ in notes[:len(PIN_ORDER)]]
    chosen_notes.sort()

    note_to_pin = {
        note: PIN_ORDER[index]
        for index, note in enumerate(chosen_notes)
    }
    return note_to_pin, chosen_notes, len(note_counts) > len(PIN_ORDER)


def build_timeline(mid: MidiFile, note_to_pin):
    merged = mido.merge_tracks(mid.tracks)
    tempo = DEFAULT_TEMPO_US_PER_BEAT
    current_ms = 0

    active = {}
    last_off_ms = {}
    timeline = []
    skipped_note_ons = 0
    unmatched_note_offs = 0
    forced_retriggers = 0

    for msg in merged:
        if msg.time:
            delta_seconds = mido.tick2second(msg.time, mid.ticks_per_beat, tempo)
            current_ms += int(round(delta_seconds * 1000.0))

        if msg.type == "set_tempo":
            tempo = msg.tempo
            continue

        if msg.type not in ("note_on", "note_off"):
            continue

        note = int(msg.note)
        pin = note_to_pin.get(note)
        if pin is None:
            if msg.type == "note_on" and int(getattr(msg, "velocity", 0)) > 0:
                skipped_note_ons += 1
            continue

        velocity = int(getattr(msg, "velocity", 0))
        is_note_on = msg.type == "note_on" and velocity > 0
        is_note_off = msg.type == "note_off" or (msg.type == "note_on" and velocity == 0)

        if is_note_on:
            if pin in active:
                off_time = current_ms
                on_time = max(
                    current_ms + RETRIGGER_GAP_MS,
                    last_off_ms.get(pin, current_ms) + MIN_DISTINCT_NOTE_GAP_MS,
                )
                timeline.append((off_time, pin, 0))
                timeline.append((on_time, pin, 1))
                last_off_ms[pin] = off_time
                forced_retriggers += 1
            else:
                on_time = max(
                    current_ms,
                    last_off_ms.get(pin, current_ms) + MIN_DISTINCT_NOTE_GAP_MS,
                )
                timeline.append((on_time, pin, 1))
            active[pin] = True

        elif is_note_off:
            if pin in active:
                timeline.append((current_ms, pin, 0))
                del active[pin]
                last_off_ms[pin] = current_ms
            else:
                unmatched_note_offs += 1

    if active:
        final_time_ms = current_ms + RETRIGGER_GAP_MS
        for pin in sorted(active):
            timeline.append((final_time_ms, pin, 0))
            last_off_ms[pin] = final_time_ms

    timeline.sort(key=lambda item: (item[0], item[2]))

    return timeline, {
        "forced_retriggers": forced_retriggers,
        "skipped_note_ons": skipped_note_ons,
        "unmatched_note_offs": unmatched_note_offs,
    }


def prompt_for_tempo_override(original_bpm: float):
    print(f"\nOriginal/base tempo: {original_bpm:.2f} BPM")
    print("Tempo override options:")
    print("  Press Enter to keep the original timing")
    print("  Enter a BPM number, such as 140")
    print("  Enter a multiplier like 0.85x or 1.10x")

    while True:
        raw = input("Tempo override: ").strip().lower()
        if not raw:
            return {
                "mode": "original",
                "target_bpm": original_bpm,
                "scale": 1.0,
                "label": "original timing",
            }

        if raw.endswith("x"):
            try:
                multiplier = float(raw[:-1])
            except ValueError:
                print("Invalid multiplier.")
                continue

            if multiplier <= 0:
                print("Multiplier must be greater than zero.")
                continue

            target_bpm = original_bpm * multiplier
            return {
                "mode": "multiplier",
                "target_bpm": target_bpm,
                "scale": 1.0 / multiplier,
                "label": f"{multiplier:.3f}x",
            }

        try:
            target_bpm = float(raw)
        except ValueError:
            print("Invalid BPM.")
            continue

        if target_bpm <= 0:
            print("BPM must be greater than zero.")
            continue

        return {
            "mode": "bpm",
            "target_bpm": target_bpm,
            "scale": original_bpm / target_bpm,
            "label": f"{target_bpm:.2f} BPM",
        }


def scale_timeline(timeline, scale: float):
    scaled = []
    for time_ms, pin, on in timeline:
        scaled_time = max(0, int(round(time_ms * scale)))
        scaled.append((scaled_time, pin, on))

    scaled.sort(key=lambda item: (item[0], item[2]))
    return scaled


def convert_to_delta_events(timeline):
    delta_events = []
    previous_time = 0

    for time_ms, pin, on in timeline:
        dt_ms = max(0, time_ms - previous_time)
        delta_events.append((dt_ms, pin, on))
        previous_time = time_ms

    return delta_events


def next_header_path(directory: Path, midi_path: Path):
    safe_base = sanitize_name(midi_path.stem)
    versions = []

    for header_path in directory.glob(f"{safe_base}*.h"):
        header_base_name, version = parse_versioned_stem(header_path.stem)
        if header_base_name == safe_base:
            versions.append(version)

    if not versions:
        return directory / f"{safe_base}.h", 0

    next_version = max(versions) + 1
    return directory / f"{safe_base}_v{next_version}.h", next_version


def write_outputs(selected_midi, header_path, delta_events, metadata):
    with header_path.open("w", encoding="utf-8") as handle:
        handle.write("#pragma once\n")
        handle.write("#include <Arduino.h>\n")
        handle.write("#include <avr/pgmspace.h>\n\n")
        handle.write(f"// Auto-generated from: {selected_midi.name}\n")
        handle.write(f"// Base tempo: {metadata['original_bpm']:.2f} BPM\n")
        handle.write(f"// Tempo override: {metadata['tempo_label']}\n")
        handle.write(f"// Effective output tempo: {metadata['effective_bpm']:.2f} BPM\n")
        handle.write(f"// Forced retriggers: {metadata['forced_retriggers']}\n")
        handle.write(f"// Minimum OFF gap between repeated notes: {metadata['min_distinct_note_gap_ms']} ms\n")
        handle.write(f"// Unmapped note_on events skipped: {metadata['skipped_note_ons']}\n")
        handle.write(f"// Unmatched note_off events ignored: {metadata['unmatched_note_offs']}\n\n")
        handle.write("// Note -> pin mapping used for this file:\n")
        for line in metadata["mapping_lines"]:
            handle.write(f"//   {line}\n")
        if metadata["truncated"]:
            handle.write("//   WARNING: more than 4 distinct notes were present; extra notes were skipped.\n")
        handle.write("\n")
        handle.write("typedef struct {\n")
        handle.write("  uint32_t dt_ms;  // delay BEFORE this event\n")
        handle.write("  uint8_t  pin;    // Arduino digital pin\n")
        handle.write("  uint8_t  on;     // 1=ON, 0=OFF\n")
        handle.write("} LedEvent;\n\n")
        handle.write("const LedEvent SONG[] PROGMEM = {\n")
        for dt_ms, pin, on in delta_events:
            handle.write(f"  {{ {dt_ms}u, {pin}u, {on}u }},\n")
        handle.write("};\n\n")
        handle.write("const uint32_t SONG_LEN = sizeof(SONG) / sizeof(SONG[0]);\n")

    json_path = header_path.with_suffix(".json")
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "source_midi": selected_midi.name,
                "output_header": header_path.name,
                "events": [
                    {"dt_ms": dt_ms, "pin": pin, "on": on}
                    for dt_ms, pin, on in delta_events
                ],
                "metadata": metadata,
            },
            handle,
            indent=2,
        )

    return json_path


def main():
    workdir = Path.cwd()
    midi_files = collect_midis(workdir)
    selected_midi = prompt_for_song(midi_files)

    mid = MidiFile(str(selected_midi))
    tempo_info = scan_tempo_info(mid)
    note_counts = collect_note_counts(mid)
    if not note_counts:
        raise ValueError("No note_on events were found in the selected MIDI file.")

    note_to_pin, chosen_notes, truncated = build_note_map(note_counts)
    mapping_lines = [
        f"{COLOR_NAMES[index]} <- MIDI note {note}"
        for index, note in enumerate(chosen_notes)
    ]

    print(f"\nSelected file: {selected_midi.name}")
    print(f"Type: {mid.type}")
    print(f"Ticks per beat: {mid.ticks_per_beat}")
    print(f"Number of tracks: {len(mid.tracks)}")
    print(f"Tempo events found: {tempo_info['tempo_change_count']}")
    print("Mapped notes for prototype output:")
    for line in mapping_lines:
        print(f"  {line}")
    if truncated:
        print("  WARNING: more than 4 distinct notes exist; only the 4 most common notes will be exported.")

    tempo_override = prompt_for_tempo_override(tempo_info["first_bpm"])
    timeline, stats = build_timeline(mid, note_to_pin)
    scaled_timeline = scale_timeline(timeline, tempo_override["scale"])
    delta_events = convert_to_delta_events(scaled_timeline)

    header_path, output_version = next_header_path(workdir, selected_midi)
    output_version_label = "base" if output_version == 0 else f"v{output_version}"

    metadata = {
        "output_version_label": output_version_label,
        "original_bpm": tempo_info["first_bpm"],
        "tempo_label": tempo_override["label"],
        "effective_bpm": tempo_override["target_bpm"],
        "forced_retriggers": stats["forced_retriggers"],
        "min_distinct_note_gap_ms": MIN_DISTINCT_NOTE_GAP_MS,
        "skipped_note_ons": stats["skipped_note_ons"],
        "unmatched_note_offs": stats["unmatched_note_offs"],
        "mapping_lines": mapping_lines,
        "truncated": truncated,
    }

    json_path = write_outputs(selected_midi, header_path, delta_events, metadata)

    print("\nConversion complete.")
    print(f"Input song: {selected_midi.name}")
    print(f"Output header: {header_path.name}")
    print(f"Output header version: {output_version_label}")
    print(f"Output json: {json_path.name}")
    print(f"Base tempo: {tempo_info['first_bpm']:.2f} BPM")
    print(f"Effective output tempo: {tempo_override['target_bpm']:.2f} BPM")
    print(f"Generated events: {len(delta_events)}")
    print(f"Forced retriggers: {stats['forced_retriggers']}")
    print(f"Unmapped note_on events skipped: {stats['skipped_note_ons']}")
    print(f"Unmatched note_off events ignored: {stats['unmatched_note_offs']}")


if __name__ == "__main__":
    main()
