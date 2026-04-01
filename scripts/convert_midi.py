import argparse
import json
import re
import shutil
import time
from collections import defaultdict
from pathlib import Path

import mido
from mido import MidiFile

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

DEFAULT_TEMPO_US_PER_BEAT = 500000
ACTIVE_HEADER_NAME = "current_song.h"
ACTIVE_METADATA_NAME = "current_song.json"

VERSION_RE = re.compile(r"^(?P<name>.+?)(?:_v(?P<version>\d+))?$")
NOTE_TOKEN_RE = re.compile(r"^\s*([A-Ga-g])([#b]?)(-?\d+)\s*$")
NUMERIC_RANGE_RE = re.compile(r"^\s*(-?\d+)\s*-\s*(-?\d+)\s*$")
NOTE_RANGE_RE = re.compile(r"^\s*([A-Ga-g][#b]?-?\d+)\s*-\s*([A-Ga-g][#b]?-?\d+)\s*$")

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "piano_config.json"
DEPLOYMENT_CONFIG_PATH = REPO_ROOT / "config" / "deployment_paths.json"
MIDI_DIR = REPO_ROOT / "songs" / "midi"
METADATA_DIR = REPO_ROOT / "songs" / "metadata"
ARDUINO_PROJECT_DIR = REPO_ROOT / "arduino" / "MusicBotOfficial"
HEADER_DIR = ARDUINO_PROJECT_DIR / "generated"
REPO_RUNTIME_SKETCH_PATH = ARDUINO_PROJECT_DIR / "MusicBotOfficial.ino"
DOWNLOADS_DIR = Path.home() / "Downloads"
STREAM_MANIFEST_PATH = METADATA_DIR / "last_streamed_song.json"


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def midi_note_name(note: int):
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (note // 12) - 1
    return f"{names[note % 12]}{octave}"


def parse_note_token(token: str):
    match = NOTE_TOKEN_RE.match(token)
    if not match:
        raise ValueError(
            "Invalid note format. Use note names like C4, F#3, Bb2, or MIDI numbers in a range like 60-71."
        )

    note_name = match.group(1).upper()
    accidental = match.group(2)
    octave = int(match.group(3))

    semitone_lookup = {
        "C": 0,
        "D": 2,
        "E": 4,
        "F": 5,
        "G": 7,
        "A": 9,
        "B": 11,
    }
    semitone = semitone_lookup[note_name]
    if accidental == "#":
        semitone += 1
    elif accidental == "b":
        semitone -= 1

    midi_note = (octave + 1) * 12 + semitone
    if not 0 <= midi_note <= 127:
        raise ValueError("MIDI note values must stay between 0 and 127.")
    return midi_note


def parse_inclusive_note_range(raw: str):
    numeric_match = NUMERIC_RANGE_RE.match(raw)
    if numeric_match:
        bottom_note = int(numeric_match.group(1))
        top_note = int(numeric_match.group(2))
    else:
        note_match = NOTE_RANGE_RE.match(raw)
        if not note_match:
            raise ValueError(
                "Use an inclusive range like C4-B4 or 60-71."
            )
        bottom_note = parse_note_token(note_match.group(1))
        top_note = parse_note_token(note_match.group(2))

    if not (0 <= bottom_note <= 127 and 0 <= top_note <= 127):
        raise ValueError("Playable range notes must stay between 0 and 127.")
    if bottom_note > top_note:
        raise ValueError("The bottom note must be lower than or equal to the top note.")
    return bottom_note, top_note


def format_note_range(bottom_note: int, top_note: int):
    return f"{midi_note_name(bottom_note)} to {midi_note_name(top_note)}"


def format_playable_count(playable_count: int, total_count: int):
    percentage = 0.0 if total_count == 0 else (playable_count / total_count) * 100.0
    return f"{playable_count} of {total_count} note events playable ({percentage:.1f}%)"


def sanitize_name(name: str) -> str:
    return name.replace(" ", "_")


def parse_versioned_stem(stem: str):
    match = VERSION_RE.match(stem)
    if not match:
        return stem, 0
    version = int(match.group("version") or 0)
    return match.group("name"), version


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_deployment_config():
    if not DEPLOYMENT_CONFIG_PATH.exists():
        return {
            "arduino_ide_sync": {"enabled": False},
            "serial_runtime": {
                "enabled": False,
                "baud_rate": 115200,
                "preferred_port": "",
                "auto_detect": True,
                "startup_wait_ms": 2500,
            },
        }

    with DEPLOYMENT_CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def collect_download_midis(directory: Path):
    midi_paths = list(directory.glob("*.mid")) + list(directory.glob("*.midi"))
    return sorted(midi_paths, key=lambda path: path.stat().st_mtime, reverse=True)


def next_library_midi_path(source_path: Path):
    base_path = MIDI_DIR / source_path.name
    if not base_path.exists():
        return base_path

    stem = source_path.stem
    suffix = source_path.suffix
    version = 1
    while True:
        candidate = MIDI_DIR / f"{stem}_imported_v{version}{suffix}"
        if not candidate.exists():
            return candidate
        version += 1


def import_midi_to_library(source_path: Path):
    source_path = source_path.resolve()
    if source_path.parent == MIDI_DIR.resolve():
        return source_path, False

    MIDI_DIR.mkdir(parents=True, exist_ok=True)
    target_path = next_library_midi_path(source_path)
    shutil.copy2(source_path, target_path)
    return target_path, True


def choose_input_midi(args):
    if args.song:
        chosen_path = Path(args.song).expanduser()
        if not chosen_path.exists():
            raise FileNotFoundError(f"Specified MIDI path does not exist: {chosen_path}")
        return chosen_path

    if args.project_song:
        chosen_path = MIDI_DIR / args.project_song
        if not chosen_path.exists():
            raise FileNotFoundError(f"Project MIDI not found: {chosen_path}")
        return chosen_path

    download_midis = collect_download_midis(DOWNLOADS_DIR)
    if download_midis:
        newest_download = download_midis[0]
        print(f"Newest downloaded MIDI: {newest_download.name}")
        print(f"Location: {newest_download}")
        choice = input(
            "Press Enter to use it, type 'project' to choose from the project library, "
            "or enter a full path to another MIDI: "
        ).strip()
        if not choice:
            return newest_download
        if choice.lower() == "project":
            return prompt_for_song(collect_midis(MIDI_DIR))

        manual_path = Path(choice).expanduser()
        if not manual_path.exists():
            raise FileNotFoundError(f"Specified MIDI path does not exist: {manual_path}")
        return manual_path

    print(f"No downloaded MIDI files found in {DOWNLOADS_DIR}.")
    return prompt_for_song(collect_midis(MIDI_DIR))


def collect_midis(directory: Path):
    return sorted(directory.glob("*.mid"), key=lambda path: path.name.lower())


def prompt_for_song(midi_files):
    if not midi_files:
        raise FileNotFoundError(f"No .mid files found in {MIDI_DIR}.")

    print(f"Available songs in {MIDI_DIR}:")
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


def scale_intervals(note_intervals, scale: float):
    scaled = []
    for interval in note_intervals:
        start_ms = max(0, int(round(interval["start_ms"] * scale)))
        end_ms = max(start_ms + 1, int(round(interval["end_ms"] * scale)))
        scaled.append(
            {
                **interval,
                "start_ms": start_ms,
                "end_ms": end_ms,
            }
        )
    return scaled


def extract_note_intervals(mid: MidiFile):
    merged = mido.merge_tracks(mid.tracks)
    tempo = DEFAULT_TEMPO_US_PER_BEAT
    current_ms = 0

    active_notes = defaultdict(list)
    note_intervals = []
    unmatched_note_offs = 0
    percussion_events_skipped = 0

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
        channel = int(getattr(msg, "channel", -1))
        if channel == 9:
            percussion_events_skipped += 1
            continue

        velocity = int(getattr(msg, "velocity", 0))
        is_note_on = msg.type == "note_on" and velocity > 0
        is_note_off = msg.type == "note_off" or (msg.type == "note_on" and velocity == 0)
        note_key = (channel, note)

        if is_note_on:
            active_notes[note_key].append(
                {"start_ms": current_ms, "velocity": velocity, "source_channel": channel}
            )
            continue

        if is_note_off:
            if active_notes[note_key]:
                pending_note = active_notes[note_key].pop(0)
                note_intervals.append(
                    {
                        "note": note,
                        "source_note": note,
                        "velocity": pending_note["velocity"],
                        "start_ms": pending_note["start_ms"],
                        "end_ms": max(current_ms, pending_note["start_ms"] + 1),
                        "source_channel": pending_note["source_channel"],
                    }
                )
            else:
                unmatched_note_offs += 1

    dangling_note_ons = 0
    for (_, note), pending_notes in active_notes.items():
        for pending_note in pending_notes:
            note_intervals.append(
                {
                    "note": note,
                    "source_note": note,
                    "velocity": pending_note["velocity"],
                    "start_ms": pending_note["start_ms"],
                    "end_ms": max(current_ms, pending_note["start_ms"] + 1),
                    "source_channel": pending_note["source_channel"],
                }
            )
            dangling_note_ons += 1

    note_intervals.sort(key=lambda item: (item["start_ms"], item["note"], item["end_ms"]))
    return note_intervals, {
        "unmatched_note_offs": unmatched_note_offs,
        "dangling_note_ons_closed": dangling_note_ons,
        "percussion_events_skipped": percussion_events_skipped,
    }


def get_mapping_channel_order(mapping_config):
    channel_sequence = mapping_config.get("channel_sequence")
    if channel_sequence:
        return [int(channel) for channel in channel_sequence]

    mode = mapping_config["mode"]
    if mode == "collapse_all_notes_to_single_channel":
        return [int(mapping_config["single_channel"])]

    if mode == "explicit_note_map":
        ordered_pairs = sorted(
            ((int(note), int(channel)) for note, channel in mapping_config.get("note_to_channel", {}).items()),
            key=lambda item: item[0],
        )
        seen_channels = set()
        channel_order = []
        for _, channel in ordered_pairs:
            if channel not in seen_channels:
                channel_order.append(channel)
                seen_channels.add(channel)
        return channel_order

    raise ValueError(f"Unsupported mapping mode: {mode}")


def get_mapping_note_numbers(mapping_config):
    if mapping_config["mode"] == "explicit_note_map":
        return sorted(int(note) for note in mapping_config.get("note_to_channel", {}))
    return []


def summarize_playable_layout(mapping_config):
    if mapping_config["mode"] == "collapse_all_notes_to_single_channel":
        channel = int(mapping_config["single_channel"])
        return {
            "label": f"All notes collapse to PCA9685 channel {channel}",
            "bottom_note": None,
            "top_note": None,
            "note_count": None,
            "is_contiguous": True,
        }

    note_numbers = get_mapping_note_numbers(mapping_config)
    if not note_numbers:
        return {
            "label": "No mapped notes",
            "bottom_note": None,
            "top_note": None,
            "note_count": 0,
            "is_contiguous": False,
        }

    bottom_note = note_numbers[0]
    top_note = note_numbers[-1]
    is_contiguous = note_numbers == list(range(bottom_note, top_note + 1))
    if is_contiguous:
        label = (
            f"{len(note_numbers)} mapped notes from {midi_note_name(bottom_note)} "
            f"to {midi_note_name(top_note)}"
        )
    else:
        label = (
            f"{len(note_numbers)} mapped notes from {midi_note_name(bottom_note)} "
            f"to {midi_note_name(top_note)} (non-contiguous)"
        )

    return {
        "label": label,
        "bottom_note": bottom_note,
        "top_note": top_note,
        "note_count": len(note_numbers),
        "is_contiguous": is_contiguous,
    }


def build_contiguous_mapping(mapping_config, bottom_note: int, top_note: int):
    channel_order = get_mapping_channel_order(mapping_config)
    note_count = top_note - bottom_note + 1
    if note_count != len(channel_order):
        raise ValueError(
            f"That range covers {note_count} notes, but the current hardware mapping exposes {len(channel_order)} channels."
        )

    note_to_channel = {}
    note_labels = {}
    for offset, note in enumerate(range(bottom_note, top_note + 1)):
        channel = channel_order[offset]
        note_to_channel[str(note)] = channel
        note_labels[str(note)] = midi_note_name(note)

    return {
        "mode": "explicit_note_map",
        "note_to_channel": note_to_channel,
        "note_labels": note_labels,
        "channel_labels": dict(mapping_config.get("channel_labels", {})),
        "channel_sequence": channel_order,
    }


def prompt_for_playable_range(mapping_config):
    channel_order = get_mapping_channel_order(mapping_config)
    if len(channel_order) <= 1:
        return mapping_config, summarize_playable_layout(mapping_config), False

    layout_summary = summarize_playable_layout(mapping_config)
    print("\nKeyboard range setup:")
    print(f"Saved playable layout: {layout_summary['label']}")
    print("Press Enter to keep the saved mapping.")
    print(
        "Or enter an inclusive contiguous range like C4-B4 or 60-71 if your solenoids cover every note in that span."
    )
    print(
        f"That range must contain exactly {len(channel_order)} notes because {len(channel_order)} channels are currently active."
    )

    while True:
        raw = input("Playable range override: ").strip()
        if not raw:
            return mapping_config, layout_summary, False

        try:
            bottom_note, top_note = parse_inclusive_note_range(raw)
            override_mapping = build_contiguous_mapping(mapping_config, bottom_note, top_note)
        except ValueError as error:
            print(error)
            continue

        override_summary = summarize_playable_layout(override_mapping)
        print(f"Using override layout: {override_summary['label']}")
        return override_mapping, override_summary, True


def analyze_note_range(note_intervals):
    if not note_intervals:
        return {
            "bottom_note": None,
            "top_note": None,
            "range_label": "No pitched note events found",
            "unique_note_count": 0,
        }

    note_numbers = sorted(interval["note"] for interval in note_intervals)
    bottom_note = note_numbers[0]
    top_note = note_numbers[-1]
    return {
        "bottom_note": bottom_note,
        "top_note": top_note,
        "range_label": format_note_range(bottom_note, top_note),
        "unique_note_count": len(set(note_numbers)),
    }


def count_playable_intervals(note_intervals, mapping_config, semitone_shift=0):
    playable_count = 0
    for interval in note_intervals:
        shifted_note = interval["note"] + semitone_shift
        if not 0 <= shifted_note <= 127:
            continue
        if map_note_to_channel(shifted_note, mapping_config) is not None:
            playable_count += 1
    return playable_count


def find_best_octave_shift(note_intervals, mapping_config):
    if mapping_config["mode"] == "collapse_all_notes_to_single_channel":
        return 0, len(note_intervals)

    supported_notes = get_mapping_note_numbers(mapping_config)
    if not supported_notes or not note_intervals:
        return 0, 0

    source_notes = [interval["note"] for interval in note_intervals]
    min_octave_shift = ((supported_notes[0] - max(source_notes)) // 12) - 1
    max_octave_shift = ((supported_notes[-1] - min(source_notes)) // 12) + 1

    best_shift = 0
    best_count = -1
    for octave_shift in range(min_octave_shift, max_octave_shift + 1):
        semitone_shift = octave_shift * 12
        playable_count = count_playable_intervals(note_intervals, mapping_config, semitone_shift)
        if playable_count > best_count or (
            playable_count == best_count and abs(semitone_shift) < abs(best_shift)
        ):
            best_shift = semitone_shift
            best_count = playable_count

    return best_shift, best_count


def transpose_note_intervals(note_intervals, semitone_shift):
    if semitone_shift == 0:
        return [dict(interval) for interval in note_intervals]

    transposed = []
    for interval in note_intervals:
        transposed.append(
            {
                **interval,
                "source_note": interval.get("source_note", interval["note"]),
                "note": interval["note"] + semitone_shift,
            }
        )
    return transposed


def prompt_for_fit_mode(note_intervals, mapping_config):
    range_info = analyze_note_range(note_intervals)
    total_note_count = len(note_intervals)
    strict_playable_count = count_playable_intervals(note_intervals, mapping_config, 0)
    best_shift, transposed_playable_count = find_best_octave_shift(note_intervals, mapping_config)
    layout_summary = summarize_playable_layout(mapping_config)

    print("\nMIDI pitch scan:")
    print(f"Detected MIDI note range: {range_info['range_label']}")
    print(f"Active playable layout: {layout_summary['label']}")
    print(
        f"Strict: {format_playable_count(strict_playable_count, total_note_count)}"
    )
    print("  Keeps the original pitches and skips anything outside your playable layout.")
    print(
        f"Transpose by octave: {format_playable_count(transposed_playable_count, total_note_count)}"
    )
    if best_shift == 0:
        print("  Keeps the song where it is because that already fits best.")
    else:
        direction = "up" if best_shift > 0 else "down"
        print(
            f"  Shifts the whole song {direction} {abs(best_shift) // 12} octave(s) to fit more notes, then skips the rest."
        )
    print("Cancel: stop here without converting or sending anything.")

    recommended_mode = "transpose" if transposed_playable_count > strict_playable_count else "strict"
    while True:
        choice = input(f"Choose strict, transpose, or cancel [{recommended_mode}]: ").strip().lower()
        if not choice:
            choice = recommended_mode
        if choice not in {"strict", "transpose", "cancel"}:
            print("Enter strict, transpose, or cancel.")
            continue
        if choice == "strict" and strict_playable_count == 0:
            print("Strict would play 0 notes with the current layout. Choose transpose, another range, or cancel.")
            continue
        if choice == "transpose" and transposed_playable_count == 0:
            print("Transpose would still play 0 notes with the current layout. Choose another range or cancel.")
            continue
        break

    return {
        "mode": choice,
        "source_range": range_info,
        "layout_summary": layout_summary,
        "strict_playable_count": strict_playable_count,
        "strict_summary": format_playable_count(strict_playable_count, total_note_count),
        "transpose_playable_count": transposed_playable_count,
        "transpose_summary": format_playable_count(transposed_playable_count, total_note_count),
        "best_octave_shift": best_shift,
    }


def describe_mapping(mapping_config):
    mode = mapping_config["mode"]
    channel_labels = mapping_config.get("channel_labels", {})
    note_labels = mapping_config.get("note_labels", {})

    if mode == "collapse_all_notes_to_single_channel":
        channel = int(mapping_config["single_channel"])
        label = channel_labels.get(str(channel), f"Channel {channel}")
        return [
            "Single-solenoid test mode",
            f"All MIDI notes collapse to PCA9685 channel {channel} ({label})",
            "This is useful for force and timing tuning with one physical solenoid.",
        ]

    note_map = mapping_config.get("note_to_channel", {})
    lines = ["Explicit note-to-channel mode"]
    for note, channel in sorted(note_map.items(), key=lambda item: int(item[0])):
        label = channel_labels.get(str(channel), f"Channel {channel}")
        note_label = note_labels.get(str(note), midi_note_name(int(note)))
        lines.append(
            f"MIDI note {note} ({note_label}) -> PCA9685 channel {channel} ({label})"
        )
    return lines


def map_note_to_channel(note, mapping_config):
    mode = mapping_config["mode"]

    if mode == "collapse_all_notes_to_single_channel":
        return int(mapping_config["single_channel"])

    if mode == "explicit_note_map":
        note_map = mapping_config.get("note_to_channel", {})
        if str(note) in note_map:
            return int(note_map[str(note)])
        return None

    raise ValueError(f"Unsupported mapping mode: {mode}")


def resolve_channel_actuation(channel, config):
    resolved = dict(config["actuation"])
    channel_overrides = config["actuation"].get("channel_overrides", {})
    resolved.update(channel_overrides.get(str(channel), {}))
    resolved.pop("channel_overrides", None)
    return resolved


def schedule_notes(note_intervals, config):
    mapping_config = config["mapping"]

    notes_by_channel = defaultdict(list)
    unmapped_notes = 0

    for interval in note_intervals:
        channel = map_note_to_channel(interval["note"], mapping_config)
        if channel is None:
            unmapped_notes += 1
            continue

        notes_by_channel[channel].append({**interval, "channel": channel})

    scheduled_notes = []
    forced_retriggers = 0
    delayed_notes = 0

    for channel in sorted(notes_by_channel):
        channel_actuation = resolve_channel_actuation(channel, config)
        release_delay_ms = int(channel_actuation["release_delay_ms"])
        minimum_rearm_gap_ms = int(channel_actuation["minimum_rearm_gap_ms"])
        retrigger_gap_ms = int(channel_actuation["retrigger_gap_ms"])
        active_note = None
        last_off_ms = -1_000_000

        for interval in sorted(
            notes_by_channel[channel],
            key=lambda item: (item["start_ms"], item["note"], item["end_ms"]),
        ):
            if active_note and interval["start_ms"] >= active_note["end_ms"]:
                scheduled_notes.append(active_note)
                last_off_ms = active_note["end_ms"] + release_delay_ms
                active_note = None

            gap_ms = minimum_rearm_gap_ms
            if active_note and interval["start_ms"] < active_note["end_ms"]:
                active_note["end_ms"] = max(active_note["start_ms"] + 1, interval["start_ms"])
                scheduled_notes.append(active_note)
                last_off_ms = active_note["end_ms"] + release_delay_ms
                active_note = None
                gap_ms = retrigger_gap_ms
                forced_retriggers += 1

            start_ms = max(interval["start_ms"], last_off_ms + gap_ms)
            if start_ms > interval["start_ms"]:
                delayed_notes += 1

            original_duration_ms = max(1, interval["end_ms"] - interval["start_ms"])
            end_ms = max(start_ms + 1, start_ms + original_duration_ms)

            active_note = {
                **interval,
                "channel": channel,
                "original_start_ms": interval["start_ms"],
                "original_end_ms": interval["end_ms"],
                "original_duration_ms": original_duration_ms,
                "start_ms": start_ms,
                "end_ms": end_ms,
            }

        if active_note:
            scheduled_notes.append(active_note)

    scheduled_notes.sort(key=lambda item: (item["start_ms"], item["channel"], item["note"]))
    return scheduled_notes, {
        "forced_retriggers": forced_retriggers,
        "delayed_notes": delayed_notes,
        "unmapped_notes": unmapped_notes,
        "channels_used": sorted(notes_by_channel),
    }


def velocity_to_strike_pwm(velocity, actuation_config):
    minimum_pwm = int(actuation_config["strike_min_pwm"])
    maximum_pwm = int(actuation_config["strike_max_pwm"])
    normalized_velocity = 0.0 if velocity <= 1 else (velocity - 1) / 126.0
    pwm_value = minimum_pwm + int(round((maximum_pwm - minimum_pwm) * normalized_velocity))
    return clamp(pwm_value, minimum_pwm, maximum_pwm)


def strike_to_hold_pwm(strike_pwm, actuation_config):
    hold_ratio = float(actuation_config["hold_ratio"])
    hold_pwm = int(round(strike_pwm * hold_ratio))
    return clamp(
        hold_pwm,
        int(actuation_config["hold_min_pwm"]),
        int(actuation_config["hold_max_pwm"]),
    )


def build_playback_events(scheduled_notes, config):
    timeline = []
    scheduled_note_metadata = []
    hold_event_count = 0
    strike_only_note_count = 0

    for note_event in scheduled_notes:
        channel_actuation = resolve_channel_actuation(note_event["channel"], config)
        strike_ms = int(channel_actuation["strike_ms"])
        release_delay_ms = int(channel_actuation["release_delay_ms"])
        strike_pwm = velocity_to_strike_pwm(note_event["velocity"], channel_actuation)
        hold_pwm = strike_to_hold_pwm(strike_pwm, channel_actuation)
        note_duration_ms = max(1, note_event["end_ms"] - note_event["start_ms"])
        hold_start_ms = note_event["start_ms"] + strike_ms
        release_ms = note_event["end_ms"] + release_delay_ms

        timeline.append((note_event["start_ms"], note_event["channel"], strike_pwm))

        if hold_start_ms < note_event["end_ms"]:
            timeline.append((hold_start_ms, note_event["channel"], hold_pwm))
            hold_event_count += 1
        else:
            strike_only_note_count += 1

        timeline.append((release_ms, note_event["channel"], 0))

        scheduled_note_metadata.append(
            {
                "source_note": note_event.get("source_note", note_event["note"]),
                "source_note_label": midi_note_name(note_event.get("source_note", note_event["note"])),
                "input_note": note_event["note"],
                "note_label": midi_note_name(note_event["note"]),
                "velocity": note_event["velocity"],
                "channel": note_event["channel"],
                "source_channel": note_event.get("source_channel"),
                "original_start_ms": note_event["original_start_ms"],
                "original_end_ms": note_event["original_end_ms"],
                "scheduled_start_ms": note_event["start_ms"],
                "scheduled_end_ms": note_event["end_ms"],
                "scheduled_duration_ms": note_duration_ms,
                "strike_pwm": strike_pwm,
                "hold_pwm": hold_pwm,
                "release_ms": release_ms,
                "actuation": channel_actuation,
            }
        )

    timeline.sort(key=lambda item: (item[0], 0 if item[2] == 0 else 1, item[1]))
    return timeline, scheduled_note_metadata, {
        "hold_events": hold_event_count,
        "strike_only_notes": strike_only_note_count,
    }


def convert_to_delta_events(timeline):
    delta_events = []
    previous_time = 0

    for time_ms, channel, pwm_value in timeline:
        dt_ms = max(0, time_ms - previous_time)
        delta_events.append((dt_ms, channel, pwm_value))
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


def render_header_text(selected_midi, delta_events, metadata, config):
    pca_config = config["pca9685"]
    mapping_lines = metadata["mapping_lines"]
    channel_lines = metadata["channel_lines"]

    lines = [
        "#pragma once",
        "#include <Arduino.h>",
        "#include <avr/pgmspace.h>",
        "",
        f"// Auto-generated from: {selected_midi.name}",
        f"// Base tempo: {metadata['original_bpm']:.2f} BPM",
        f"// Tempo override: {metadata['tempo_label']}",
        f"// Effective output tempo: {metadata['effective_bpm']:.2f} BPM",
        f"// Detected MIDI note range: {metadata['source_range_label']}",
        f"// Active playable layout: {metadata['playable_layout_label']}",
        f"// Fit mode: {metadata['fit_mode_label']}",
        f"// Strict coverage: {metadata['strict_playable_summary']}",
        f"// Octave transpose coverage: {metadata['transpose_playable_summary']}",
        f"// Mapping mode: {config['mapping']['mode']}",
        f"// Forced retriggers: {metadata['forced_retriggers']}",
        f"// Delayed notes: {metadata['delayed_notes']}",
        f"// Unmapped notes skipped: {metadata['unmapped_notes']}",
        f"// Unmatched note_off events ignored: {metadata['unmatched_note_offs']}",
        f"// Dangling note_on events auto-closed: {metadata['dangling_note_ons_closed']}",
        f"// Percussion note events ignored: {metadata['percussion_events_skipped']}",
        "",
        "// Piano actuator mapping used for this file:",
    ]

    for line in mapping_lines:
        lines.append(f"//   {line}")

    lines.extend(
        [
            "",
            "// Active hardware channels in this export:",
        ]
    )

    for line in channel_lines:
        lines.append(f"//   {line}")

    lines.extend(
        [
            "",
            "// Actuation profile:",
        ]
    )

    for line in metadata["actuation_lines"]:
        lines.append(f"//   {line}")

    lines.extend(
        [
            "",
            f"const uint8_t SONG_PCA9685_I2C_ADDRESS = 0x{int(pca_config['i2c_address']):02X};",
            f"const uint16_t SONG_PCA9685_PWM_FREQUENCY_HZ = {int(pca_config['pwm_frequency_hz'])}u;",
            f"const uint8_t SONG_CHANNEL_COUNT = {len(metadata['channels_used'])}u;",
            "const uint8_t SONG_CHANNELS[] = {",
        ]
    )

    for channel in metadata["channels_used"]:
        lines.append(f"  {channel}u,")

    lines.extend(
        [
            "};",
            "",
            "typedef struct {",
            "  uint32_t dt_ms;   // delay BEFORE this event",
            "  uint8_t  channel; // PCA9685 channel",
            "  uint16_t pwm;     // 0-4095 duty cycle",
            "} SolenoidEvent;",
            "",
            "const SolenoidEvent SONG[] PROGMEM = {",
        ]
    )

    for dt_ms, channel, pwm_value in delta_events:
        lines.append(f"  {{ {dt_ms}u, {channel}u, {pwm_value}u }},")

    lines.extend(
        [
            "};",
            "",
            "const uint32_t SONG_EVENT_COUNT = sizeof(SONG) / sizeof(SONG[0]);",
            "",
        ]
    )

    return "\n".join(lines)


def build_channel_lines(channels_used, mapping_config):
    channel_labels = mapping_config.get("channel_labels", {})
    lines = []
    for channel in channels_used:
        label = channel_labels.get(str(channel), f"Channel {channel}")
        lines.append(f"PCA9685 channel {channel}: {label}")
    return lines


def build_actuation_lines(channels_used, config):
    lines = []
    for channel in channels_used:
        actuation = resolve_channel_actuation(channel, config)
        lines.append(
            "Channel "
            f"{channel}: strike {actuation['strike_min_pwm']}-{actuation['strike_max_pwm']}, "
            f"hold {actuation['hold_min_pwm']}-{actuation['hold_max_pwm']}, "
            f"hold ratio {actuation['hold_ratio']}, "
            f"strike {actuation['strike_ms']} ms, "
            f"release delay {actuation['release_delay_ms']} ms, "
            f"rearm {actuation['minimum_rearm_gap_ms']} ms, "
            f"retrigger {actuation['retrigger_gap_ms']} ms"
        )
    return lines


def build_manifest_payload(selected_midi, metadata, config):
    return {
        "source_midi": selected_midi.name,
        "source_midi_path": str(selected_midi),
        "project_mode": metadata["project_mode"],
        "effective_bpm": metadata["effective_bpm"],
        "channels_used": metadata["channels_used"],
        "mapping_lines": metadata["mapping_lines"],
        "config_path": str(CONFIG_PATH),
    }


def choose_serial_port(serial_config):
    preferred_port = serial_config.get("preferred_port", "").strip()
    if preferred_port:
        return preferred_port

    if serial is None or list_ports is None:
        raise RuntimeError(
            "pyserial is not installed. Install it with 'pip install pyserial' to use USB playback."
        )

    ports = list(list_ports.comports())
    if not ports:
        raise RuntimeError("No serial devices were found. Connect the Arduino over USB and try again.")

    if len(ports) == 1:
        return ports[0].device

    candidate_ports = []
    for port in ports:
        descriptor = " ".join(
            filter(
                None,
                [
                    port.device,
                    getattr(port, "description", ""),
                    getattr(port, "manufacturer", ""),
                    getattr(port, "hwid", ""),
                ],
            )
        ).lower()
        if any(token in descriptor for token in ("arduino", "wch", "ch340", "usb serial", "uno")):
            candidate_ports.append(port)

    if len(candidate_ports) == 1:
        return candidate_ports[0].device

    print("Multiple serial ports were found:")
    choices = candidate_ports or ports
    for index, port in enumerate(choices, start=1):
        description = getattr(port, "description", "")
        print(f"  {index}. {port.device} - {description}")

    while True:
        raw = input("Choose the Arduino COM port number: ").strip()
        if raw.isdigit():
            selected_index = int(raw)
            if 1 <= selected_index <= len(choices):
                return choices[selected_index - 1].device
        print("Enter a valid port number.")


def read_serial_response(connection, deadline):
    while time.time() < deadline:
        raw_line = connection.readline()
        if not raw_line:
            continue
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        return line
    raise TimeoutError("Timed out waiting for a response from the Arduino runtime.")


def send_serial_command(connection, command, expected_prefixes, timeout_seconds=3.0):
    connection.write((command + "\n").encode("ascii"))
    connection.flush()
    deadline = time.time() + timeout_seconds
    while True:
        response = read_serial_response(connection, deadline)
        if any(response.startswith(prefix) for prefix in expected_prefixes):
            return response


def stream_song_to_arduino(payload, deployment_config):
    serial_config = deployment_config.get("serial_runtime", {})
    if not serial_config.get("enabled", True):
        return None

    port = choose_serial_port(serial_config)
    baud_rate = int(serial_config.get("baud_rate", 115200))
    startup_wait_ms = int(serial_config.get("startup_wait_ms", 2500))
    events = payload["events"]

    with serial.Serial(port=port, baudrate=baud_rate, timeout=0.5) as connection:
        time.sleep(startup_wait_ms / 1000.0)
        connection.reset_input_buffer()
        connection.reset_output_buffer()

        send_serial_command(connection, "HELLO", ("READY",), timeout_seconds=4.0)
        send_serial_command(connection, "STOP", ("OK STOPPED",), timeout_seconds=2.0)
        send_serial_command(connection, "CLEAR", ("OK CLEARED",), timeout_seconds=2.0)
        send_serial_command(connection, f"BEGIN {len(events)}", ("OK BEGIN",), timeout_seconds=2.0)

        for event in events:
            command = f"EVENT {event['dt_ms']} {event['channel']} {event['pwm']}"
            connection.write((command + "\n").encode("ascii"))

        connection.flush()
        load_response = read_serial_response(connection, time.time() + 4.0)
        if not load_response.startswith("OK SONG_LOADED"):
            raise RuntimeError(f"Unexpected response while loading the song: {load_response}")

        play_response = send_serial_command(connection, "PLAY", ("OK PLAYING",), timeout_seconds=2.0)

    manifest_payload = {
        "port": port,
        "baud_rate": baud_rate,
        "source_midi": payload["source_midi"],
        "output_header": payload["output_header"],
        "stream_response": play_response,
    }
    STREAM_MANIFEST_PATH.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")

    return manifest_payload


def sync_arduino_ide_runtime(header_text, deployment_config):
    sync_config = deployment_config.get("arduino_ide_sync", {})
    if not sync_config.get("enabled", False):
        return None

    sketch_path = Path(sync_config["sketch_path"])
    generated_dir_name = sync_config.get("generated_dir_name", "generated")
    generated_dir = sketch_path.parent / generated_dir_name

    runtime_text = REPO_RUNTIME_SKETCH_PATH.read_text(encoding="utf-8")
    generated_dir.mkdir(parents=True, exist_ok=True)
    deployed_header_path = generated_dir / ACTIVE_HEADER_NAME

    try:
        sketch_path.write_text(runtime_text, encoding="utf-8")
        deployed_header_path.write_text(header_text, encoding="utf-8")
    except PermissionError as error:
        return {
            "sketch_path": sketch_path,
            "active_header_path": deployed_header_path,
            "sync_error": str(error),
        }

    return {
        "sketch_path": sketch_path,
        "active_header_path": deployed_header_path,
    }


def write_outputs(selected_midi, header_path, delta_events, metadata, config, scheduled_notes, deployment_config):
    HEADER_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    header_text = render_header_text(selected_midi, delta_events, metadata, config)
    header_path.write_text(header_text, encoding="utf-8")

    active_header_path = HEADER_DIR / ACTIVE_HEADER_NAME
    active_header_path.write_text(header_text, encoding="utf-8")

    payload = {
        "source_midi": selected_midi.name,
        "source_midi_path": str(selected_midi.relative_to(REPO_ROOT)),
        "output_header": header_path.name,
        "output_header_path": str(header_path.relative_to(REPO_ROOT)),
        "active_header": ACTIVE_HEADER_NAME,
        "active_header_path": str(active_header_path.relative_to(REPO_ROOT)),
        "config_path": str(CONFIG_PATH.relative_to(REPO_ROOT)),
        "events": [
            {"dt_ms": dt_ms, "channel": channel, "pwm": pwm_value}
            for dt_ms, channel, pwm_value in delta_events
        ],
        "scheduled_notes": scheduled_notes,
        "metadata": metadata,
        "config": config,
    }

    json_path = METADATA_DIR / f"{header_path.stem}.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    active_json_path = METADATA_DIR / ACTIVE_METADATA_NAME
    active_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    deployment_paths = sync_arduino_ide_runtime(header_text, deployment_config)

    return json_path, active_header_path, active_json_path, deployment_paths, payload


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Convert a MIDI file for the autonomous piano player and optionally send it over USB."
    )
    parser.add_argument("--song", help="Full path to a MIDI file to use.")
    parser.add_argument("--project-song", help="Filename of a MIDI already in songs/midi.")
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Convert and write files, but do not send the song over USB.",
    )
    return parser


def main():
    args = build_arg_parser().parse_args()
    config = load_config()
    deployment_config = load_deployment_config()
    selected_midi_source = choose_input_midi(args)
    selected_midi, was_imported = import_midi_to_library(selected_midi_source)

    mid = MidiFile(str(selected_midi))
    tempo_info = scan_tempo_info(mid)
    note_intervals, interval_stats = extract_note_intervals(mid)
    if not note_intervals:
        raise ValueError("No note_on events were found in the selected MIDI file.")

    effective_mapping, playable_layout_summary, mapping_overridden = prompt_for_playable_range(
        config["mapping"]
    )
    effective_config = dict(config)
    effective_config["mapping"] = effective_mapping

    fit_selection = prompt_for_fit_mode(note_intervals, effective_mapping)
    if fit_selection["mode"] == "cancel":
        print("Cancelled before conversion.")
        return

    applied_octave_shift = 0 if fit_selection["mode"] == "strict" else fit_selection["best_octave_shift"]
    shifted_intervals = transpose_note_intervals(note_intervals, applied_octave_shift)
    tempo_override = prompt_for_tempo_override(tempo_info["first_bpm"])
    scaled_intervals = scale_intervals(shifted_intervals, tempo_override["scale"])
    scheduled_notes, scheduling_stats = schedule_notes(scaled_intervals, effective_config)
    if not scheduled_notes:
        raise ValueError(
            "No playable notes remained after applying the selected fit mode. Try transpose, a different playable range, or another song."
        )
    timeline, scheduled_note_metadata, playback_stats = build_playback_events(
        scheduled_notes, effective_config
    )
    delta_events = convert_to_delta_events(timeline)

    header_path, output_version = next_header_path(HEADER_DIR, selected_midi)
    output_version_label = "base" if output_version == 0 else f"v{output_version}"
    mapping_lines = describe_mapping(effective_config["mapping"])
    channel_lines = build_channel_lines(scheduling_stats["channels_used"], effective_config["mapping"])
    actuation_lines = build_actuation_lines(scheduling_stats["channels_used"], effective_config)

    if fit_selection["mode"] == "strict":
        fit_mode_label = "strict (original pitches, skip out-of-range notes)"
    elif applied_octave_shift == 0:
        fit_mode_label = "transpose by octave (best shift was 0 semitones)"
    else:
        direction = "up" if applied_octave_shift > 0 else "down"
        fit_mode_label = (
            f"transpose by octave ({direction} {abs(applied_octave_shift) // 12} octave(s), "
            f"{applied_octave_shift:+d} semitones)"
        )

    metadata = {
        "project_mode": config["project_mode"],
        "output_version_label": output_version_label,
        "original_bpm": tempo_info["first_bpm"],
        "tempo_label": tempo_override["label"],
        "effective_bpm": tempo_override["target_bpm"],
        "tempo_change_count": tempo_info["tempo_change_count"],
        "source_range_label": fit_selection["source_range"]["range_label"],
        "playable_layout_label": playable_layout_summary["label"],
        "fit_mode": fit_selection["mode"],
        "fit_mode_label": fit_mode_label,
        "transpose_semitones": applied_octave_shift,
        "strict_playable_count": fit_selection["strict_playable_count"],
        "strict_playable_summary": fit_selection["strict_summary"],
        "transpose_playable_count": fit_selection["transpose_playable_count"],
        "transpose_playable_summary": fit_selection["transpose_summary"],
        "mapping_override_used": mapping_overridden,
        "source_note_count": len(note_intervals),
        "scheduled_note_count": len(scheduled_notes),
        "event_count": len(delta_events),
        "forced_retriggers": scheduling_stats["forced_retriggers"],
        "delayed_notes": scheduling_stats["delayed_notes"],
        "unmapped_notes": scheduling_stats["unmapped_notes"],
        "unmatched_note_offs": interval_stats["unmatched_note_offs"],
        "dangling_note_ons_closed": interval_stats["dangling_note_ons_closed"],
        "percussion_events_skipped": interval_stats["percussion_events_skipped"],
        "hold_events": playback_stats["hold_events"],
        "strike_only_notes": playback_stats["strike_only_notes"],
        "mapping_lines": mapping_lines,
        "channel_lines": channel_lines,
        "actuation_lines": actuation_lines,
        "channels_used": scheduling_stats["channels_used"],
    }

    json_path, active_header_path, active_json_path, deployment_paths, payload = write_outputs(
        selected_midi,
        header_path,
        delta_events,
        metadata,
        effective_config,
        scheduled_note_metadata,
        deployment_config,
    )

    stream_manifest = None
    if not args.export_only:
        stream_manifest = stream_song_to_arduino(payload, deployment_config)

    print("\nSelected file:", selected_midi.name)
    print(f"Original source path: {selected_midi_source}")
    if was_imported:
        print(f"Imported into project library: {selected_midi}")
    print(f"Type: {mid.type}")
    print(f"Ticks per beat: {mid.ticks_per_beat}")
    print(f"Number of tracks: {len(mid.tracks)}")
    print(f"Tempo events found: {tempo_info['tempo_change_count']}")
    print(f"Detected MIDI note range: {fit_selection['source_range']['range_label']}")
    print(f"Playable layout: {playable_layout_summary['label']}")
    print(f"Strict coverage: {fit_selection['strict_summary']}")
    print(f"Transpose coverage: {fit_selection['transpose_summary']}")
    print(f"Fit mode used: {fit_mode_label}")
    print(f"Range override used: {'yes' if mapping_overridden else 'no'}")
    print("Mapping summary:")
    for line in mapping_lines:
        print(f"  {line}")
    print("Channel summary:")
    for line in channel_lines:
        print(f"  {line}")
    print("Actuation summary:")
    for line in actuation_lines:
        print(f"  {line}")
    print("\nConversion complete.")
    print(f"Versioned header: {header_path.relative_to(REPO_ROOT)}")
    print(f"Active Arduino header: {active_header_path.relative_to(REPO_ROOT)}")
    print(f"Versioned metadata: {json_path.relative_to(REPO_ROOT)}")
    print(f"Active metadata: {active_json_path.relative_to(REPO_ROOT)}")
    if deployment_paths is not None:
        print(f"Synced Arduino IDE sketch: {deployment_paths['sketch_path']}")
        print(f"Synced Arduino IDE active header: {deployment_paths['active_header_path']}")
        if "sync_error" in deployment_paths:
            print(f"Arduino IDE sync warning: {deployment_paths['sync_error']}")
    if stream_manifest is not None:
        print(f"USB playback sent on port: {stream_manifest['port']}")
    print(f"Output header version: {output_version_label}")
    print(f"Base tempo: {tempo_info['first_bpm']:.2f} BPM")
    print(f"Effective output tempo: {tempo_override['target_bpm']:.2f} BPM")
    print(f"Input note intervals: {len(note_intervals)}")
    print(f"Scheduled notes: {len(scheduled_notes)}")
    print(f"Generated events: {len(delta_events)}")
    print(f"Forced retriggers: {scheduling_stats['forced_retriggers']}")
    print(f"Delayed notes: {scheduling_stats['delayed_notes']}")
    print(f"Hold events: {playback_stats['hold_events']}")
    print(f"Strike-only notes: {playback_stats['strike_only_notes']}")
    print(f"Unmapped notes skipped: {scheduling_stats['unmapped_notes']}")
    print(f"Unmatched note_off events ignored: {interval_stats['unmatched_note_offs']}")
    print(f"Dangling note_on events auto-closed: {interval_stats['dangling_note_ons_closed']}")
    print(f"Percussion note events ignored: {interval_stats['percussion_events_skipped']}")


if __name__ == "__main__":
    main()
