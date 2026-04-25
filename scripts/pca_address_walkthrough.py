"""Interactive PCA9685 address test helper.

This walks the user through the exact board-by-board tests needed to answer:
"Do these PCA boards all sit at the same default address, and do I need to
physically change some of them?"

It talks to the already-uploaded MusicBotOfficial Arduino runtime and sends the
`I2C` command at each step. The results are also saved as JSON so the user can
review what each board reported without re-running the whole sequence from
memory.
"""

from __future__ import annotations

import argparse
import json

import convert_midi as engine
import piano_tools


REPORT_PATH = engine.METADATA_DIR / "pca_address_walkthrough.json"


def prompt_to_continue(title: str, instructions: str):
    print()
    print(title)
    print("-" * len(title))
    print(instructions.strip())
    raw = input("\nPress Enter when ready, or type q to quit: ").strip().lower()
    if raw in {"q", "quit", "exit"}:
        raise KeyboardInterrupt("Walkthrough cancelled by user.")


def query_i2c(connection):
    response = engine.send_serial_command(connection, "I2C", ("I2C",), timeout_seconds=2.0)
    return engine.parse_i2c_response(response)


def summarize_detected(i2c_info):
    detected = i2c_info.get("detected_addresses", [])
    if not detected:
        return "No PCA9685 boards detected"
    return f"Detected {engine.format_i2c_address_list(detected)}"


def analyze_single_board_result(step_result):
    detected = step_result["detected_addresses"]
    if not detected:
        return "No board was detected. Check SDA, SCL, VCC, and GND to that board."
    if len(detected) > 1:
        return (
            "More than one address responded while this was supposed to be a one-board test. "
            "Another board is probably still connected to the bus."
        )
    if detected[0] == 0x40:
        return (
            "This board is still on the default address 0x40. "
            "That is normal for one board by itself."
        )
    return f"This board is already configured for {engine.format_i2c_address_list(detected)}."


def build_final_summary(single_board_results, combined_result):
    single_detected = [tuple(result["detected_addresses"]) for result in single_board_results]
    if all(addresses == (0x40,) for addresses in single_detected):
        return (
            "All four one-board tests came back as 0x40. "
            "That means the boards are still at the same default address, so yes: "
            "you need to physically change three board addresses before one-at-a-time calibration can work."
        )

    if any(not addresses for addresses in single_detected):
        return (
            "At least one board did not answer during its one-board test. "
            "Fix power or I2C wiring before changing addresses."
        )

    if tuple(combined_result["detected_addresses"]) == (0x40, 0x41, 0x42, 0x43):
        return (
            "Great: the combined test sees all four expected addresses. "
            "Addressing is no longer the blocker for calibration."
        )

    return (
        "The one-board tests did not all match the final combined test cleanly. "
        "Review the saved report and compare each board's physical address setting."
    )


def run_walkthrough(port_override=None):
    config = engine.load_config()
    expected_addresses = engine.get_pca_board_addresses(config["pca9685"])

    print("PCA9685 Address Walkthrough")
    print("==========================")
    print(
        "This helper talks to the uploaded MusicBotOfficial Arduino runtime and sends the I2C scan command at each step."
    )
    print(f"Expected four-board address plan: {engine.format_i2c_address_list(expected_addresses)}")
    print(f"Report will be saved to: {REPORT_PATH}")

    connection = None
    try:
        connection, port, ready_info = piano_tools.open_runtime_connection(port_override=port_override)
        print(f"\nConnected to Arduino runtime on {port} (protocol v{ready_info['protocol_version']}).")
        if ready_info.get("i2c_info") is None:
            raise RuntimeError(
                "The current Arduino runtime did not answer the I2C scan command. "
                "Upload arduino/MusicBotOfficial/MusicBotOfficial.ino first."
            )

        results = {
            "port": port,
            "expected_addresses": expected_addresses,
            "steps": [],
        }

        prompt_to_continue(
            "Step 1: All boards connected",
            """
Leave the full 4-board setup connected exactly as it is now.
This tells us the current combined bus state before any isolation tests.
""",
        )
        initial_info = query_i2c(connection)
        print(summarize_detected(initial_info))
        results["steps"].append(
            {
                "name": "all_boards_initial",
                "detected_addresses": initial_info["detected_addresses"],
                "analysis": engine.build_i2c_mismatch_warning(initial_info) or "All expected boards detected.",
            }
        )

        single_board_results = []
        for index in range(4):
            prompt_to_continue(
                f"Step {index + 2}: Board {index + 1} by itself",
                f"""
Disconnect power and I2C from the other PCA boards so only one PCA9685 board remains on the bus.
Keep only the board you are testing connected to Arduino A4/A5, logic power, and ground.

This one-board test should usually read as 0x40 if the board is still at its untouched default address.
""",
            )
            i2c_info = query_i2c(connection)
            analysis = analyze_single_board_result(i2c_info)
            print(summarize_detected(i2c_info))
            print(analysis)
            step_result = {
                "name": f"single_board_{index + 1}",
                "detected_addresses": i2c_info["detected_addresses"],
                "analysis": analysis,
            }
            single_board_results.append(step_result)
            results["steps"].append(step_result)

        prompt_to_continue(
            "Final step: Reconnect all four boards",
            """
Reconnect all four PCA9685 boards to the shared SDA/SCL bus and power again.
This final scan checks whether the full system now exposes four unique addresses.
""",
        )
        final_info = query_i2c(connection)
        print(summarize_detected(final_info))
        results["steps"].append(
            {
                "name": "all_boards_final",
                "detected_addresses": final_info["detected_addresses"],
                "analysis": engine.build_i2c_mismatch_warning(final_info) or "All expected boards detected.",
            }
        )

        results["summary"] = build_final_summary(single_board_results, final_info)
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

        print("\nSummary")
        print("-------")
        print(results["summary"])
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
        description="Walk through PCA9685 address tests and record which addresses answer on the I2C bus."
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
