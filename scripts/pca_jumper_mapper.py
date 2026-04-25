"""Map PCA9685 address jumper pads one at a time.

This is a follow-up to the temporary-bridge walkthrough. It assumes you now
have one PCA board that can be detected by itself at 0x40 and want to discover
which of the exposed silver jumper pairs actually change the I2C address.

Workflow:
1. Leave only one PCA board connected to Arduino SDA/SCL/VCC/GND.
2. Run a baseline scan with no bridge.
3. Test each exposed jumper pair one at a time with a temporary bridge.
4. Save the detected address for each jumper pair.

The script does not guess which physical pair is A0 or A1. It just records what
address appears when each candidate pair is bridged by itself.
"""

from __future__ import annotations

import argparse
import json

import convert_midi as engine
import piano_tools


REPORT_PATH = engine.METADATA_DIR / "pca_jumper_mapper.json"


def prompt_step(title: str, body: str):
    print()
    print(title)
    print("-" * len(title))
    print(body.strip())
    raw = input("\nPress Enter when ready, or type q to quit: ").strip().lower()
    if raw in {"q", "quit", "exit"}:
        raise KeyboardInterrupt("Walkthrough cancelled by user.")


def query_i2c(connection):
    response = engine.send_serial_command(connection, "I2C", ("I2C",), timeout_seconds=2.0)
    return engine.parse_i2c_response(response)


def format_detected(detected_addresses):
    if not detected_addresses:
        return "none"
    return engine.format_i2c_address_list(detected_addresses)


def record_step(connection, results, name, title, body):
    prompt_step(title, body)
    i2c_info = query_i2c(connection)
    detected = i2c_info.get("detected_addresses", [])
    print(f"Detected addresses: {format_detected(detected)}")
    results["steps"].append(
        {
            "name": name,
            "detected_addresses": detected,
        }
    )
    return detected


def summarize_results(results):
    baseline = ()
    for step in results["steps"]:
        if step["name"] == "baseline":
            baseline = tuple(step["detected_addresses"])
            break

    lines = []
    if baseline != (0x40,):
        lines.append(
            "Baseline did not come back as 0x40, so stop here and fix the one-board wiring before changing jumpers."
        )
        return lines

    lines.append("Baseline one-board scan worked at 0x40.")
    changed = []
    unchanged = []
    missing = []

    for step in results["steps"]:
        if not step["name"].startswith("jumper_"):
            continue
        detected = tuple(step["detected_addresses"])
        label = step["name"].replace("jumper_", "jumper ")
        if not detected:
            missing.append(label)
        elif detected == (0x40,):
            unchanged.append(label)
        else:
            changed.append((label, detected))

    if changed:
        for label, detected in changed:
            lines.append(f"{label} changes the address to {engine.format_i2c_address_list(detected)}.")
    if unchanged:
        lines.append(
            f"These jumper tests did not change the address and still read 0x40: {', '.join(unchanged)}."
        )
    if missing:
        lines.append(
            f"These jumper tests made the board disappear entirely: {', '.join(missing)}. "
            "That usually means the bridge touched the wrong metal or caused a bad contact."
        )

    if not changed:
        lines.append(
            "None of the tested jumper pairs changed the address. Either the temporary bridge did not truly short the exposed jumper pair, "
            "or the pads you chose are not the address jumpers."
        )

    return lines


def run_mapper(port_override=None, jumper_count=6):
    print("PCA Jumper Mapper")
    print("=================")
    print("Leave only one PCA board connected to Arduino A4/A5, VCC, and GND.")
    print("Power off the board before moving each temporary bridge.")
    print(f"Report path: {REPORT_PATH}")

    connection = None
    try:
        connection, port, ready_info = piano_tools.open_runtime_connection(port_override=port_override)
        print(f"\nConnected to Arduino runtime on {port} (protocol v{ready_info['protocol_version']}).")

        results = {
            "port": port,
            "steps": [],
        }

        record_step(
            connection,
            results,
            "baseline",
            "Baseline: one board only, no temporary bridge",
            """
Disconnect the other three PCA boards completely from SDA, SCL, VCC, and GND.
Leave just one PCA board connected to:
  - Arduino A4 -> PCA SDA
  - Arduino A5 -> PCA SCL
  - Arduino 5V -> PCA VCC
  - Arduino GND -> PCA GND

Do not add any temporary jumper bridge yet.
Expected result: 0x40.
""",
        )

        for index in range(1, jumper_count + 1):
            record_step(
                connection,
                results,
                f"jumper_{index}",
                f"Test jumper pair {index}",
                f"""
Power the board down first.
Add a temporary bridge across exposed jumper pair {index} only.
Remove any bridge from all other jumper pairs.
Keep only this same single PCA board connected to the Arduino.

Use the bare exposed silver jumper pair, not the resistor components marked 103/221.
Expected result: one address, often 0x41 or 0x42 if this is one of the low address bits.
""",
            )

        results["summary_lines"] = summarize_results(results)
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

        print("\nSummary")
        print("-------")
        for line in results["summary_lines"]:
            print(f"- {line}")
        print(f"\nSaved report: {REPORT_PATH}")

    finally:
        if connection is not None:
            try:
                engine.send_serial_command(connection, "ALL_OFF", ("OK ALL_OFF",), timeout_seconds=2.0)
            except Exception:
                pass
            connection.close()


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Test exposed PCA9685 jumper pairs one at a time and record which address each one produces."
    )
    parser.add_argument("--port", help="Specific serial port to use, such as COM7.")
    parser.add_argument(
        "--jumper-count",
        type=int,
        default=6,
        help="How many candidate exposed jumper pairs you want to test on the board.",
    )
    return parser


def main():
    args = build_arg_parser().parse_args()
    run_mapper(port_override=args.port, jumper_count=args.jumper_count)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as error:
        print(f"\n{error}")
        raise SystemExit(1)
    except (EOFError, FileNotFoundError, RuntimeError, TimeoutError, ValueError, OSError) as error:
        print(f"\nUnable to continue: {error}")
        raise SystemExit(1)
