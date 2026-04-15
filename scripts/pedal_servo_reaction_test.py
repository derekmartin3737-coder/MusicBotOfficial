"""Reaction-time bench test for a sustain-pedal servo.

This script pairs with arduino/PedalServoBenchTest/PedalServoBenchTest.ino. The
Arduino moves the servo between two angles, and the user presses Space when the
servo reaches the endpoint. The saved CSV/JSON timings estimate travel delay so
future pedal support can trigger slightly early and land in time with the song.

Important limitation: this is not closed-loop position feedback. The timing
includes human reaction time and should be treated as an engineering estimate.
"""

import argparse
import csv
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import msvcrt
except ImportError:  # pragma: no cover - Windows-only workflow
    msvcrt = None

import serial
from serial.tools import list_ports


REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_CSV_PATH = REPO_ROOT / "docs" / "pedal_servo_reaction_results.csv"
SUMMARY_JSON_PATH = REPO_ROOT / "docs" / "pedal_servo_reaction_summary.json"

DEFAULT_BAUD_RATE = 115200
DEFAULT_MEASURED_MOVES = 10
DEFAULT_ARM_LENGTH_IN = 0.5
DEFAULT_UP_ANGLE_DEG = 0
DEFAULT_DOWN_ANGLE_DEG = 180
DEFAULT_SETTLE_SECONDS = 1.5


def list_serial_ports():
    ports = list(list_ports.comports())
    if not ports:
        print("No serial devices were found.")
        return

    print("Available serial ports:")
    for port in ports:
        manufacturer = port.manufacturer or "Unknown"
        print(f"{port.device} - {port.description} {manufacturer}")


def choose_serial_port(preferred_port=None):
    ports = list(list_ports.comports())
    if not ports:
        raise RuntimeError("No serial devices were found. Connect the Arduino and try again.")

    if preferred_port:
        for port in ports:
            if port.device.upper() == preferred_port.upper():
                return port.device
        raise RuntimeError(f"Requested port {preferred_port} was not found.")

    for port in ports:
        descriptor = " ".join(
            filter(
                None,
                [
                    port.device,
                    port.description,
                    port.manufacturer,
                ],
            )
        ).lower()
        if any(token in descriptor for token in ("arduino", "wch", "ch340", "usb serial", "uno")):
            return port.device

    if len(ports) == 1:
        return ports[0].device

    print("Multiple serial ports were found:")
    for index, port in enumerate(ports, start=1):
        manufacturer = port.manufacturer or "Unknown"
        print(f"  {index}. {port.device} - {port.description} ({manufacturer})")

    while True:
        choice = input("Choose the Arduino COM port number: ").strip()
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(ports):
                return ports[index - 1].device
        print("Enter a valid port number.")


def read_until_prefix(connection, prefixes, timeout_seconds=4.0):
    """Read serial lines until the Arduino sends one of the expected prefixes."""
    deadline = time.perf_counter() + timeout_seconds
    while time.perf_counter() < deadline:
        raw_line = connection.readline()
        if not raw_line:
            continue
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        if line.startswith("ERROR "):
            return line
        if any(line.startswith(prefix) for prefix in prefixes):
            return line
    raise TimeoutError(f"Timed out waiting for one of: {', '.join(prefixes)}")


def send_command(connection, command, expected_prefixes, timeout_seconds=4.0):
    connection.write((command + "\n").encode("ascii"))
    connection.flush()
    response = read_until_prefix(connection, expected_prefixes, timeout_seconds=timeout_seconds)
    if response.startswith("ERROR "):
        raise RuntimeError(f"Servo bench sketch returned an error for '{command}': {response}")
    return response


def flush_keyboard_buffer():
    if msvcrt is None:
        raise RuntimeError("This reaction-time tester currently supports Windows only.")

    while msvcrt.kbhit():
        msvcrt.getwch()


def wait_for_space_press(prompt_text):
    """Block until the user taps Space for one measured servo endpoint."""
    print(prompt_text)
    flush_keyboard_buffer()

    while True:
        if msvcrt.kbhit():
            key = msvcrt.getwch()
            if key == " ":
                return
            if key in ("\r", "\n"):
                continue
            if key == "\x03":
                raise KeyboardInterrupt
        time.sleep(0.005)


def round_trip_arc_length_inches(arm_length_in, start_angle_deg, end_angle_deg):
    """Estimate the servo arm tip travel distance for a given angular sweep."""
    theta_rad = math.radians(abs(end_angle_deg - start_angle_deg))
    return arm_length_in * theta_rad


def build_results_rows(trials, test_started_at, port, args):
    rows = []
    for trial in trials:
        rows.append(
            {
                "trial_id": trial["trial_id"],
                "test_date": test_started_at,
                "port": port,
                "servo_model": args.servo_model,
                "arm_length_in": args.arm_length_in,
                "up_angle_deg": args.up_angle_deg,
                "down_angle_deg": args.down_angle_deg,
                "direction": trial["direction"],
                "reaction_time_ms": round(trial["reaction_time_ms"], 3),
                "arc_length_in": round(trial["arc_length_in"], 4),
                "estimated_tip_speed_in_per_s": round(trial["estimated_tip_speed_in_per_s"], 4),
            }
        )
    return rows


def write_results(rows, summary):
    RESULTS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "trial_id",
        "test_date",
        "port",
        "servo_model",
        "arm_length_in",
        "up_angle_deg",
        "down_angle_deg",
        "direction",
        "reaction_time_ms",
        "arc_length_in",
        "estimated_tip_speed_in_per_s",
    ]

    with RESULTS_CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    SUMMARY_JSON_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def summarize_trials(trials, args, port, test_started_at):
    """Build human-readable aggregate timing values from the raw trials."""
    grouped = {"down": [], "up": []}
    for trial in trials:
        grouped[trial["direction"]].append(trial)

    def average(values):
        return sum(values) / len(values) if values else None

    def build_direction_summary(direction):
        direction_trials = grouped[direction]
        reaction_times = [trial["reaction_time_ms"] for trial in direction_trials]
        tip_speeds = [trial["estimated_tip_speed_in_per_s"] for trial in direction_trials]
        average_reaction_time_ms = average(reaction_times)
        return {
            "trial_count": len(direction_trials),
            "average_reaction_time_ms": average_reaction_time_ms,
            "average_tip_speed_in_per_s": average(tip_speeds),
            "estimated_tip_speed_from_average_time_in_per_s": (
                None
                if average_reaction_time_ms in (None, 0)
                else grouped[direction][0]["arc_length_in"] / (average_reaction_time_ms / 1000.0)
            ),
            "minimum_reaction_time_ms": min(reaction_times) if reaction_times else None,
            "maximum_reaction_time_ms": max(reaction_times) if reaction_times else None,
        }

    overall_reaction_times = [trial["reaction_time_ms"] for trial in trials]
    overall_average_reaction_time_ms = average(overall_reaction_times)

    return {
        "test_date": test_started_at,
        "port": port,
        "servo_model": args.servo_model,
        "arm_length_in": args.arm_length_in,
        "up_angle_deg": args.up_angle_deg,
        "down_angle_deg": args.down_angle_deg,
        "measured_moves": args.measured_moves,
        "overall_average_reaction_time_ms": overall_average_reaction_time_ms,
        "overall_estimated_tip_speed_in_per_s": (
            None
            if overall_average_reaction_time_ms in (None, 0)
            else trials[0]["arc_length_in"] / (overall_average_reaction_time_ms / 1000.0)
        ),
        "notes": "Reaction-based timings include human response delay. Use them as an estimate, not as true sensor feedback.",
        "down": build_direction_summary("down"),
        "up": build_direction_summary("up"),
    }


def print_summary(summary):
    print("\nReaction-time test complete.")
    print(f"Saved raw trials to: {RESULTS_CSV_PATH}")
    print(f"Saved summary to: {SUMMARY_JSON_PATH}")
    print(f"\nOverall average travel time: {summary['overall_average_reaction_time_ms']:.1f} ms")
    print(
        f"Overall estimated tip speed: "
        f"{summary['overall_estimated_tip_speed_in_per_s']:.3f} in/s"
    )

    for direction in ("down", "up"):
        direction_summary = summary[direction]
        print(f"\n{direction.upper()} results:")
        print(f"  Trials: {direction_summary['trial_count']}")
        print(f"  Average travel time: {direction_summary['average_reaction_time_ms']:.1f} ms")
        print(
            f"  Estimated tip speed from average time: "
            f"{direction_summary['estimated_tip_speed_from_average_time_in_per_s']:.3f} in/s"
        )
        print(f"  Fastest trial: {direction_summary['minimum_reaction_time_ms']:.1f} ms")
        print(f"  Slowest trial: {direction_summary['maximum_reaction_time_ms']:.1f} ms")


def run_reaction_test(args):
    """Run the full serial test sequence and write results under docs/."""
    if msvcrt is None:
        raise RuntimeError("This script currently supports Windows only because it uses spacebar capture.")

    port = choose_serial_port(args.port)
    test_started_at = datetime.now().isoformat(timespec="seconds")
    arc_length_in = round_trip_arc_length_inches(args.arm_length_in, args.up_angle_deg, args.down_angle_deg)

    with serial.Serial(port=port, baudrate=args.baud_rate, timeout=0.5) as connection:
        time.sleep(2.5)
        connection.reset_input_buffer()
        connection.reset_output_buffer()

        ready_line = read_until_prefix(connection, ("READY PEDAL_SERVO_TEST",), timeout_seconds=5.0)
        print(f"Connected on {port}: {ready_line}")
        send_command(connection, "STATUS", ("STATUS",), timeout_seconds=2.0)
        send_command(connection, "HOME", ("OK HOME",), timeout_seconds=4.0)
        time.sleep(args.settle_seconds)

        input(
            f"\nPress Enter to begin. The first move to {args.down_angle_deg} degrees "
            f"will be used only to establish a full-range starting point and will not be recorded. "
        )

        # The first movement may start from an unknown physical angle, so it is
        # used only to put the servo at a known endpoint before measured moves.
        send_command(connection, "MOVE DOWN", ("OK MOVE_DOWN",), timeout_seconds=2.0)
        print("Priming move complete. This first move was omitted from the results.")
        time.sleep(args.settle_seconds)

        trials = []
        trial_id = 1
        next_direction = "up"

        for repetition in range(1, args.measured_moves + 1):
            direction = next_direction
            target_angle = args.up_angle_deg if direction == "up" else args.down_angle_deg
            command = "MOVE UP" if direction == "up" else "MOVE DOWN"
            expected_prefix = "OK MOVE_UP" if direction == "up" else "OK MOVE_DOWN"

            flush_keyboard_buffer()
            start_time = time.perf_counter()
            send_command(connection, command, (expected_prefix,), timeout_seconds=2.0)
            wait_for_space_press(
                f"Move {repetition}/{args.measured_moves}: press Space when the servo reaches "
                f"{int(target_angle)} degrees ({direction})."
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            trials.append(
                {
                    "trial_id": trial_id,
                    "direction": direction,
                    "reaction_time_ms": elapsed_ms,
                    "arc_length_in": arc_length_in,
                    "estimated_tip_speed_in_per_s": arc_length_in / (elapsed_ms / 1000.0),
                }
            )
            print(f"  Recorded {direction} travel: {elapsed_ms:.1f} ms")
            trial_id += 1
            time.sleep(args.settle_seconds)
            next_direction = "down" if direction == "up" else "up"

        send_command(connection, "HOME", ("OK HOME",), timeout_seconds=4.0)

    rows = build_results_rows(trials, test_started_at, port, args)
    summary = summarize_trials(trials, args, port, test_started_at)
    write_results(rows, summary)
    print_summary(summary)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Measure sustain-pedal servo travel time by pressing Space when the servo reaches each endpoint."
    )
    parser.add_argument("--port", help="Arduino serial port such as COM7.")
    parser.add_argument("--list-ports", action="store_true", help="List serial ports and exit.")
    parser.add_argument("--baud-rate", type=int, default=DEFAULT_BAUD_RATE, help="Serial baud rate.")
    parser.add_argument(
        "--measured-moves",
        type=int,
        default=DEFAULT_MEASURED_MOVES,
        help="Total recorded moves after the unmeasured priming move.",
    )
    parser.add_argument("--arm-length-in", type=float, default=DEFAULT_ARM_LENGTH_IN, help="Servo arm length in inches.")
    parser.add_argument("--up-angle-deg", type=float, default=DEFAULT_UP_ANGLE_DEG, help="Servo up angle used in the test sketch.")
    parser.add_argument("--down-angle-deg", type=float, default=DEFAULT_DOWN_ANGLE_DEG, help="Servo down angle used in the test sketch.")
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=DEFAULT_SETTLE_SECONDS,
        help="Pause between recorded moves.",
    )
    parser.add_argument("--servo-model", default="9g microservo", help="Model name stored in the results.")
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.list_ports:
        list_serial_ports()
        return

    run_reaction_test(args)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, FileNotFoundError, RuntimeError, TimeoutError, ValueError, OSError) as error:
        print(f"\nUnable to continue: {error}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(1)
