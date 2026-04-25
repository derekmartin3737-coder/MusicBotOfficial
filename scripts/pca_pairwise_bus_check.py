"""Check the shared I2C bus one soldered PCA board at a time.

Use this after a soldered-layout test when:
- one unsoldered board still reads 0x40 by itself
- soldered boards alone are not visible in the runtime's 0x40-0x43 scan
- the full four-board bus may be collapsing to `none`

This walkthrough keeps the known-good unsoldered board on the bus and then adds
one soldered board at a time. If 0x40 disappears when a specific soldered board
is added, that board is likely dragging the bus or has a bad solder bridge.
"""

from __future__ import annotations

import argparse
import json

import convert_midi as engine
import piano_tools


REPORT_PATH = engine.METADATA_DIR / "pca_pairwise_bus_check.json"


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


def record_step(connection, results, name: str, title: str, body: str):
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
    by_name = {step["name"]: tuple(step["detected_addresses"]) for step in results["steps"]}
    summary = []

    if by_name.get("unsoldered_alone") == (0x40,):
        summary.append("Baseline unsoldered board still reads 0x40 by itself.")
    else:
        summary.append("Baseline unsoldered board did not read 0x40. Fix that first.")
        return summary

    for step_name, label in (
        ("unsoldered_plus_leftmost", "leftmost-bridge board"),
        ("unsoldered_plus_second_left", "second-left-bridge board"),
        ("unsoldered_plus_third_left", "third-left-bridge board"),
    ):
        detected = by_name.get(step_name, ())
        if detected == (0x40,):
            summary.append(
                f"With the {label} added, the bus still shows only 0x40. That board is present on the bus but not on one of the low target addresses."
            )
        elif not detected:
            summary.append(
                f"With the {label} added, the bus scan collapsed to none. That board likely has a solder bridge or wiring issue that is dragging the bus."
            )
        else:
            summary.append(f"With the {label} added, the runtime saw {format_detected(detected)}.")

    all_four = by_name.get("all_four", ())
    if not all_four:
        summary.append("With all four boards connected, the bus scan still collapsed to none.")
    else:
        summary.append(f"With all four boards connected, the runtime saw {format_detected(all_four)}.")

    return summary


def run_check(port_override=None):
    print("PCA Pairwise Bus Check")
    print("======================")
    print("Keep the unsoldered 0x40 board connected for the pairwise steps and add one soldered board at a time.")
    print(f"Report path: {REPORT_PATH}")

    connection = None
    try:
        connection, port, ready_info = piano_tools.open_runtime_connection(port_override=port_override)
        print(f"\nConnected to Arduino runtime on {port} (protocol v{ready_info['protocol_version']}).")

        results = {"port": port, "steps": []}

        record_step(
            connection,
            results,
            "unsoldered_alone",
            "Step 1: Unsoldered board alone",
            """
Connect only the unsoldered board to SDA, SCL, VCC, and GND.
Leave all soldered boards unplugged.

Expected result: 0x40.
""",
        )

        record_step(
            connection,
            results,
            "unsoldered_plus_leftmost",
            "Step 2: Unsoldered board + leftmost-bridge board",
            """
Power down first.
Keep the unsoldered board connected.
Add only the leftmost-bridge board to the shared SDA/SCL/VCC/GND lines.
Leave the other two soldered boards unplugged.
""",
        )

        record_step(
            connection,
            results,
            "unsoldered_plus_second_left",
            "Step 3: Unsoldered board + second-left-bridge board",
            """
Power down first.
Return to the unsoldered board plus only the second-left-bridge board.
Leave the leftmost-bridge and third-left-bridge boards unplugged.
""",
        )

        record_step(
            connection,
            results,
            "unsoldered_plus_third_left",
            "Step 4: Unsoldered board + third-left-bridge board",
            """
Power down first.
Return to the unsoldered board plus only the third-left-bridge board.
Leave the other two soldered boards unplugged.
""",
        )

        record_step(
            connection,
            results,
            "all_four",
            "Step 5: All four boards together",
            """
Power down first.
Reconnect the full four-board shared bus and scan again.
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
    parser = argparse.ArgumentParser(description="Check the shared I2C bus one soldered PCA board at a time.")
    parser.add_argument("--port", help="Specific serial port to use, such as COM7.")
    return parser


def main():
    args = build_arg_parser().parse_args()
    run_check(port_override=args.port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as error:
        print(f"\n{error}")
        raise SystemExit(1)
    except (EOFError, FileNotFoundError, RuntimeError, TimeoutError, ValueError, OSError) as error:
        print(f"\nUnable to continue: {error}")
        raise SystemExit(1)
