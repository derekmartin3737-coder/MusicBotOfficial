"""Detect PCA9685 board addresses in physical order and retarget the repo.

Use this when the boards intentionally live on higher I2C addresses and we want
the software to follow the hardware instead of re-soldering back to 0x40-0x43.

Workflow:
1. Upload the current MusicBotOfficial runtime that includes full PCA scan data.
2. Connect one PCA board at a time, in physical low-to-high piano order.
3. This script records the one detected address for each board.
4. The script rewrites config/piano_config.json and arduino/MusicBotOfficial/
   MusicBotOfficial.ino to use those addresses in that same physical order.
"""

from __future__ import annotations

import argparse
import json
import re
import time

import convert_midi as engine
import piano_tools


REPORT_PATH = engine.METADATA_DIR / "pca_retarget_runtime_addresses.json"
PCA9685_ALL_CALL_ADDRESS = 0x70
RUNTIME_ADDRESS_ARRAY_RE = re.compile(
    r"(static const uint8_t RUNTIME_PCA9685_I2C_ADDRESSES\[RUNTIME_PCA_BOARD_COUNT\] = \{\s*)(.*?)(\s*\};)",
    re.DOTALL,
)


def prompt_step(title: str, body: str):
    print()
    print(title)
    print("-" * len(title))
    print(body.strip())
    raw = input("\nPress Enter when ready, or type q to quit: ").strip().lower()
    if raw in {"q", "quit", "exit"}:
        raise KeyboardInterrupt("Retargeting cancelled by user.")


def query_i2c(connection):
    response = engine.send_serial_command(connection, "I2C", ("I2C",), timeout_seconds=2.0)
    info = engine.parse_i2c_response(response)
    info["supports_full_scan"] = " all=" in response
    return info


def reconnect_runtime(previous_connection, port_override):
    if previous_connection is not None:
        try:
            previous_connection.close()
        except Exception:
            pass
    connection, port, ready_info = piano_tools.open_runtime_connection(port_override=port_override)
    return connection, port, ready_info


def query_i2c_with_reconnect(connection, port_override):
    try:
        return connection, query_i2c(connection)
    except (RuntimeError, TimeoutError, OSError):
        # If the user power-cycles the Arduino or the serial link hiccups while
        # swapping boards, reopen the runtime once and try again.
        time.sleep(0.8)
        connection, _, _ = reconnect_runtime(connection, port_override)
        return connection, query_i2c(connection)


def extract_detected_addresses(i2c_info):
    full_scan = list(i2c_info.get("all_detected_addresses", []))
    detected = full_scan if full_scan else list(i2c_info.get("detected_addresses", []))
    # PCA9685 boards acknowledge the shared LED All Call address 0x70 at power-up.
    # For board-identification we care about the unique hardware address, not the
    # shared broadcast address.
    if len(detected) > 1 and PCA9685_ALL_CALL_ADDRESS in detected:
        detected = [address for address in detected if address != PCA9685_ALL_CALL_ADDRESS]
    return detected


def format_detected(addresses):
    if not addresses:
        return "none"
    return engine.format_i2c_address_list(addresses)


def require_single_detected_address(connection, step_name: str, port_override=None):
    connection, i2c_info = query_i2c_with_reconnect(connection, port_override)
    full_detected = list(i2c_info.get("all_detected_addresses", []))
    detected = extract_detected_addresses(i2c_info)
    print(f"Detected addresses: {format_detected(detected)}")
    if full_detected and full_detected != detected:
        print(
            "Full scan also saw "
            f"{engine.format_i2c_address_list(full_detected)}; "
            "ignoring shared all-call address 0x70 for board identification."
        )
    if len(detected) != 1:
        if not detected:
            raise RuntimeError(
                f"{step_name} did not detect exactly one PCA9685 board. "
                "Leave only that one board connected to SDA, SCL, VCC, and GND."
            )
        raise RuntimeError(
            f"{step_name} detected more than one PCA9685 board: {format_detected(detected)}. "
            "Disconnect the other boards completely before continuing."
        )
    return connection, i2c_info, detected[0]


def update_config_board_addresses(addresses):
    with engine.CONFIG_PATH.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    config["pca9685"]["board_addresses"] = [int(address) for address in addresses]
    config.setdefault("notes", {})
    config["notes"][
        "wiring_assumption"
    ] = (
        "Global channels 0 through 15 live on the first configured PCA9685 address, "
        "16 through 31 on the second, 32 through 47 on the third, and 48 through 63 on the fourth."
    )
    engine.CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def update_runtime_board_addresses(addresses):
    runtime_text = engine.REPO_RUNTIME_SKETCH_PATH.read_text(encoding="utf-8")
    replacement_body = "".join(f"    0x{int(address):02X},\n" for address in addresses)
    updated_text, substitution_count = RUNTIME_ADDRESS_ARRAY_RE.subn(
        rf"\g<1>{replacement_body}\g<3>",
        runtime_text,
        count=1,
    )
    if substitution_count != 1:
        raise RuntimeError(
            f"Could not find the runtime PCA9685 address array in {engine.REPO_RUNTIME_SKETCH_PATH}."
        )
    engine.REPO_RUNTIME_SKETCH_PATH.write_text(updated_text, encoding="utf-8")


def run_retarget(port_override=None):
    print("PCA Runtime Address Retarget")
    print("===========================")
    print("This helper records each board's real I2C address in physical low-to-high order.")
    print("It then updates the repo config and the Arduino runtime to use those addresses.")
    print(f"Report path: {REPORT_PATH}")

    connection = None
    try:
        connection, port, ready_info = piano_tools.open_runtime_connection(port_override=port_override)
        print(f"\nConnected to Arduino runtime on {port} (protocol v{ready_info['protocol_version']}).")

        connection, startup_i2c = query_i2c_with_reconnect(connection, port)
        if not startup_i2c.get("supports_full_scan"):
            raise RuntimeError(
                "This Arduino runtime does not expose the full PCA scan yet. "
                "Upload arduino/MusicBotOfficial/MusicBotOfficial.ino from the repo first, then rerun this helper."
            )

        steps = [
            (
                "board_1",
                "Step 1: Lowest-note board alone",
                """
Power down first.
Connect only the PCA board that drives the lowest 16 piano notes.
Disconnect the other three PCA boards completely from SDA, SCL, VCC, and GND.
Keep the Arduino itself plugged into USB if possible; only swap the PCA board wiring.
""",
            ),
            (
                "board_2",
                "Step 2: Second board alone",
                """
Power down first.
Disconnect the previous board and connect only the PCA board that drives the next 16 notes up the keyboard.
Leave the other three PCA boards unplugged.
Keep the Arduino itself plugged into USB if possible; only swap the PCA board wiring.
""",
            ),
            (
                "board_3",
                "Step 3: Third board alone",
                """
Power down first.
Disconnect the previous board and connect only the PCA board that drives the next 16 notes up the keyboard.
Leave the other three PCA boards unplugged.
Keep the Arduino itself plugged into USB if possible; only swap the PCA board wiring.
""",
            ),
            (
                "board_4",
                "Step 4: Highest-note board alone",
                """
Power down first.
Disconnect the previous board and connect only the PCA board that drives the highest notes.
This is the top board with the final 13 solenoids.
Leave the other three PCA boards unplugged.
Keep the Arduino itself plugged into USB if possible; only swap the PCA board wiring.
""",
            ),
        ]

        results = {
            "port": port,
            "protocol_version": ready_info["protocol_version"],
            "steps": [],
            "configured_before": engine.get_pca_board_addresses(engine.load_config()["pca9685"]),
        }

        detected_in_order = []
        for name, title, body in steps:
            prompt_step(title, body)
            connection, i2c_info, detected_address = require_single_detected_address(connection, title, port)
            detected_in_order.append(detected_address)
            results["steps"].append(
                {
                    "name": name,
                    "detected_address": detected_address,
                    "all_detected_addresses": i2c_info.get("all_detected_addresses", []),
                    "configured_detected_addresses": i2c_info.get("detected_addresses", []),
                }
            )

        if len(set(detected_in_order)) != len(detected_in_order):
            raise RuntimeError(
                "At least two boards reported the same address during the one-board checks. "
                "That setup will still collide on the shared bus, so fix the duplicate addresses before retargeting the repo."
            )

        prompt_step(
            "Final step: All four boards together",
            """
Power down first.
Reconnect all four PCA boards to the shared SDA/SCL bus and shared logic power.
Keep the physical order the same as the four single-board steps you just recorded.
Keep the Arduino itself plugged into USB if possible; only swap the PCA board wiring.
""",
        )
        connection, final_i2c = query_i2c_with_reconnect(connection, port)
        final_detected = extract_detected_addresses(final_i2c)
        final_full_detected = list(final_i2c.get("all_detected_addresses", []))
        print(f"Detected addresses: {format_detected(final_detected)}")
        if final_full_detected and final_full_detected != final_detected:
            print(
                "Full scan also saw "
                f"{engine.format_i2c_address_list(final_full_detected)}; "
                "ignoring shared all-call address 0x70 for the software address list."
            )

        update_config_board_addresses(detected_in_order)
        update_runtime_board_addresses(detected_in_order)

        results["configured_after"] = list(detected_in_order)
        results["final_all_connected_detected"] = final_detected
        results["final_all_connected_full_detected"] = final_full_detected
        summary = (
            "Updated the repo to use board addresses in physical low-to-high order: "
            f"{engine.format_i2c_address_list(detected_in_order)}. "
            "Upload arduino/MusicBotOfficial/MusicBotOfficial.ino again so the Arduino runtime matches the config."
        )
        if sorted(final_detected) != sorted(detected_in_order):
            summary += (
                " The final all-board scan did not show that same full set yet, so double-check the shared SDA/SCL/VCC/GND wiring before playback."
            )
        results["summary"] = summary

        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

        print("\nSummary")
        print("-------")
        print(results["summary"])
        print(f"Saved report: {REPORT_PATH}")

    finally:
        if connection is not None:
            try:
                engine.send_serial_command(connection, "ALL_OFF", ("OK ALL_OFF",), timeout_seconds=2.0)
            except Exception:
                pass
            connection.close()


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Detect real PCA9685 board addresses in physical order and retarget the repo to use them."
    )
    parser.add_argument("--port", help="Specific serial port to use, such as COM7.")
    return parser


def main():
    args = build_arg_parser().parse_args()
    run_retarget(port_override=args.port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as error:
        print(f"\n{error}")
        raise SystemExit(1)
    except (EOFError, FileNotFoundError, RuntimeError, TimeoutError, ValueError, OSError) as error:
        print(f"\nUnable to continue: {error}")
        raise SystemExit(1)
