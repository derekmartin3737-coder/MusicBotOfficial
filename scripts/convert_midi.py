"""MIDI-to-solenoid conversion and playback engine.

This is the main Python module for the autonomous piano player. It handles the
full user workflow:

1. Pick a MIDI file from Downloads, the project song library, or a direct path.
2. Scan the MIDI for tempo, note range, percussion, and playable coverage.
3. Map MIDI notes onto the configured PCA9685/MOSFET solenoid channels.
4. Convert note timing into strike, hold, and release PWM events.
5. Write generated Arduino/header metadata and optionally stream the song over
   USB to the fixed Arduino runtime.

Generated song files are outputs, not hand-maintained source. Most hardware
behavior should be adjusted in config/piano_config.json instead of editing this
module.
"""

import argparse
import copy
import filecmp
import json
import re
import shutil
import time
from collections import defaultdict
from pathlib import Path

import mido
from mido import MidiFile

# pyserial is optional for dry runs. Import lazily so classmates can still
# analyze MIDI files without an Arduino plugged in.
try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

# MIDI files may omit tempo; 500000 us/beat is the MIDI default for 120 BPM.
DEFAULT_TEMPO_US_PER_BEAT = 500000
ACTIVE_HEADER_NAME = "current_song.h"
ACTIVE_METADATA_NAME = "current_song.json"
PCA9685_CHANNELS_PER_BOARD = 16
MAX_PCA9685_BOARDS = 4

VERSION_RE = re.compile(r"^(?P<name>.+?)(?:_v(?P<version>\d+))?$")
NOTE_TOKEN_RE = re.compile(r"^\s*([A-Ga-g])([#b]?)(-?\d+)\s*$")
NUMERIC_RANGE_RE = re.compile(r"^\s*(-?\d+)\s*-\s*(-?\d+)\s*$")
NOTE_RANGE_RE = re.compile(r"^\s*([A-Ga-g][#b]?-?\d+)\s*-\s*([A-Ga-g][#b]?-?\d+)\s*$")

# All paths are rooted at the repository so the scripts work from VS Code,
# PowerShell, or a different current working directory.
REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "piano_config.json"
DEPLOYMENT_CONFIG_PATH = REPO_ROOT / "config" / "deployment_paths.json"
USER_PREFERENCES_PATH = REPO_ROOT / "config" / "user_preferences.json"
CALIBRATED_MAPPING_PATH = REPO_ROOT / "config" / "calibrated_mapping.json"
MIDI_DIR = REPO_ROOT / "songs" / "midi"
METADATA_DIR = REPO_ROOT / "songs" / "metadata"
ARDUINO_PROJECT_DIR = REPO_ROOT / "arduino" / "MusicBotOfficial"
HEADER_DIR = ARDUINO_PROJECT_DIR / "generated"
REPO_RUNTIME_SKETCH_PATH = ARDUINO_PROJECT_DIR / "MusicBotOfficial.ino"
DOWNLOADS_DIR = Path.home() / "Downloads"
STREAM_MANIFEST_PATH = METADATA_DIR / "last_streamed_song.json"

DEFAULT_USER_PREFERENCES = {
    "playback": {
        "auto_use_newest_download": True,
        "default_fit_mode": "prompt",
        "default_playable_range": "",
        "default_tempo": "",
        "wait_for_finish": True,
        "show_diagnostics": True,
    }
}


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def report_line(reporter, message=""):
    if reporter is None:
        return
    reporter(message)


def normalize_pca_config(pca_config):
    normalized = dict(pca_config or {})
    board_addresses = normalized.get("board_addresses")
    if board_addresses:
        normalized["board_addresses"] = [int(address) for address in board_addresses]
    elif "i2c_address" in normalized:
        normalized["board_addresses"] = [int(normalized["i2c_address"])]
    else:
        normalized["board_addresses"] = [0x40]
    normalized["pwm_frequency_hz"] = int(normalized.get("pwm_frequency_hz", 250))
    return normalized


def get_pca_board_addresses(config_or_pca):
    if "pca9685" in config_or_pca:
        pca_config = config_or_pca["pca9685"]
    else:
        pca_config = config_or_pca
    return normalize_pca_config(pca_config)["board_addresses"]


def get_global_channel_capacity(config_or_pca):
    return len(get_pca_board_addresses(config_or_pca)) * PCA9685_CHANNELS_PER_BOARD


def split_global_channel(channel, config_or_pca):
    channel = int(channel)
    board_addresses = get_pca_board_addresses(config_or_pca)
    capacity = len(board_addresses) * PCA9685_CHANNELS_PER_BOARD
    if not 0 <= channel < capacity:
        raise ValueError(
            f"Global channel {channel} is outside the configured PCA9685 capacity of 0-{capacity - 1}."
        )

    board_index = channel // PCA9685_CHANNELS_PER_BOARD
    local_channel = channel % PCA9685_CHANNELS_PER_BOARD
    return {
        "global_channel": channel,
        "board_index": board_index,
        "i2c_address": board_addresses[board_index],
        "local_channel": local_channel,
    }


def describe_global_channel(channel, config_or_pca):
    target = split_global_channel(channel, config_or_pca)
    return (
        f"global channel {target['global_channel']} "
        f"(PCA9685 0x{target['i2c_address']:02X} channel {target['local_channel']})"
    )


def validate_mapping_channels(mapping_config, pca_config):
    capacity = get_global_channel_capacity(pca_config)

    def validate_channel_value(channel, context):
        channel = int(channel)
        if not 0 <= channel < capacity:
            raise ValueError(
                f"{context} uses global channel {channel}, but the configured PCA9685 hardware only exposes "
                f"channels 0-{capacity - 1}."
            )

    for note, channel in mapping_config.get("note_to_channel", {}).items():
        validate_channel_value(channel, f"Note {note}")

    for channel in mapping_config.get("channel_sequence", []):
        validate_channel_value(channel, "channel_sequence")


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


def parse_active_channel_count(raw, pca_config):
    raw = str(raw).strip()
    if not raw:
        return None

    try:
        count = int(raw)
    except ValueError as error:
        raise ValueError("Active hardware channel count must be a whole number.") from error

    capacity = get_global_channel_capacity(pca_config)
    if not 1 <= count <= capacity:
        raise ValueError(f"Active hardware channel count must be between 1 and {capacity}.")
    return count


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
        config = json.load(handle)
    config["pca9685"] = normalize_pca_config(config.get("pca9685", {}))

    # Manual calibration writes config/calibrated_mapping.json. When that file
    # exists, it overrides the default repo mapping without permanently editing
    # piano_config.json. This lets each hardware build keep its own wiring map.
    if CALIBRATED_MAPPING_PATH.exists():
        with CALIBRATED_MAPPING_PATH.open("r", encoding="utf-8") as handle:
            calibrated_payload = json.load(handle)

        calibrated_mapping = calibrated_payload.get("mapping", calibrated_payload)
        if isinstance(calibrated_mapping, dict) and calibrated_mapping:
            config["mapping"] = calibrated_mapping
            config.setdefault("notes", {})
            config["notes"]["calibrated_mapping_path"] = str(CALIBRATED_MAPPING_PATH.relative_to(REPO_ROOT))

    validate_mapping_channels(config["mapping"], config["pca9685"])

    return config


def load_user_preferences():
    preferences = copy.deepcopy(DEFAULT_USER_PREFERENCES)
    if not USER_PREFERENCES_PATH.exists():
        return preferences

    with USER_PREFERENCES_PATH.open("r", encoding="utf-8") as handle:
        loaded_preferences = json.load(handle)

    for section, defaults in preferences.items():
        loaded_section = loaded_preferences.get(section, {})
        if isinstance(loaded_section, dict):
            defaults.update(loaded_section)
    return preferences


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


def collect_download_files(directory: Path):
    if not directory.exists():
        return []
    return sorted(
        [path for path in directory.iterdir() if path.is_file()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def collect_download_midis(directory: Path):
    return [
        path
        for path in collect_download_files(directory)
        if path.suffix.lower() in {".mid", ".midi"}
    ]


def find_latest_download_zip(directory: Path):
    for path in collect_download_files(directory):
        if path.suffix.lower() == ".zip":
            return path
    return None


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
    existing_same_name_path = MIDI_DIR / source_path.name
    if existing_same_name_path.exists() and filecmp.cmp(source_path, existing_same_name_path, shallow=False):
        return existing_same_name_path, False

    for existing_import in MIDI_DIR.glob(f"{source_path.stem}_imported_v*{source_path.suffix}"):
        if filecmp.cmp(source_path, existing_import, shallow=False):
            return existing_import, False

    target_path = next_library_midi_path(source_path)
    shutil.copy2(source_path, target_path)
    return target_path, True


def build_song_catalog(user_preferences):
    download_midis = collect_download_midis(DOWNLOADS_DIR)
    project_midis = collect_midis(MIDI_DIR)
    latest_zip = find_latest_download_zip(DOWNLOADS_DIR)
    auto_use_latest = bool(user_preferences["playback"].get("auto_use_newest_download", True))

    entries = []
    for path in download_midis:
        entries.append(
            {
                "path": path,
                "source": "Downloads",
                "display_name": path.name,
                "description": f"Downloads | {path.name}",
            }
        )
    for path in project_midis:
        entries.append(
            {
                "path": path,
                "source": "Library",
                "display_name": path.name,
                "description": f"Library | {path.name}",
            }
        )

    suggested_path = None
    suggested_reason = None
    if download_midis and auto_use_latest:
        suggested_path = download_midis[0]
        suggested_reason = "newest downloaded MIDI in Windows Downloads"
    elif project_midis:
        suggested_path = project_midis[0]
        suggested_reason = "first song in the project MIDI library"
    elif download_midis:
        suggested_path = download_midis[0]
        suggested_reason = "newest downloaded MIDI in Windows Downloads"

    return {
        "entries": entries,
        "suggested_path": suggested_path,
        "suggested_reason": suggested_reason,
        "latest_zip": latest_zip,
    }


def inspect_midi_file(midi_path):
    midi_path = Path(midi_path).expanduser()
    mid = MidiFile(str(midi_path))
    tempo_info = scan_tempo_info(mid)
    note_intervals, interval_stats = extract_note_intervals(mid)
    range_info = analyze_note_range(note_intervals)

    return {
        "path": midi_path,
        "name": midi_path.name,
        "track_count": len(mid.tracks),
        "type": mid.type,
        "ticks_per_beat": mid.ticks_per_beat,
        "tempo_bpm": tempo_info["first_bpm"],
        "tempo_change_count": tempo_info["tempo_change_count"],
        "range_label": range_info["range_label"],
        "note_count": len(note_intervals),
        "percussion_events_skipped": interval_stats["percussion_events_skipped"],
    }


def choose_input_midi(args, user_preferences):
    # Selection priority is deliberate:
    # direct path > named project song > interactive library > newest download.
    # That keeps the "just download and run" workflow simple while still giving
    # advanced users repeatable command-line control.
    if args.song:
        chosen_path = Path(args.song).expanduser()
        if not chosen_path.exists():
            raise FileNotFoundError(f"Specified MIDI path does not exist: {chosen_path}")
        return chosen_path, "explicit MIDI path provided by the user"

    if args.project_song:
        chosen_path = MIDI_DIR / args.project_song
        if not chosen_path.exists():
            raise FileNotFoundError(f"Project MIDI not found: {chosen_path}")
        return chosen_path, "explicit project library selection"

    if args.choose_library:
        return prompt_for_song(collect_midis(MIDI_DIR)), "manual project library selection"

    download_midis = collect_download_midis(DOWNLOADS_DIR)
    auto_use_latest = bool(user_preferences["playback"].get("auto_use_newest_download", True))
    if download_midis:
        newest_download = download_midis[0]
        if auto_use_latest or args.play_latest:
            print(f"Using newest downloaded MIDI automatically: {newest_download.name}")
            print(f"Location: {newest_download}")
            return newest_download, "newest downloaded MIDI in Windows Downloads"

    latest_zip = find_latest_download_zip(DOWNLOADS_DIR)
    if latest_zip and not download_midis:
        print(f"No MIDI files were found in {DOWNLOADS_DIR}.")
        print(f"The newest likely download is a ZIP file: {latest_zip.name}")
        print("If your MIDI came in a ZIP archive, unzip it first and rerun this command.")

    project_midis = collect_midis(MIDI_DIR)
    if project_midis:
        print(f"Falling back to the project MIDI library because no downloaded MIDI was auto-selected.")
        return prompt_for_song(project_midis), "fallback to the project MIDI library"

    raise FileNotFoundError(
        f"No MIDI files were found in {DOWNLOADS_DIR} or {MIDI_DIR}. Download a .mid file and try again."
    )


def collect_midis(directory: Path):
    if not directory.exists():
        return []
    return sorted(
        [
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in {".mid", ".midi"}
        ],
        key=lambda path: path.name.lower(),
    )


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


def parse_tempo_override_input(raw, original_bpm: float):
    raw = str(raw).strip().lower()
    if not raw:
        return {
            "mode": "original",
            "target_bpm": original_bpm,
            "scale": 1.0,
            "label": "original timing",
        }

    if raw.endswith("x"):
        multiplier = float(raw[:-1])
        if multiplier <= 0:
            raise ValueError("Multiplier must be greater than zero.")

        target_bpm = original_bpm * multiplier
        return {
            "mode": "multiplier",
            "target_bpm": target_bpm,
            "scale": 1.0 / multiplier,
            "label": f"{multiplier:.3f}x",
        }

    if raw.endswith("bpm"):
        target_bpm = float(raw[:-3].strip())
        if target_bpm <= 0:
            raise ValueError("BPM must be greater than zero.")

        return {
            "mode": "bpm",
            "target_bpm": target_bpm,
            "scale": original_bpm / target_bpm,
            "label": f"{target_bpm:.2f} BPM",
        }

    numeric_value = float(raw)
    # Bare values like ".5" are treated as speed multipliers because that is how
    # users naturally request half-speed playback. Use "8bpm" for an actual
    # extremely slow BPM value.
    if 0 < numeric_value <= 4:
        multiplier = numeric_value
        target_bpm = original_bpm * multiplier
        return {
            "mode": "multiplier",
            "target_bpm": target_bpm,
            "scale": 1.0 / multiplier,
            "label": f"{multiplier:.3f}x",
        }

    target_bpm = numeric_value
    if target_bpm <= 0:
        raise ValueError("BPM must be greater than zero.")

    return {
        "mode": "bpm",
        "target_bpm": target_bpm,
        "scale": original_bpm / target_bpm,
        "label": f"{target_bpm:.2f} BPM",
    }


def prompt_for_tempo_override(original_bpm: float, preset=None):
    if preset not in (None, ""):
        return parse_tempo_override_input(preset, original_bpm)

    print(f"\nOriginal/base tempo: {original_bpm:.2f} BPM")
    print("Tempo override options:")
    print("  Press Enter to keep the original timing")
    print("  Enter a BPM number, such as 140")
    print("  Enter a multiplier like 0.85x or 1.10x")
    print("  Tip: bare values from 0 to 4, like .5, are treated as multipliers")
    print("  Use an explicit BPM suffix for very slow tempos, such as 8bpm")

    while True:
        raw = input("Tempo override: ").strip().lower()
        try:
            return parse_tempo_override_input(raw, original_bpm)
        except ValueError as error:
            print(error)


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
    """Return note intervals in milliseconds from the merged MIDI timeline.

    A note interval is the musical note-level object we use before hardware
    scheduling: pitch, velocity, start time, end time, and source MIDI channel.
    Percussion channel 9 is skipped because MIDI channel 10 is conventionally
    drums, not pitched piano notes.
    """
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
    """Return the hardware channels in the order calibration should visit them."""
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


def get_available_channel_sequence(mapping_config, pca_config):
    capacity = get_global_channel_capacity(pca_config)
    base_sequence = get_mapping_channel_order(mapping_config)
    available = list(base_sequence)
    seen_channels = set(available)

    for channel in range(capacity):
        if channel not in seen_channels:
            available.append(channel)
            seen_channels.add(channel)

    return available


def resolve_active_channel_sequence(mapping_config, pca_config, active_channel_count=None):
    current_sequence = get_mapping_channel_order(mapping_config)
    if active_channel_count in (None, ""):
        return current_sequence

    count = parse_active_channel_count(active_channel_count, pca_config)
    available_sequence = get_available_channel_sequence(mapping_config, pca_config)
    return available_sequence[:count]


def apply_active_channel_limit(mapping_config, pca_config, active_channel_count=None):
    resolved_sequence = resolve_active_channel_sequence(mapping_config, pca_config, active_channel_count)
    limited_mapping = copy.deepcopy(mapping_config)
    limited_mapping["channel_sequence"] = resolved_sequence

    if limited_mapping["mode"] == "collapse_all_notes_to_single_channel":
        single_channel = int(limited_mapping["single_channel"])
        if single_channel not in set(resolved_sequence):
            raise ValueError(
                f"Single-channel test mode uses {describe_global_channel(single_channel, pca_config)}, "
                "but that channel is outside the currently active hardware count."
            )
    elif limited_mapping["mode"] == "explicit_note_map":
        active_channels = set(resolved_sequence)
        note_to_channel = {
            str(note): int(channel)
            for note, channel in limited_mapping.get("note_to_channel", {}).items()
            if int(channel) in active_channels
        }
        limited_mapping["note_to_channel"] = dict(sorted(note_to_channel.items(), key=lambda item: int(item[0])))

        if "note_labels" in limited_mapping:
            limited_mapping["note_labels"] = {
                note: label
                for note, label in limited_mapping["note_labels"].items()
                if note in limited_mapping["note_to_channel"]
            }

    return limited_mapping, resolved_sequence


def summarize_active_channel_sequence(channel_sequence, pca_config):
    if not channel_sequence:
        return "No active hardware channels selected"

    if len(channel_sequence) == 1:
        return f"1 active hardware channel: {describe_global_channel(channel_sequence[0], pca_config)}"

    return (
        f"{len(channel_sequence)} active hardware channels from "
        f"{describe_global_channel(channel_sequence[0], pca_config)} through "
        f"{describe_global_channel(channel_sequence[-1], pca_config)}"
    )


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


def prompt_for_playable_range(mapping_config, preset=None):
    """Let users keep the saved layout or temporarily fit it to another octave."""
    channel_order = get_mapping_channel_order(mapping_config)
    if len(channel_order) <= 1:
        return mapping_config, summarize_playable_layout(mapping_config), False

    if preset not in (None, ""):
        bottom_note, top_note = parse_inclusive_note_range(str(preset))
        override_mapping = build_contiguous_mapping(mapping_config, bottom_note, top_note)
        override_summary = summarize_playable_layout(override_mapping)
        return override_mapping, override_summary, True

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


def find_octave_transpose_target(note, mapping_config):
    if map_note_to_channel(note, mapping_config) is not None:
        return note

    if mapping_config["mode"] == "collapse_all_notes_to_single_channel":
        return note

    supported_notes = get_mapping_note_numbers(mapping_config)
    if not supported_notes:
        return None

    same_pitch_class_candidates = [
        supported_note for supported_note in supported_notes if (supported_note % 12) == (note % 12)
    ]
    if not same_pitch_class_candidates:
        return None

    # Prefer the nearest playable octave. On exact ties, prefer the lower note
    # so the remap is stable and does not unexpectedly jump upward.
    return min(
        same_pitch_class_candidates,
        key=lambda candidate: (abs(candidate - note), 0 if candidate <= note else 1, candidate),
    )


def count_octave_transposed_playable_intervals(note_intervals, mapping_config):
    playable_count = 0
    note_target_cache = {}
    for interval in note_intervals:
        note = int(interval["note"])
        if note not in note_target_cache:
            note_target_cache[note] = find_octave_transpose_target(note, mapping_config)
        if note_target_cache[note] is not None:
            playable_count += 1
    return playable_count


def summarize_octave_shift_counts(shift_counts):
    if not shift_counts:
        return "no octave remapping was needed"

    parts = []
    for semitone_shift, count in sorted(shift_counts.items(), key=lambda item: (abs(item[0]), item[0])):
        direction = "up" if semitone_shift > 0 else "down"
        octave_count = abs(semitone_shift) // 12
        noun = "note event" if count == 1 else "note events"
        parts.append(f"{count} {noun} {direction} {octave_count} octave(s)")
    return ", ".join(parts)


def build_transpose_stats_from_scheduled_notes(scheduled_notes, skipped_for_timing=0):
    shift_counts = defaultdict(int)
    remapped_note_events = 0

    for note_event in scheduled_notes:
        source_note = int(note_event.get("source_note", note_event["note"]))
        input_note = int(note_event["note"])
        semitone_shift = input_note - source_note
        if semitone_shift == 0:
            continue
        remapped_note_events += 1
        shift_counts[semitone_shift] += 1

    return {
        "remapped_note_events": remapped_note_events,
        "shift_counts": dict(sorted(shift_counts.items())),
        "shift_summary": summarize_octave_shift_counts(shift_counts),
        "skipped_for_timing": skipped_for_timing,
    }


def describe_recognizability(playable_count, total_count):
    if total_count <= 0:
        return "no pitched note events were found"

    ratio = playable_count / total_count
    if ratio >= 0.9:
        return "very likely recognizable"
    if ratio >= 0.7:
        return "likely recognizable, but simplified"
    if ratio >= 0.4:
        return "partially recognizable"
    return "probably fragmentary"


def transpose_note_intervals_to_available_octaves(note_intervals, mapping_config):
    transposed = []
    remapped_note_events = 0
    shift_counts = defaultdict(int)
    note_target_cache = {}

    for interval in note_intervals:
        source_note = int(interval["note"])
        if source_note not in note_target_cache:
            note_target_cache[source_note] = find_octave_transpose_target(source_note, mapping_config)

        target_note = note_target_cache[source_note]
        if target_note is None:
            transposed.append(dict(interval))
            continue

        semitone_shift = target_note - source_note
        if semitone_shift != 0:
            remapped_note_events += 1
            shift_counts[semitone_shift] += 1

        transposed.append(
            {
                **interval,
                "source_note": interval.get("source_note", source_note),
                "note": target_note,
            }
        )

    return transposed, {
        "remapped_note_events": remapped_note_events,
        "shift_counts": dict(sorted(shift_counts.items())),
        "shift_summary": summarize_octave_shift_counts(shift_counts),
    }


def get_octave_transpose_candidate_notes(note, mapping_config):
    direct_channel = map_note_to_channel(note, mapping_config)
    if direct_channel is not None:
        return [int(note)]

    if mapping_config["mode"] == "collapse_all_notes_to_single_channel":
        return [int(note)]

    supported_notes = get_mapping_note_numbers(mapping_config)
    candidates = [supported_note for supported_note in supported_notes if (supported_note % 12) == (int(note) % 12)]
    return sorted(
        candidates,
        key=lambda candidate: (abs(candidate - int(note)), 0 if candidate <= int(note) else 1, candidate),
    )


def prompt_for_fit_mode(note_intervals, mapping_config, preset=None):
    range_info = analyze_note_range(note_intervals)
    total_note_count = len(note_intervals)
    strict_playable_count = count_playable_intervals(note_intervals, mapping_config, 0)
    transposed_playable_count = count_octave_transposed_playable_intervals(note_intervals, mapping_config)
    layout_summary = summarize_playable_layout(mapping_config)
    strict_recognizability = describe_recognizability(strict_playable_count, total_note_count)
    transpose_recognizability = describe_recognizability(transposed_playable_count, total_note_count)
    interactive = preset not in {"strict", "transpose", "cancel"}

    if interactive:
        print("\nMIDI pitch scan:")
        print(f"Detected MIDI note range: {range_info['range_label']}")
        print(f"Active playable layout: {layout_summary['label']}")
        print(
            f"Strict: {format_playable_count(strict_playable_count, total_note_count)}"
        )
        print(f"  Keeps the original pitches and skips anything outside your playable layout. Result: {strict_recognizability}.")
        print(
            f"Transpose by octave: {format_playable_count(transposed_playable_count, total_note_count)}"
        )
        print(
            "  Keeps already-playable notes where they are, and folds each out-of-range note into the nearest playable octave when that note exists in your layout. "
            f"Result: {transpose_recognizability}."
        )
        print("Cancel: stop here without converting or sending anything.")

    recommended_mode = "transpose" if transposed_playable_count > strict_playable_count else "strict"
    if preset in {"strict", "transpose", "cancel"}:
        choice = preset
        if choice == "strict" and strict_playable_count == 0:
            raise ValueError("Strict playback would result in 0 playable notes with the current layout.")
        if choice == "transpose" and transposed_playable_count == 0:
            raise ValueError("Transpose playback would still result in 0 playable notes with the current layout.")
    else:
        choice = None
    while True:
        if choice is None:
            choice = input(f"Choose strict, transpose, or cancel [{recommended_mode}]: ").strip().lower()
        if not choice:
            choice = recommended_mode
        if choice not in {"strict", "transpose", "cancel"}:
            print("Enter strict, transpose, or cancel.")
            choice = None
            continue
        if choice == "strict" and strict_playable_count == 0:
            print("Strict would play 0 notes with the current layout. Choose transpose, another range, or cancel.")
            choice = None
            continue
        if choice == "transpose" and transposed_playable_count == 0:
            print("Transpose would still play 0 notes with the current layout. Choose another range or cancel.")
            choice = None
            continue
        break

    return {
        "mode": choice,
        "source_range": range_info,
        "layout_summary": layout_summary,
        "strict_playable_count": strict_playable_count,
        "strict_summary": format_playable_count(strict_playable_count, total_note_count),
        "strict_recognizability": strict_recognizability,
        "transpose_playable_count": transposed_playable_count,
        "transpose_summary": format_playable_count(transposed_playable_count, total_note_count),
        "transpose_recognizability": transpose_recognizability,
    }


def describe_mapping(mapping_config, pca_config=None):
    mode = mapping_config["mode"]
    channel_labels = mapping_config.get("channel_labels", {})
    note_labels = mapping_config.get("note_labels", {})
    if pca_config is None:
        pca_config = {"board_addresses": [0x40]}

    if mode == "collapse_all_notes_to_single_channel":
        channel = int(mapping_config["single_channel"])
        label = channel_labels.get(str(channel), f"Channel {channel}")
        return [
            "Single-solenoid test mode",
            f"All MIDI notes collapse to {describe_global_channel(channel, pca_config)} ({label})",
            "This is useful for force and timing tuning with one physical solenoid.",
        ]

    note_map = mapping_config.get("note_to_channel", {})
    lines = ["Explicit note-to-channel mode"]
    for note, channel in sorted(note_map.items(), key=lambda item: int(item[0])):
        label = channel_labels.get(str(channel), f"Channel {channel}")
        note_label = note_labels.get(str(note), midi_note_name(int(note)))
        lines.append(
            f"MIDI note {note} ({note_label}) -> {describe_global_channel(channel, pca_config)} ({label})"
        )
    return lines


def build_unmapped_note_lines(unmapped_note_counts, limit=8):
    lines = []
    for note, count in sorted(unmapped_note_counts.items(), key=lambda item: (-item[1], item[0]))[:limit]:
        lines.append(f"{midi_note_name(note)} ({note}): {count}")
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
    """Map notes to channels and prevent impossible overlap on each solenoid.

    A real solenoid cannot play two notes at once on the same channel. If a MIDI
    file retriggers a key before the previous actuation has released, this pass
    shortens/rearms the previous event and delays the next event just enough for
    the hardware to recover.
    """
    mapping_config = config["mapping"]

    notes_by_channel = defaultdict(list)
    unmapped_notes = 0
    unmapped_note_counts = defaultdict(int)

    for interval in note_intervals:
        channel = map_note_to_channel(interval["note"], mapping_config)
        if channel is None:
            unmapped_notes += 1
            unmapped_note_counts[int(interval["note"])] += 1
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
        "unmapped_note_counts": {str(note): count for note, count in sorted(unmapped_note_counts.items())},
        "channels_used": sorted(notes_by_channel),
    }


def schedule_notes_with_octave_transpose(note_intervals, config):
    """Schedule notes while choosing octave-fold targets that minimize timing damage.

    Exact in-range notes stay on their mapped key. Out-of-range notes can choose
    among playable same-pitch-class targets across the available octave(s). If a
    remapped note would have to be delayed, it is skipped rather than shifting
    the beat later in time.
    """
    mapping_config = config["mapping"]

    channel_states = {}
    scheduled_notes = []
    forced_retriggers = 0
    delayed_notes = 0
    unmapped_notes = 0
    unmapped_note_counts = defaultdict(int)
    channels_used = set()
    skipped_transposed_notes_for_timing = 0

    def get_channel_state(channel):
        if channel not in channel_states:
            channel_states[channel] = {
                "active_note": None,
                "last_off_ms": -1_000_000,
            }
        return channel_states[channel]

    def evaluate_candidate(interval, target_note, channel):
        channel_actuation = resolve_channel_actuation(channel, config)
        release_delay_ms = int(channel_actuation["release_delay_ms"])
        minimum_rearm_gap_ms = int(channel_actuation["minimum_rearm_gap_ms"])
        retrigger_gap_ms = int(channel_actuation["retrigger_gap_ms"])

        state = get_channel_state(channel)
        active_note = state["active_note"]
        last_off_ms = state["last_off_ms"]
        naturally_closed_note = None
        truncated_active_end_ms = None
        forced_retrigger = False
        gap_ms = minimum_rearm_gap_ms

        if active_note and interval["start_ms"] >= active_note["end_ms"]:
            naturally_closed_note = active_note
            last_off_ms = active_note["end_ms"] + release_delay_ms
            active_note = None

        if active_note and interval["start_ms"] < active_note["end_ms"]:
            forced_retrigger = True
            truncated_active_end_ms = max(active_note["start_ms"] + 1, interval["start_ms"])
            last_off_ms = truncated_active_end_ms + release_delay_ms
            gap_ms = retrigger_gap_ms

        start_ms = max(interval["start_ms"], last_off_ms + gap_ms)
        delay_ms = start_ms - interval["start_ms"]

        return {
            "channel": channel,
            "target_note": target_note,
            "start_ms": start_ms,
            "delay_ms": delay_ms,
            "forced_retrigger": forced_retrigger,
            "naturally_closed_note": naturally_closed_note,
            "truncated_active_end_ms": truncated_active_end_ms,
        }

    for interval in sorted(note_intervals, key=lambda item: (item["start_ms"], item["note"], item["end_ms"])):
        source_note = int(interval.get("source_note", interval["note"]))
        candidate_notes = get_octave_transpose_candidate_notes(source_note, mapping_config)
        if not candidate_notes:
            unmapped_notes += 1
            unmapped_note_counts[source_note] += 1
            continue

        candidate_evaluations = []
        for target_note in candidate_notes:
            channel = map_note_to_channel(target_note, mapping_config)
            if channel is None:
                continue
            candidate_evaluations.append(evaluate_candidate(interval, int(target_note), int(channel)))

        if not candidate_evaluations:
            unmapped_notes += 1
            unmapped_note_counts[source_note] += 1
            continue

        best_candidate = min(
            candidate_evaluations,
            key=lambda candidate: (
                candidate["delay_ms"],
                1 if candidate["forced_retrigger"] else 0,
                abs(candidate["target_note"] - source_note),
                candidate["target_note"],
                candidate["channel"],
            ),
        )

        remapped_note = best_candidate["target_note"] != source_note
        if remapped_note and best_candidate["delay_ms"] > 0:
            skipped_transposed_notes_for_timing += 1
            unmapped_notes += 1
            unmapped_note_counts[source_note] += 1
            continue

        state = get_channel_state(best_candidate["channel"])
        channel_actuation = resolve_channel_actuation(best_candidate["channel"], config)
        release_delay_ms = int(channel_actuation["release_delay_ms"])

        if best_candidate["naturally_closed_note"] is not None:
            scheduled_notes.append(best_candidate["naturally_closed_note"])
            state["last_off_ms"] = best_candidate["naturally_closed_note"]["end_ms"] + release_delay_ms
            state["active_note"] = None

        if best_candidate["forced_retrigger"] and state["active_note"] is not None:
            state["active_note"]["end_ms"] = best_candidate["truncated_active_end_ms"]
            scheduled_notes.append(state["active_note"])
            state["last_off_ms"] = state["active_note"]["end_ms"] + release_delay_ms
            state["active_note"] = None
            forced_retriggers += 1

        original_duration_ms = max(1, interval["end_ms"] - interval["start_ms"])
        start_ms = best_candidate["start_ms"]
        if start_ms > interval["start_ms"]:
            delayed_notes += 1

        active_note = {
            **interval,
            "source_note": source_note,
            "note": best_candidate["target_note"],
            "channel": best_candidate["channel"],
            "original_start_ms": interval["start_ms"],
            "original_end_ms": interval["end_ms"],
            "original_duration_ms": original_duration_ms,
            "start_ms": start_ms,
            "end_ms": max(start_ms + 1, start_ms + original_duration_ms),
        }
        state["active_note"] = active_note
        channels_used.add(best_candidate["channel"])

    for channel, state in channel_states.items():
        if state["active_note"] is not None:
            scheduled_notes.append(state["active_note"])
            channels_used.add(channel)

    scheduled_notes.sort(key=lambda item: (item["start_ms"], item["channel"], item["note"]))
    return scheduled_notes, {
        "forced_retriggers": forced_retriggers,
        "delayed_notes": delayed_notes,
        "unmapped_notes": unmapped_notes,
        "unmapped_note_counts": {str(note): count for note, count in sorted(unmapped_note_counts.items())},
        "channels_used": sorted(channels_used),
        "skipped_transposed_notes_for_timing": skipped_transposed_notes_for_timing,
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
    """Convert scheduled notes into low-level PWM events.

    Each playable note becomes a strong strike, an optional lower-power hold,
    and a release event that sets the PCA9685 channel back to zero.
    """
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
    board_addresses = get_pca_board_addresses(pca_config)
    padded_board_addresses = list(board_addresses[:MAX_PCA9685_BOARDS])
    while len(padded_board_addresses) < MAX_PCA9685_BOARDS:
        padded_board_addresses.append(padded_board_addresses[0])
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
        f"// Recognizability estimate: {metadata['recognizability_summary']}",
        f"// Strict coverage: {metadata['strict_playable_summary']}",
        f"// Octave transpose coverage: {metadata['transpose_playable_summary']}",
        f"// Octave transpose remap summary: {metadata['transpose_shift_summary']}",
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

    if metadata["unmapped_note_lines"]:
        lines.extend(
            [
                "",
                "// Most skipped notes in this export:",
            ]
        )
        for line in metadata["unmapped_note_lines"]:
            lines.append(f"//   {line}")

    lines.extend(
        [
            "",
            f"const uint8_t SONG_PCA9685_BOARD_COUNT = {len(board_addresses)}u;",
            f"const uint8_t SONG_PCA9685_MAX_BOARD_COUNT = {MAX_PCA9685_BOARDS}u;",
            "const uint8_t SONG_PCA9685_BOARD_ADDRESSES[SONG_PCA9685_MAX_BOARD_COUNT] = {",
        ]
    )

    for address in padded_board_addresses:
        lines.append(f"  0x{int(address):02X},")

    lines.extend(
        [
            "};",
            f"const uint8_t SONG_PCA9685_I2C_ADDRESS = 0x{int(board_addresses[0]):02X};",
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
            "  uint8_t  channel; // global channel across every PCA9685 board",
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


def build_channel_lines(channels_used, mapping_config, pca_config):
    channel_labels = mapping_config.get("channel_labels", {})
    lines = []
    for channel in channels_used:
        label = channel_labels.get(str(channel), f"Channel {channel}")
        lines.append(f"{describe_global_channel(channel, pca_config)}: {label}")
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


def list_serial_ports():
    if serial is None or list_ports is None:
        raise RuntimeError("pyserial is not installed. Install it with 'pip install pyserial'.")

    ports = list(list_ports.comports())
    if not ports:
        print("No serial devices were found.")
        return

    print("Available serial ports:")
    for port in ports:
        description = getattr(port, "description", "")
        manufacturer = getattr(port, "manufacturer", "")
        print(f"  {port.device} - {description} {manufacturer}".strip())


def parse_ready_response(response):
    match = re.match(r"^READY\s+(?P<version>\d+)\s+BUFFER\s+(?P<capacity>\d+)$", response.strip())
    if not match:
        raise RuntimeError(f"Unexpected Arduino handshake: {response}")
    return {
        "protocol_version": int(match.group("version")),
        "buffer_capacity": int(match.group("capacity")),
    }


def parse_runtime_key_values(response):
    fields = {}
    for token in response.strip().split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        fields[key] = value
    return fields


def parse_status_response(response):
    parts = response.strip().split()
    if len(parts) < 2 or parts[0] != "STATUS":
        raise RuntimeError(f"Unexpected STATUS response: {response}")

    fields = parse_runtime_key_values(response)
    fields["state"] = parts[1]
    for key in ("recv", "played", "buffered", "free", "total"):
        if key in fields:
            fields[key] = int(fields[key])
    return fields


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
        if response.startswith("ERROR "):
            raise RuntimeError(f"Arduino runtime returned an error for '{command}': {response}")
        if any(response.startswith(prefix) for prefix in expected_prefixes):
            return response


def send_event_chunk(connection, events, start_index, chunk_size):
    end_index = min(len(events), start_index + chunk_size)
    for event in events[start_index:end_index]:
        command = f"EVENT {event['dt_ms']} {event['channel']} {event['pwm']}"
        connection.write((command + "\n").encode("ascii"))
    connection.flush()
    return end_index


def wait_for_playback_done(connection, timeout_seconds):
    deadline = time.time() + timeout_seconds
    while True:
        response = read_serial_response(connection, deadline)
        if response.startswith("ERROR "):
            raise RuntimeError(f"Arduino runtime returned an error while waiting for playback completion: {response}")
        if response.startswith("OK PLAYBACK_DONE"):
            return response


def stream_song_to_arduino(payload, deployment_config):
    """Stream generated events to the fixed Arduino runtime over serial.

    The Uno cannot store a large song in RAM, so Python fills the Arduino's small
    event buffer, starts playback, then keeps topping up the buffer while the
    sketch plays earlier events.
    """
    serial_config = deployment_config.get("serial_runtime", {})
    if not serial_config.get("enabled", True):
        return None

    port = choose_serial_port(serial_config)
    baud_rate = int(serial_config.get("baud_rate", 115200))
    startup_wait_ms = int(serial_config.get("startup_wait_ms", 2500))
    wait_for_finish = bool(serial_config.get("wait_for_finish", True))
    status_poll_ms = int(serial_config.get("status_poll_ms", 25))
    events = payload["events"]

    playback_done_response = None
    with serial.Serial(port=port, baudrate=baud_rate, timeout=0.5) as connection:
        try:
            time.sleep(startup_wait_ms / 1000.0)
            connection.reset_input_buffer()
            connection.reset_output_buffer()

            ready_response = send_serial_command(connection, "HELLO", ("READY",), timeout_seconds=4.0)
            ready_info = parse_ready_response(ready_response)
            send_serial_command(connection, "STOP", ("OK STOPPED",), timeout_seconds=2.0)
            send_serial_command(connection, "CLEAR", ("OK CLEARED",), timeout_seconds=2.0)
            begin_response = send_serial_command(connection, f"BEGIN {len(events)}", ("OK BEGIN",), timeout_seconds=2.0)
            begin_fields = parse_runtime_key_values(begin_response)
            buffer_capacity = int(begin_fields.get("capacity", ready_info["buffer_capacity"]))

            sent_event_count = 0
            if events:
                sent_event_count = send_event_chunk(connection, events, sent_event_count, buffer_capacity)
                send_serial_command(connection, "COMMIT", ("OK ACCEPTED",), timeout_seconds=2.0)

            play_response = send_serial_command(connection, "PLAY", ("OK PLAYING",), timeout_seconds=2.0)

            while sent_event_count < len(events):
                status_response = send_serial_command(connection, "STATUS", ("STATUS",), timeout_seconds=2.0)
                status_fields = parse_status_response(status_response)
                free_slots = int(status_fields.get("free", 0))
                if free_slots <= 0:
                    time.sleep(status_poll_ms / 1000.0)
                    continue

                sent_event_count = send_event_chunk(connection, events, sent_event_count, free_slots)
                send_serial_command(connection, "COMMIT", ("OK ACCEPTED",), timeout_seconds=2.0)

            if wait_for_finish:
                total_runtime_seconds = sum(event["dt_ms"] for event in events) / 1000.0
                playback_done_response = wait_for_playback_done(
                    connection,
                    timeout_seconds=max(10.0, total_runtime_seconds + 15.0),
                )
        except Exception:
            # If Python loses the serial connection mid-song, make a best-effort
            # stop command so a solenoid is not left energized.
            try:
                connection.write(b"ALL_OFF\n")
                connection.flush()
            except Exception:
                pass
            raise

    manifest_payload = {
        "port": port,
        "baud_rate": baud_rate,
        "source_midi": payload["source_midi"],
        "output_header": payload["output_header"],
        "protocol_version": ready_info["protocol_version"],
        "buffer_capacity": buffer_capacity,
        "sent_event_count": sent_event_count,
        "stream_response": play_response,
        "playback_done_response": playback_done_response,
    }
    STREAM_MANIFEST_PATH.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")

    return manifest_payload


def sync_arduino_ide_runtime(header_text, deployment_config):
    sync_config = deployment_config.get("arduino_ide_sync", {})
    if not sync_config.get("enabled", False):
        return None

    sketch_path_raw = str(sync_config.get("sketch_path", "")).strip()
    if not sketch_path_raw:
        return {
            "sync_skipped": "No Arduino IDE sketch path is configured.",
        }

    sketch_path = Path(sketch_path_raw)
    generated_dir_name = sync_config.get("generated_dir_name", "generated")
    generated_dir = sketch_path.parent / generated_dir_name

    if not sketch_path.parent.exists():
        return {
            "sketch_path": sketch_path,
            "active_header_path": generated_dir / ACTIVE_HEADER_NAME,
            "sync_skipped": "Configured Arduino IDE sketch folder does not exist on this machine.",
        }

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


def run_conversion_workflow(
    selected_midi_source,
    selection_reason,
    active_channel_count=None,
    preferred_range=None,
    preferred_fit_mode=None,
    preferred_tempo=None,
    port=None,
    dry_run=False,
    export_only=False,
    allow_prompts=True,
    config=None,
    user_preferences=None,
    deployment_config=None,
    reporter=print,
):
    if config is None:
        config = load_config()
    if user_preferences is None:
        user_preferences = load_user_preferences()
    if deployment_config is None:
        deployment_config = load_deployment_config()
    else:
        deployment_config = copy.deepcopy(deployment_config)

    if port:
        deployment_config.setdefault("serial_runtime", {})
        deployment_config["serial_runtime"]["preferred_port"] = port

    selected_midi_source = Path(selected_midi_source).expanduser()
    selected_midi, was_imported = import_midi_to_library(selected_midi_source)

    try:
        mid = MidiFile(str(selected_midi))
    except Exception as error:
        raise RuntimeError(
            f"'{selected_midi.name}' could not be read as a MIDI file. If it came from a ZIP download, unzip it first."
        ) from error

    tempo_info = scan_tempo_info(mid)
    note_intervals, interval_stats = extract_note_intervals(mid)
    if not note_intervals:
        raise ValueError("No note_on events were found in the selected MIDI file.")

    base_mapping, active_channel_sequence = apply_active_channel_limit(
        config["mapping"],
        config["pca9685"],
        active_channel_count=active_channel_count,
    )
    hardware_channel_summary = summarize_active_channel_sequence(active_channel_sequence, config["pca9685"])

    if preferred_range is None:
        preferred_range = user_preferences["playback"].get("default_playable_range", "")
    if allow_prompts or preferred_range not in (None, ""):
        effective_mapping, playable_layout_summary, mapping_overridden = prompt_for_playable_range(
            base_mapping,
            preset=preferred_range,
        )
    else:
        effective_mapping = copy.deepcopy(base_mapping)
        playable_layout_summary = summarize_playable_layout(effective_mapping)
        mapping_overridden = False
    effective_config = dict(config)
    effective_config["mapping"] = effective_mapping

    if preferred_fit_mode is None:
        preferred_fit_mode = user_preferences["playback"].get("default_fit_mode", "prompt")
        if preferred_fit_mode == "prompt":
            preferred_fit_mode = None
    if not allow_prompts and preferred_fit_mode in (None, ""):
        preferred_fit_mode = "transpose"
    fit_selection = prompt_for_fit_mode(note_intervals, effective_mapping, preset=preferred_fit_mode)
    if fit_selection["mode"] == "cancel":
        report_line(reporter, "Cancelled before conversion.")
        return {"cancelled": True}

    if fit_selection["mode"] == "strict":
        transpose_stats = {
            "remapped_note_events": 0,
            "shift_counts": {},
            "shift_summary": "no octave remapping was applied",
            "skipped_for_timing": 0,
        }

    if preferred_tempo is None:
        preferred_tempo = user_preferences["playback"].get("default_tempo", "")
    if allow_prompts or preferred_tempo not in (None, ""):
        tempo_override = prompt_for_tempo_override(tempo_info["first_bpm"], preset=preferred_tempo)
    else:
        tempo_override = parse_tempo_override_input("", tempo_info["first_bpm"])
    scaled_intervals = scale_intervals(note_intervals, tempo_override["scale"])
    if fit_selection["mode"] == "strict":
        scheduled_notes, scheduling_stats = schedule_notes(scaled_intervals, effective_config)
    else:
        scheduled_notes, scheduling_stats = schedule_notes_with_octave_transpose(scaled_intervals, effective_config)
        transpose_stats = build_transpose_stats_from_scheduled_notes(
            scheduled_notes,
            skipped_for_timing=scheduling_stats.get("skipped_transposed_notes_for_timing", 0),
        )
    if not scheduled_notes:
        raise ValueError(
            "No playable notes remained after applying the selected fit mode. Try transpose, a different playable range, or another song."
        )
    timeline, scheduled_note_metadata, playback_stats = build_playback_events(
        scheduled_notes, effective_config
    )
    delta_events = convert_to_delta_events(timeline)
    unmapped_note_lines = build_unmapped_note_lines(
        {int(note): count for note, count in scheduling_stats["unmapped_note_counts"].items()}
    )
    selected_playable_count = len(scheduled_notes)
    recognizability_summary = describe_recognizability(selected_playable_count, len(note_intervals))

    header_path, output_version = next_header_path(HEADER_DIR, selected_midi)
    output_version_label = "base" if output_version == 0 else f"v{output_version}"
    mapping_lines = describe_mapping(effective_config["mapping"], effective_config["pca9685"])
    channel_lines = build_channel_lines(
        scheduling_stats["channels_used"],
        effective_config["mapping"],
        effective_config["pca9685"],
    )
    actuation_lines = build_actuation_lines(scheduling_stats["channels_used"], effective_config)

    if fit_selection["mode"] == "strict":
        fit_mode_label = "strict (original pitches, skip out-of-range notes)"
    else:
        if transpose_stats["remapped_note_events"] == 0:
            fit_mode_label = "transpose by octave (all playable notes were already inside the active layout)"
        else:
            fit_mode_label = (
                "transpose by octave "
                f"({transpose_stats['remapped_note_events']} note events remapped; {transpose_stats['shift_summary']})"
            )

    metadata = {
        "project_mode": config["project_mode"],
        "output_version_label": output_version_label,
        "original_bpm": tempo_info["first_bpm"],
        "tempo_label": tempo_override["label"],
        "effective_bpm": tempo_override["target_bpm"],
        "tempo_change_count": tempo_info["tempo_change_count"],
        "active_hardware_channel_count": len(active_channel_sequence),
        "active_hardware_channel_summary": hardware_channel_summary,
        "source_range_label": fit_selection["source_range"]["range_label"],
        "playable_layout_label": playable_layout_summary["label"],
        "fit_mode": fit_selection["mode"],
        "fit_mode_label": fit_mode_label,
        "transpose_semitones": 0,
        "transpose_strategy": "per_note_octave_fold",
        "transpose_remapped_note_events": transpose_stats["remapped_note_events"],
        "transpose_shift_counts": transpose_stats["shift_counts"],
        "transpose_shift_summary": transpose_stats["shift_summary"],
        "transpose_skipped_for_timing": transpose_stats["skipped_for_timing"],
        "strict_playable_count": fit_selection["strict_playable_count"],
        "strict_playable_summary": fit_selection["strict_summary"],
        "transpose_playable_count": fit_selection["transpose_playable_count"],
        "transpose_playable_summary": fit_selection["transpose_summary"],
        "mapping_override_used": mapping_overridden,
        "selection_reason": selection_reason,
        "recognizability_summary": recognizability_summary,
        "unmapped_note_lines": unmapped_note_lines,
        "source_note_count": len(note_intervals),
        "scheduled_note_count": len(scheduled_notes),
        "event_count": len(delta_events),
        "forced_retriggers": scheduling_stats["forced_retriggers"],
        "delayed_notes": scheduling_stats["delayed_notes"],
        "unmapped_notes": scheduling_stats["unmapped_notes"],
        "unmapped_note_counts": scheduling_stats["unmapped_note_counts"],
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

    report_line(reporter, "")
    report_line(reporter, f"Selected file: {selected_midi.name}")
    report_line(reporter, f"Chosen because: {selection_reason}")
    report_line(reporter, f"Original source path: {selected_midi_source}")
    if was_imported:
        report_line(reporter, f"Imported into project library: {selected_midi}")
    report_line(reporter, f"Type: {mid.type}")
    report_line(reporter, f"Ticks per beat: {mid.ticks_per_beat}")
    report_line(reporter, f"Number of tracks: {len(mid.tracks)}")
    report_line(reporter, f"Tempo events found: {tempo_info['tempo_change_count']}")
    report_line(reporter, f"Active hardware: {hardware_channel_summary}")
    report_line(reporter, f"Detected MIDI note range: {fit_selection['source_range']['range_label']}")
    report_line(reporter, f"Playable layout: {playable_layout_summary['label']}")
    report_line(reporter, f"Strict coverage: {fit_selection['strict_summary']}")
    report_line(reporter, f"Transpose coverage: {fit_selection['transpose_summary']}")
    report_line(reporter, f"Fit mode used: {fit_mode_label}")
    report_line(reporter, f"Transpose remap summary: {transpose_stats['shift_summary']}")
    if transpose_stats["skipped_for_timing"] > 0:
        report_line(
            reporter,
            f"Transpose timing guard skipped {transpose_stats['skipped_for_timing']} remapped note events to keep the beat on time.",
        )
    report_line(reporter, f"Recognizability estimate: {recognizability_summary}")
    report_line(reporter, f"Range override used: {'yes' if mapping_overridden else 'no'}")
    if interval_stats["percussion_events_skipped"] > len(note_intervals):
        report_line(
            reporter,
            "Percussion warning: this file appears to contain more percussion events than pitched note events.",
        )
    report_line(reporter, "Mapping summary:")
    for line in mapping_lines:
        report_line(reporter, f"  {line}")
    report_line(reporter, "Channel summary:")
    for line in channel_lines:
        report_line(reporter, f"  {line}")
    report_line(reporter, "Actuation summary:")
    for line in actuation_lines:
        report_line(reporter, f"  {line}")
    if unmapped_note_lines:
        report_line(reporter, "Most skipped notes:")
        for line in unmapped_note_lines:
            report_line(reporter, f"  {line}")

    json_path = None
    active_header_path = None
    active_json_path = None
    deployment_paths = None
    payload = None
    if dry_run:
        report_line(reporter, "")
        report_line(reporter, "Dry run complete. No files were written and nothing was sent over USB.")
    else:
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
    if payload is not None and not export_only:
        stream_manifest = stream_song_to_arduino(payload, deployment_config)

    if not dry_run:
        report_line(reporter, "")
        report_line(reporter, "Conversion complete.")
        report_line(reporter, f"Versioned header: {header_path.relative_to(REPO_ROOT)}")
        report_line(reporter, f"Active Arduino header: {active_header_path.relative_to(REPO_ROOT)}")
        report_line(reporter, f"Versioned metadata: {json_path.relative_to(REPO_ROOT)}")
        report_line(reporter, f"Active metadata: {active_json_path.relative_to(REPO_ROOT)}")
        if deployment_paths is not None:
            if "sketch_path" in deployment_paths:
                report_line(reporter, f"Synced Arduino IDE sketch: {deployment_paths['sketch_path']}")
            if "active_header_path" in deployment_paths:
                report_line(reporter, f"Synced Arduino IDE active header: {deployment_paths['active_header_path']}")
            if "sync_skipped" in deployment_paths:
                report_line(reporter, f"Arduino IDE sync skipped: {deployment_paths['sync_skipped']}")
            if "sync_error" in deployment_paths:
                report_line(reporter, f"Arduino IDE sync warning: {deployment_paths['sync_error']}")
        if stream_manifest is not None:
            report_line(reporter, f"USB playback sent on port: {stream_manifest['port']}")
            report_line(
                reporter,
                f"Streamed {stream_manifest['sent_event_count']} events with runtime protocol "
                f"v{stream_manifest['protocol_version']} using a buffer capacity of {stream_manifest['buffer_capacity']}.",
            )
        report_line(reporter, f"Output header version: {output_version_label}")
        report_line(reporter, f"Base tempo: {tempo_info['first_bpm']:.2f} BPM")
        report_line(reporter, f"Effective output tempo: {tempo_override['target_bpm']:.2f} BPM")
        report_line(reporter, f"Input note intervals: {len(note_intervals)}")
        report_line(reporter, f"Scheduled notes: {len(scheduled_notes)}")
        report_line(reporter, f"Generated events: {len(delta_events)}")
        report_line(reporter, f"Forced retriggers: {scheduling_stats['forced_retriggers']}")
        report_line(reporter, f"Delayed notes: {scheduling_stats['delayed_notes']}")
        report_line(reporter, f"Hold events: {playback_stats['hold_events']}")
        report_line(reporter, f"Strike-only notes: {playback_stats['strike_only_notes']}")
        report_line(reporter, f"Unmapped notes skipped: {scheduling_stats['unmapped_notes']}")
        report_line(reporter, f"Unmatched note_off events ignored: {interval_stats['unmatched_note_offs']}")
        report_line(reporter, f"Dangling note_on events auto-closed: {interval_stats['dangling_note_ons_closed']}")
        report_line(reporter, f"Percussion note events ignored: {interval_stats['percussion_events_skipped']}")

    return {
        "cancelled": False,
        "selected_midi": selected_midi,
        "selected_midi_source": selected_midi_source,
        "selection_reason": selection_reason,
        "active_channel_sequence": active_channel_sequence,
        "was_imported": was_imported,
        "metadata": metadata,
        "playable_layout_summary": playable_layout_summary,
        "tempo_override": tempo_override,
        "fit_selection": fit_selection,
        "output_version_label": output_version_label,
        "header_path": header_path,
        "json_path": json_path,
        "active_header_path": active_header_path,
        "active_json_path": active_json_path,
        "deployment_paths": deployment_paths,
        "payload": payload,
        "stream_manifest": stream_manifest,
    }


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Convert a MIDI file for the autonomous piano player and optionally send it over USB."
    )
    parser.add_argument("--song", help="Full path to a MIDI file to use.")
    parser.add_argument("--project-song", help="Filename of a MIDI already in songs/midi.")
    parser.add_argument(
        "--choose-library",
        action="store_true",
        help="Choose a MIDI from songs/midi instead of auto-using the newest download.",
    )
    parser.add_argument(
        "--play-latest",
        action="store_true",
        help="Explicitly use the newest .mid/.midi file in the Windows Downloads folder.",
    )
    parser.add_argument(
        "--active-channels",
        help="How many hardware solenoid channels are currently installed. Leave unset to use the saved mapping count.",
    )
    parser.add_argument(
        "--fit-mode",
        choices=("strict", "transpose", "cancel"),
        help="Choose how out-of-range notes are handled without prompting.",
    )
    parser.add_argument(
        "--range",
        dest="playable_range",
        help="Override the playable note range with an inclusive range such as C4-B4 or 60-71.",
    )
    parser.add_argument(
        "--tempo",
        help="Override the tempo without prompting. Use a BPM like 140 or a multiplier like 0.85x.",
    )
    parser.add_argument(
        "--port",
        help="Use a specific serial port such as COM4 instead of auto-detecting the Arduino.",
    )
    parser.add_argument(
        "--list-ports",
        action="store_true",
        help="List detected serial ports and exit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze the MIDI and print the plan, but do not write output files or send USB playback.",
    )
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Convert and write files, but do not send the song over USB.",
    )
    return parser


def main():
    # High-level pipeline:
    # choose MIDI -> analyze/fit -> schedule hardware events -> write outputs ->
    # optionally stream the events to the Arduino runtime.
    args = build_arg_parser().parse_args()
    if args.list_ports:
        list_serial_ports()
        return

    config = load_config()
    user_preferences = load_user_preferences()
    deployment_config = load_deployment_config()
    if args.port:
        deployment_config.setdefault("serial_runtime", {})
        deployment_config["serial_runtime"]["preferred_port"] = args.port

    selected_midi_source, selection_reason = choose_input_midi(args, user_preferences)
    run_conversion_workflow(
        selected_midi_source=selected_midi_source,
        selection_reason=selection_reason,
        active_channel_count=args.active_channels,
        preferred_range=args.playable_range,
        preferred_fit_mode=args.fit_mode,
        preferred_tempo=args.tempo,
        port=args.port,
        dry_run=args.dry_run,
        export_only=args.export_only,
        allow_prompts=True,
        config=config,
        user_preferences=user_preferences,
        deployment_config=deployment_config,
        reporter=print,
    )


if __name__ == "__main__":
    try:
        main()
    except (EOFError, FileNotFoundError, RuntimeError, TimeoutError, ValueError, OSError) as error:
        print(f"\nUnable to continue: {error}")
        raise SystemExit(1)
