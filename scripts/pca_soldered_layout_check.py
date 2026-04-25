"""Verify the current four-board PCA9685 soldered address layout.

This helper is for the specific bench state where:
- one board is left unsoldered
- three other boards each have one different solder bridge applied

It guides the user through testing each board alone and then the full four-board
bus using the existing MusicBotOfficial Arduino runtime's `I2C` command.

Important limitation:
- The current Arduino runtime only checks the configured four-address plan
  (0x40, 0x41, 0x42, 0x43). If a soldered board moves to some other valid PCA9685
  address, that step will show `none` here. That still tells us the board is not
  on one of the desired low addresses.
"""

from __future__ import annotations

import argparse
import json

import convert_midi as engine
import piano_tools


REPORT_PATH = engine.METADATA_DIR / "pca_soldered_layout_check.json"


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
    detected_by_name = {step["name"]: tuple(step["detected_addresses"]) for step in results["steps"]}

    summary_lines = []

    if detected_by_name.get("unsoldered_board") == (0x40,):
        summary_lines.append("The unsoldered board still behaves like the default 0x40 board, which is what we want.")
    else:
        summary_lines.append(
            "The unsoldered board did not come back as 0x40. Fix that before trusting the soldered-board results."
        )

    for step_name, label in (
        ("leftmost_bridge_board", "leftmost-bridge board"),
        ("second_left_bridge_board", "second-left-bridge board"),
        ("third_left_bridge_board", "third-left-bridge board"),
    ):
        detected = detected_by_name.get(step_name, ())
        if detected in {(0x41,), (0x42,), (0x43,)}:
            summary_lines.append(f"The {label} is on a desired low address: {format_detected(detected)}.")
        elif detected == (0x40,):
            summary_lines.append(f"The {label} still looks like 0x40, so that solder bridge did not move it.")
        elif not detected:
            summary_lines.append(
                f"The {label} was not visible in the runtime's 0x40-0x43 scan. "
                "That usually means it moved to some other address outside the desired four-address plan."
            )
        else:
            summary_lines.append(f"The {label} came back as {format_detected(detected)}.")

    all_four = detected_by_name.get("all_four_boards", ())
    if all_four == (0x40, 0x41, 0x42, 0x43):
        summary_lines.append("Perfect: the full four-board setup now exposes all four expected addresses.")
    elif all_four:
        summary_lines.append(
            f"With all four boards connected, the runtime detected {format_detected(all_four)} instead of all four expected addresses."
        )
    else:
        summary_lines.append("With all four boards connected, the runtime detected no PCA boards at all.")

    return summary_lines


def run_layout_check(port_override=None):
    print("PCA Soldered Layout Check")
    print("=========================")
    print("This test assumes only one board is left unsoldered and the other three each have one solder bridge.")
    print("For each single-board step, unplug the other three PCA boards completely from SDA, SCL, VCC, and GND.")
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
            "unsoldered_board",
            "Step 1: Unsoldered board alone",
            """
Leave only the high-key PCA board connected if that is the one you left unsoldered.
Disconnect the other three soldered PCA boards completely from SDA, SCL, VCC, and GND.

Expected result: 0x40.
""",
        )

        record_step(
            connection,
            results,
            "leftmost_bridge_board",
            "Step 2: Leftmost-bridge board alone",
            """
Power down first.
Disconnect the unsoldered board and connect only the PCA board that has the leftmost solder bridge.
Disconnect the other two soldered PCA boards as well.

Expected result: ideally 0x41, 0x42, or 0x43. If this step shows none, that bridge probably moved the board
to some other PCA address outside the runtime's 0x40-0x43 scan range.
""",
        )

        record_step(
            connection,
            results,
            "second_left_bridge_board",
            "Step 3: Second-left-bridge board alone",
            """
Power down first.
Disconnect the previous board and connect only the PCA board that has the second-left-most solder bridge.
Leave the other three PCA boards unplugged.

Expected result: ideally 0x41, 0x42, or 0x43.
""",
        )

        record_step(
            connection,
            results,
            "third_left_bridge_board",
            "Step 4: Third-left-bridge board alone",
            """
Power down first.
Disconnect the previous board and connect only the PCA board that has the third-left-most solder bridge.
Leave the other three PCA boards unplugged.

Expected result: ideally 0x41, 0x42, or 0x43.
""",
        )

        record_step(
            connection,
            results,
            "all_four_boards",
            "Step 5: All four boards together",
            """
Power down first.
Reconnect all four PCA boards to the shared SDA/SCL bus and shared logic power.

Expected result: 0x40, 0x41, 0x42, 0x43.
If you see fewer than four addresses here, at least one soldered board is not on the desired low address plan.
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
        description="Verify the current soldered four-board PCA9685 address layout."
    )
    parser.add_argument("--port", help="Specific serial port to use, such as COM7.")
    return parser


def main():
    args = build_arg_parser().parse_args()
    run_layout_check(port_override=args.port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as error:
        print(f"\n{error}")
        raise SystemExit(1)
    except (EOFError, FileNotFoundError, RuntimeError, TimeoutError, ValueError, OSError) as error:
        print(f"\nUnable to continue: {error}")
        raise SystemExit(1)
