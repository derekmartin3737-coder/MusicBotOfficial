"""Interactive walkthrough for temporary PCA9685 address-bridge testing.

Use this when you want to simulate soldering by temporarily shorting address
jumpers with wire, clips, or another removable bridge. The script sends the
Arduino runtime's `I2C` command after each manual wiring step and records the
results.

Goal:
1. Prove one PCA board can be detected by itself.
2. See which temporary bridge changes the address.
3. Identify which two candidate jumpers behave like A0 and A1.
4. Optionally confirm the final four-board 0x40/0x41/0x42/0x43 layout.
"""

from __future__ import annotations

import argparse
import json

import convert_midi as engine
import piano_tools


REPORT_PATH = engine.METADATA_DIR / "pca_temporary_bridge_walkthrough.json"


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


def analyze_candidate_steps(step_results):
    detected_map = {step["name"]: tuple(step["detected_addresses"]) for step in step_results}
    baseline = detected_map.get("single_board_no_bridge", ())
    candidate_1 = detected_map.get("single_board_candidate_1", ())
    candidate_2 = detected_map.get("single_board_candidate_2", ())
    both = detected_map.get("single_board_both_candidates", ())
    final_all = detected_map.get("all_boards_final", ())

    lines = []

    if baseline != (0x40,):
        lines.append(
            "The baseline one-board test did not come back as 0x40, so do not solder yet. "
            "Fix the one-board logic wiring first: only one PCA board connected, and it must have SDA, SCL, VCC, and GND."
        )
        return lines

    lines.append("Baseline one-board test succeeded at 0x40, so the board can be detected by itself.")

    if candidate_1 == (0x41,) and candidate_2 == (0x42,) and both == (0x43,):
        lines.append(
            "Candidate bridge 1 behaves like A0 and candidate bridge 2 behaves like A1. "
            "That is the clean result you want for addresses 0x40/0x41/0x42/0x43."
        )
    elif candidate_1 == (0x42,) and candidate_2 == (0x41,) and both == (0x43,):
        lines.append(
            "Candidate bridge 1 behaves like A1 and candidate bridge 2 behaves like A0. "
            "That is still fine; the two test jumpers are just swapped relative to your guess."
        )
    else:
        lines.append(
            "The candidate-bridge results did not match the simple A0/A1 pattern yet. "
            "That usually means one of the tested jumper pairs is not A0 or A1, or the temporary bridge was not making clean contact."
        )

    if final_all == (0x40, 0x41, 0x42, 0x43):
        lines.append("Final four-board test looks perfect: all four expected addresses are visible together.")
    elif final_all:
        lines.append(
            f"Final four-board test detected {engine.format_i2c_address_list(final_all)} instead of all four expected addresses."
        )
    else:
        lines.append("Final four-board test detected no PCA boards. Recheck the full bus wiring before soldering.")

    return lines


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


def run_walkthrough(port_override=None):
    expected_addresses = [0x40, 0x41, 0x42, 0x43]

    print("PCA Temporary Bridge Walkthrough")
    print("===============================")
    print("This test is for temporary wire bridges across address-jumper pads.")
    print("Power off the PCA board before moving any temporary bridge.")
    print("Use only one PCA board during the single-board steps.")
    print("Report path:", REPORT_PATH)

    connection = None
    try:
        connection, port, ready_info = piano_tools.open_runtime_connection(port_override=port_override)
        print(f"\nConnected to Arduino runtime on {port} (protocol v{ready_info['protocol_version']}).")

        results = {
            "port": port,
            "expected_addresses": expected_addresses,
            "steps": [],
        }

        record_step(
            connection,
            results,
            "single_board_no_bridge",
            "Step 1: One board only, no temporary bridge",
            """
Disconnect the other three PCA boards completely from SDA, SCL, VCC, and GND.
Leave only one PCA board connected to the Arduino logic lines:
  - Arduino A4 -> PCA SDA
  - Arduino A5 -> PCA SCL
  - Arduino 5V -> PCA VCC
  - Arduino GND -> PCA GND

Do not leave the other boards on the I2C bus for this test.
Do not add any temporary bridge yet.
Expected result: 0x40.
""",
        )

        record_step(
            connection,
            results,
            "single_board_candidate_1",
            "Step 2: Same board, temporary bridge candidate 1 only",
            """
Power the board down first.
Add one temporary bridge across the first candidate address jumper pair you want to test.
Keep only this one PCA board connected to the Arduino.
Leave candidate 2 open for this step.
Expected result: often 0x41 or 0x42, depending on which address bit you picked.
""",
        )

        record_step(
            connection,
            results,
            "single_board_candidate_2",
            "Step 3: Same board, temporary bridge candidate 2 only",
            """
Power the board down first.
Remove candidate 1.
Add a temporary bridge across the second candidate address jumper pair.
Keep only this one PCA board connected to the Arduino.
Expected result: often the other nearby address, such as 0x42 or 0x41.
""",
        )

        record_step(
            connection,
            results,
            "single_board_both_candidates",
            "Step 4: Same board, both temporary bridges together",
            """
Power the board down first.
Place both temporary bridges on the same single PCA board at once.
Keep only this one PCA board connected to the Arduino.
Expected result: if the two jumpers behave like A0 and A1, this should read 0x43.
""",
        )

        record_step(
            connection,
            results,
            "all_boards_final",
            "Step 5: Final four-board check",
            """
Power down and remove the temporary bridge test setup.
Now connect all four PCA boards on the shared SDA/SCL bus using the address pattern you want:
  - one board at 0x40
  - one board at 0x41
  - one board at 0x42
  - one board at 0x43

Then run the full-bus scan.
Expected result: 0x40, 0x41, 0x42, 0x43.
""",
        )

        results["summary_lines"] = analyze_candidate_steps(results["steps"])
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
        description="Guide a temporary wire-bridge PCA9685 address test and record the I2C scan results."
    )
    parser.add_argument("--port", help="Specific serial port to use, such as COM7.")
    return parser


def main():
    args = build_arg_parser().parse_args()
    run_walkthrough(port_override=args.port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as error:
        print(f"\n{error}")
        raise SystemExit(1)
    except (EOFError, FileNotFoundError, RuntimeError, TimeoutError, ValueError, OSError) as error:
        print(f"\nUnable to continue: {error}")
        raise SystemExit(1)
