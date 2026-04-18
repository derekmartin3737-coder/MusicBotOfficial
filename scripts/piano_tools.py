"""Calibration and debug tools for the solenoid keyboard.

The normal player uses scripts/play_piano.py. This file is for hardware bring-up:
checking the serial connection, firing channels safely one at a time, saving a
note-to-channel calibration map, and tuning one channel's strike/hold values.
"""

import argparse
import copy
import json
import time
from collections import defaultdict
from pathlib import Path

import convert_midi as engine

CALIBRATION_REPORT_PATH = engine.METADATA_DIR / "calibration_report.json"
CALIBRATION_REPORT_TEXT_PATH = engine.METADATA_DIR / "calibration_report.txt"


def build_calibration_pulse(actuation):
    """Build a conservative test pulse from the configured actuation limits."""
    strike_pwm = int(round((int(actuation["strike_min_pwm"]) + int(actuation["strike_max_pwm"])) / 2))
    hold_pwm = int(round((int(actuation["hold_min_pwm"]) + int(actuation["hold_max_pwm"])) / 2))
    return {
        "strike_pwm": strike_pwm,
        "hold_pwm": hold_pwm,
        "strike_ms": int(actuation["strike_ms"]),
        "hold_ms": max(120, int(actuation["strike_ms"]) * 3),
        "release_ms": 240,
    }


def open_runtime_connection(port_override=None):
    """Connect to the already-uploaded MusicBotOfficial Arduino runtime."""
    deployment_config = engine.load_deployment_config()
    serial_config = dict(deployment_config.get("serial_runtime", {}))
    if port_override:
        serial_config["preferred_port"] = port_override

    port = engine.choose_serial_port(serial_config)
    baud_rate = int(serial_config.get("baud_rate", 115200))
    startup_wait_ms = int(serial_config.get("startup_wait_ms", 2500))

    if engine.serial is None:
        raise RuntimeError("pyserial is not installed. Install it with 'pip install -r requirements.txt'.")

    connection = engine.serial.Serial(port=port, baudrate=baud_rate, timeout=0.5)
    time.sleep(startup_wait_ms / 1000.0)
    connection.reset_input_buffer()
    connection.reset_output_buffer()

    ready_response = engine.send_serial_command(connection, "HELLO", ("READY",), timeout_seconds=4.0)
    ready_info = engine.parse_ready_response(ready_response)
    ready_info["i2c_info"] = None
    ready_info["i2c_warning"] = None
    try:
        i2c_response = engine.send_serial_command(connection, "I2C", ("I2C",), timeout_seconds=2.0)
    except RuntimeError as error:
        if "UNKNOWN_COMMAND" not in str(error):
            raise
    else:
        ready_info["i2c_info"] = engine.parse_i2c_response(i2c_response)
        ready_info["i2c_warning"] = engine.build_i2c_mismatch_warning(ready_info["i2c_info"])
    engine.send_serial_command(connection, "STOP", ("OK STOPPED",), timeout_seconds=2.0)
    engine.send_serial_command(connection, "CLEAR", ("OK CLEARED",), timeout_seconds=2.0)
    return connection, port, ready_info


def fire_channel(connection, channel, pulse):
    """Ask the Arduino runtime to fire one PCA9685 channel for calibration."""
    command = (
        f"FIRE {channel} {pulse['strike_pwm']} {pulse['hold_pwm']} "
        f"{pulse['strike_ms']} {pulse['hold_ms']} {pulse['release_ms']}"
    )
    return engine.send_serial_command(connection, command, ("OK FIRED",), timeout_seconds=5.0)


def save_calibrated_mapping(mapping, report_payload):
    # The calibrated mapping is intentionally separate from piano_config.json so
    # each machine can save its own wiring without changing the repo default.
    engine.CALIBRATED_MAPPING_PATH.write_text(
        json.dumps({"mapping": mapping, "report": report_payload}, indent=2),
        encoding="utf-8",
    )
    CALIBRATION_REPORT_PATH.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    lines = [
        "Autonomous Piano Calibration Report",
        "",
        f"Port: {report_payload['port']}",
        f"Protocol version: {report_payload['protocol_version']}",
        f"Mode: {report_payload['mode']}",
        f"Saved mapping: {engine.CALIBRATED_MAPPING_PATH.relative_to(engine.REPO_ROOT)}",
        "",
        "Channel to note mapping:",
    ]
    for line in report_payload["mapping_lines"]:
        lines.append(f"  {line}")

    CALIBRATION_REPORT_TEXT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_mapping_lines(mapping):
    lines = []
    note_to_channel = mapping.get("note_to_channel", {})
    channel_labels = mapping.get("channel_labels", {})
    pca_config = engine.load_config()["pca9685"]
    for note, channel in sorted(note_to_channel.items(), key=lambda item: int(item[0])):
        channel_label = channel_labels.get(str(channel), f"Channel {channel}")
        lines.append(
            f"{engine.midi_note_name(int(note))} ({note}) -> {engine.describe_global_channel(channel, pca_config)} ({channel_label})"
        )
    return lines


def build_calibration_config(base_config, active_channel_count):
    """Prepare calibration to walk the active global channels in raw hardware order.

    Calibration should not inherit a stale saved note order from an older wiring
    map. If the user says there are N active channels, test global channels
    0..N-1 so every PCA board/channel combination is unambiguous.
    """
    active_count = engine.parse_active_channel_count(active_channel_count, base_config["pca9685"])
    active_sequence = list(range(active_count))

    config = copy.deepcopy(base_config)
    mapping = config["mapping"]
    mapping["channel_sequence"] = active_sequence

    if mapping.get("mode") == "explicit_note_map":
        active_channels = set(active_sequence)
        note_to_channel = {
            str(note): int(channel)
            for note, channel in mapping.get("note_to_channel", {}).items()
            if int(channel) in active_channels
        }
        mapping["note_to_channel"] = dict(sorted(note_to_channel.items(), key=lambda item: int(item[0])))
        if "note_labels" in mapping:
            mapping["note_labels"] = {
                note: label
                for note, label in mapping["note_labels"].items()
                if note in mapping["note_to_channel"]
            }

    return config, active_sequence


def iter_calibration_channels(mapping):
    """Yield each active hardware channel exactly once in calibration order."""
    channel_to_notes = defaultdict(list)
    if mapping.get("mode") == "explicit_note_map":
        for note, channel in mapping.get("note_to_channel", {}).items():
            channel_to_notes[int(channel)].append(int(note))

    for channel in engine.get_mapping_channel_order(mapping):
        yield channel, sorted(channel_to_notes.get(int(channel), []))


def iter_mapping_in_note_order(mapping):
    """Yield configured channel tests in musical order when notes are known."""
    if mapping.get("mode") != "explicit_note_map":
        for channel in engine.get_mapping_channel_order(mapping):
            yield None, channel
        return

    note_to_channel = mapping.get("note_to_channel", {})
    for note, channel in sorted(
        ((int(note), int(channel)) for note, channel in note_to_channel.items()),
        key=lambda item: item[0],
    ):
        yield note, channel


def contiguous_octave_mapping(config, bottom_note):
    mapping = engine.build_contiguous_mapping(
        config["mapping"],
        bottom_note,
        bottom_note + len(engine.get_mapping_channel_order(config["mapping"])) - 1,
    )
    return mapping


def run_sweep(connection, config):
    """Fire every mapped note once so wiring/order mistakes are obvious."""
    print("\nSweeping active hardware channels in global channel order.")
    for channel, mapped_notes in iter_calibration_channels(config["mapping"]):
        actuation = engine.resolve_channel_actuation(channel, config)
        pulse = build_calibration_pulse(actuation)
        label = config["mapping"].get("channel_labels", {}).get(str(channel), f"Channel {channel}")
        channel_target = engine.describe_global_channel(channel, config["pca9685"])
        if len(mapped_notes) == 1:
            print(f"  Testing {engine.midi_note_name(mapped_notes[0])} on {channel_target}: {label}")
        elif len(mapped_notes) > 1:
            notes = ", ".join(engine.midi_note_name(note) for note in mapped_notes)
            print(f"  Firing {channel_target}: {label} (currently mapped to {notes})")
        else:
            print(f"  Firing {channel_target}: {label}")
        fire_channel(connection, channel, pulse)
        time.sleep(0.25)


def prompt_bottom_note():
    while True:
        raw = input("Enter the bottom note of your contiguous keyboard range (example: C4): ").strip()
        try:
            return engine.parse_note_token(raw)
        except ValueError as error:
            print(error)


def prompt_active_channel_count(config):
    default_count = len(engine.get_mapping_channel_order(config["mapping"]))
    capacity = engine.get_global_channel_capacity(config["pca9685"])
    print(
        f"How many hardware channels are active right now? Press Enter to keep {default_count}. "
        f"The configured 4-board system can use up to {capacity}."
    )
    while True:
        raw = input(f"Active channel count [{default_count}]: ").strip()
        if not raw:
            return default_count
        try:
            return engine.parse_active_channel_count(raw, config["pca9685"])
        except ValueError as error:
            print(error)


def calibrate_contiguous_octave(connection, config, port, ready_info):
    run_sweep(connection, config)
    bottom_note = prompt_bottom_note()
    mapping = contiguous_octave_mapping(config, bottom_note)
    mapping_lines = build_mapping_lines(mapping)

    print("\nProposed saved mapping:")
    for line in mapping_lines:
        print(f"  {line}")

    report_payload = {
        "mode": "contiguous_octave",
        "port": port,
        "protocol_version": ready_info["protocol_version"],
        "mapping_lines": mapping_lines,
        "mapping": mapping,
    }
    save_calibrated_mapping(mapping, report_payload)
    print(f"\nSaved calibrated mapping to {engine.CALIBRATED_MAPPING_PATH.relative_to(engine.REPO_ROOT)}")


def calibrate_manual_mapping(connection, config, port, ready_info):
    """Build a mapping by firing each channel and asking which key moved."""
    note_to_channel = {}
    note_labels = {}
    channel_labels = dict(config["mapping"].get("channel_labels", {}))
    channel_sequence = engine.get_mapping_channel_order(config["mapping"])

    print("\nManual channel mapping:")
    print("A single channel will fire, then you enter the piano key it moved.")
    print("Use note names like C4 or F#3. Press Enter to skip a channel.")

    for channel in channel_sequence:
        actuation = engine.resolve_channel_actuation(channel, config)
        pulse = build_calibration_pulse(actuation)
        label = channel_labels.get(str(channel), f"Channel {channel}")
        print(f"\nFiring {engine.describe_global_channel(channel, config['pca9685'])}: {label}")
        fire_channel(connection, channel, pulse)

        while True:
            raw = input("Which piano note moved? ").strip()
            if not raw:
                break
            try:
                note = engine.parse_note_token(raw)
            except ValueError as error:
                print(error)
                continue
            if str(note) in note_to_channel:
                print("That note was already assigned. Enter a different note or press Enter to skip.")
                continue
            note_to_channel[str(note)] = channel
            note_labels[str(note)] = engine.midi_note_name(note)
            break

    if not note_to_channel:
        raise RuntimeError("No channel mappings were entered, so nothing was saved.")

    mapping = {
        "mode": "explicit_note_map",
        "note_to_channel": dict(sorted(note_to_channel.items(), key=lambda item: int(item[0]))),
        "note_labels": note_labels,
        "channel_labels": channel_labels,
        "channel_sequence": channel_sequence,
    }
    mapping_lines = build_mapping_lines(mapping)
    report_payload = {
        "mode": "manual_mapping",
        "port": port,
        "protocol_version": ready_info["protocol_version"],
        "mapping_lines": mapping_lines,
        "mapping": mapping,
    }
    save_calibrated_mapping(mapping, report_payload)
    print(f"\nSaved calibrated mapping to {engine.CALIBRATED_MAPPING_PATH.relative_to(engine.REPO_ROOT)}")


def tune_channel(connection, config, channel):
    """Interactively test one channel's PWM and timing values."""
    actuation = engine.resolve_channel_actuation(channel, config)
    pulse = build_calibration_pulse(actuation)

    print("\nChannel tuning test")
    print("Press Enter to keep the suggested value for each field.")

    strike_pwm = input(f"Strike PWM [{pulse['strike_pwm']}]: ").strip() or str(pulse["strike_pwm"])
    hold_pwm = input(f"Hold PWM [{pulse['hold_pwm']}]: ").strip() or str(pulse["hold_pwm"])
    strike_ms = input(f"Strike ms [{pulse['strike_ms']}]: ").strip() or str(pulse["strike_ms"])
    hold_ms = input(f"Hold ms [{pulse['hold_ms']}]: ").strip() or str(pulse["hold_ms"])
    release_ms = input(f"Release ms [{pulse['release_ms']}]: ").strip() or str(pulse["release_ms"])

    tuned_pulse = {
        "strike_pwm": int(strike_pwm),
        "hold_pwm": int(hold_pwm),
        "strike_ms": int(strike_ms),
        "hold_ms": int(hold_ms),
        "release_ms": int(release_ms),
    }

    print(f"\nFiring tuned pulse on {engine.describe_global_channel(channel, config['pca9685'])}.")
    fire_channel(connection, channel, tuned_pulse)
    print("If that felt right, update the engineering config later with those values.")


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Calibration and debug tools for the autonomous piano player."
    )
    parser.add_argument("--port", help="Specific serial port to use, such as COM4.")
    parser.add_argument(
        "--active-channels",
        help="How many hardware channels are currently installed. Leave unset to answer interactively.",
    )
    parser.add_argument("--sweep", action="store_true", help="Fire each configured channel once in sequence.")
    parser.add_argument(
        "--calibrate-octave",
        action="store_true",
        help="Save a contiguous note range starting from a prompted bottom note.",
    )
    parser.add_argument(
        "--calibrate-manual",
        action="store_true",
        help="Fire each channel and manually assign the piano note it moves.",
    )
    parser.add_argument("--tune-channel", type=int, help="Run a simple tuning pulse on one channel.")
    return parser


def choose_action(args):
    if args.sweep:
        return "sweep"
    if args.calibrate_octave:
        return "calibrate_octave"
    if args.calibrate_manual:
        return "calibrate_manual"
    if args.tune_channel is not None:
        return "tune"

    print("Calibration actions:")
    print("  1. Sweep the configured channels")
    print("  2. Save a contiguous octave map")
    print("  3. Save a manual channel-to-note map")
    print("  4. Tune one channel")
    while True:
        choice = input("Choose 1, 2, 3, or 4: ").strip()
        if choice == "1":
            return "sweep"
        if choice == "2":
            return "calibrate_octave"
        if choice == "3":
            return "calibrate_manual"
        if choice == "4":
            return "tune"
        print("Enter 1, 2, 3, or 4.")


def main():
    args = build_arg_parser().parse_args()
    config = engine.load_config()
    action = choose_action(args)

    if action in {"sweep", "calibrate_octave", "calibrate_manual"}:
        active_channel_count = args.active_channels
        if active_channel_count is None:
            active_channel_count = prompt_active_channel_count(config)
        config, active_sequence = build_calibration_config(config, active_channel_count)
        print(engine.summarize_active_channel_sequence(active_sequence, config["pca9685"]))

    connection = None
    try:
        connection, port, ready_info = open_runtime_connection(port_override=args.port)
        print(f"Connected to Arduino runtime on {port} (protocol v{ready_info['protocol_version']}).")
        if ready_info.get("i2c_warning"):
            print(f"I2C warning: {ready_info['i2c_warning']}")
        elif ready_info.get("i2c_info") and ready_info["i2c_info"].get("detected_addresses"):
            print(
                "Detected PCA9685 addresses: "
                f"{engine.format_i2c_address_list(ready_info['i2c_info']['detected_addresses'])}"
            )

        if action == "sweep":
            run_sweep(connection, config)
            return
        if action == "calibrate_octave":
            calibrate_contiguous_octave(connection, config, port, ready_info)
            return
        if action == "calibrate_manual":
            calibrate_manual_mapping(connection, config, port, ready_info)
            return
        if action == "tune":
            channel = args.tune_channel
            if channel is None:
                raw = input("Which channel should be tuned? ").strip()
                channel = int(raw)
            tune_channel(connection, config, channel)
            return
    finally:
        if connection is not None:
            try:
                # Always leave the MOSFET/PCA outputs off after a debug action,
                # even if the user cancels or a command fails.
                engine.send_serial_command(connection, "ALL_OFF", ("OK ALL_OFF",), timeout_seconds=2.0)
            except Exception:
                pass
            connection.close()


if __name__ == "__main__":
    try:
        main()
    except (EOFError, FileNotFoundError, RuntimeError, TimeoutError, ValueError, OSError) as error:
        print(f"\nUnable to continue: {error}")
        raise SystemExit(1)
