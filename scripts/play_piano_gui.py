"""Tkinter launcher for user-friendly piano playback.

Run this from an IDE or by double-clicking the batch file. It wraps the normal
conversion/playback engine with a small desktop UI so the user can choose a
song, tempo, and current hardware note range without answering terminal prompts.
"""

from __future__ import annotations

import copy
import csv
import json
import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, simpledialog, ttk

import convert_midi as engine
import piano_tools

APP_BG = "#eef2f6"
PANEL_BG = "#ffffff"
HERO_BG = "#171b22"
TEXT_COLOR = "#1c2430"
MUTED_TEXT = "#667281"
ACCENT_COLOR = "#198f6a"
ACCENT_HOVER = "#14795a"
ACCENT_SOFT = "#dcefe8"
BORDER_COLOR = "#d6dde5"
INPUT_BG = "#fbfcfd"
INPUT_BORDER = "#c7d0da"
LOG_BG = "#10151c"
LOG_TEXT = "#e7edf5"
LOG_MUTED = "#90a0b5"
QUEUE_INTER_SONG_DELAY_SECONDS = 3.0
SPEED_TEST_SPEEDS = [
    ("8ths", 8),
    ("16ths", 16),
    ("32nds", 32),
    ("64ths", 64),
]
SPEED_TEST_SPEED_LABELS = [label for label, _division in SPEED_TEST_SPEEDS]
SPEED_TEST_LOG_JSON_PATH = engine.METADATA_DIR / "speed_test_log.json"
SPEED_TEST_LOG_CSV_PATH = engine.METADATA_DIR / "speed_test_log.csv"
SPEED_TEST_LOG_COLUMNS = [
    "timestamp",
    "status",
    "note_label",
    "note",
    "channel",
    "speed_label",
    "bpm",
    "period_ms",
    "repeats",
    "velocity",
    "strike_pwm",
    "hold_pwm",
    "strike_ms",
    "release_gap_ms",
    "saved_to_config",
    "saved_minimum_repeat_period_ms",
    "saved_playback_velocity_override",
    "channel_target",
]


def speed_test_division_for_label(label):
    for speed_label, division in SPEED_TEST_SPEEDS:
        if speed_label == label:
            return division
    raise ValueError(f"Unknown speed selection: {label}")


def speed_test_period_ms(bpm, division):
    quarter_ms = 60000.0 / float(bpm)
    return quarter_ms * (4.0 / float(division))


def build_speed_test_delta_events(note, channel, bpm, division, repeats, velocity, config):
    """Build a repeated single-note burst on an exact rhythmic grid."""
    actuation = engine.resolve_note_actuation(note, channel, config)
    strike_pwm = engine.velocity_to_strike_pwm(int(velocity), actuation)
    hold_pwm = engine.strike_to_hold_pwm(strike_pwm, actuation)
    strike_ms = max(1, int(actuation["strike_ms"]))
    configured_release_ms = max(0, int(actuation.get("release_delay_ms", 0)))
    configured_rearm_ms = max(0, int(actuation.get("minimum_rearm_gap_ms", 0)))
    target_release_gap_ms = max(configured_release_ms, configured_rearm_ms)
    period = speed_test_period_ms(bpm, division)

    timeline = [(0, int(channel), 0)]
    for repeat_index in range(int(repeats)):
        start_ms = int(round(repeat_index * period))
        next_start_ms = int(round((repeat_index + 1) * period))
        available_ms = max(1, next_start_ms - start_ms)
        if available_ms <= 8:
            release_gap_ms = 0
        else:
            release_gap_ms = min(target_release_gap_ms, available_ms - 1)
        release_ms = max(start_ms + 1, next_start_ms - release_gap_ms)
        hold_start_ms = start_ms + strike_ms

        timeline.append((start_ms, int(channel), int(strike_pwm)))
        if hold_start_ms < release_ms:
            timeline.append((hold_start_ms, int(channel), int(hold_pwm)))
        timeline.append((release_ms, int(channel), 0))

    timeline.sort(key=lambda item: (item[0], 0 if item[2] == 0 else 1, item[1]))
    delta_events = [
        {"dt_ms": dt_ms, "channel": event_channel, "pwm": pwm_value}
        for dt_ms, event_channel, pwm_value in engine.convert_to_delta_events(timeline)
    ]
    return delta_events, {
        "period_ms": period,
        "strike_pwm": strike_pwm,
        "hold_pwm": hold_pwm,
        "strike_ms": strike_ms,
        "release_gap_ms": min(target_release_gap_ms, max(0, int(round(max(1, period) - 1)))),
    }


class CalibrationActionDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Note Mapping Calibration")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=APP_BG)

        self.result = None
        self.action_var = tk.StringVar(value="manual")

        outer = ttk.Frame(self, padding=18, style="App.TFrame")
        outer.grid(row=0, column=0, sticky="nsew")

        ttk.Label(
            outer,
            text="Choose a note mapping action",
            style="DialogTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            outer,
            text="Use manual mapping when the installed notes are not one clean contiguous span.",
            style="Muted.TLabel",
            wraplength=420,
        ).grid(row=1, column=0, sticky="w", pady=(6, 12))

        ttk.Radiobutton(
            outer,
            text="Sweep saved notes with playback actuation",
            variable=self.action_var,
            value="sweep",
            style="Dialog.TRadiobutton",
        ).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Radiobutton(
            outer,
            text="Save contiguous octave map",
            variable=self.action_var,
            value="contiguous",
            style="Dialog.TRadiobutton",
        ).grid(row=3, column=0, sticky="w", pady=2)
        ttk.Radiobutton(
            outer,
            text="Save manual channel-to-note map",
            variable=self.action_var,
            value="manual",
            style="Dialog.TRadiobutton",
        ).grid(row=4, column=0, sticky="w", pady=2)
        ttk.Radiobutton(
            outer,
            text="Patch existing saved map (unused channels only)",
            variable=self.action_var,
            value="patch",
            style="Dialog.TRadiobutton",
        ).grid(row=5, column=0, sticky="w", pady=2)

        button_row = ttk.Frame(outer, style="App.TFrame")
        button_row.grid(row=6, column=0, sticky="e", pady=(14, 0))
        ttk.Button(button_row, text="Cancel", style="Secondary.TButton", command=self.cancel).grid(row=0, column=0)
        ttk.Button(button_row, text="Continue", style="Primary.TButton", command=self.accept).grid(row=0, column=1, padx=(8, 0))

    def accept(self):
        self.result = self.action_var.get()
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


class TroubleshootingActionDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Key Troubleshooting")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=APP_BG)

        self.result = None
        self.key_color_var = tk.StringVar(value="white")

        outer = ttk.Frame(self, padding=18, style="App.TFrame")
        outer.grid(row=0, column=0, sticky="nsew")

        ttk.Label(
            outer,
            text="Choose a troubleshooting routine",
            style="DialogTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            outer,
            text=(
                "This uses the same installed-solenoid count, range override, export-only setting, "
                "and tempo override from the main window. Enter 0.5x there to slow the run down."
            ),
            style="Muted.TLabel",
            wraplength=440,
        ).grid(row=1, column=0, sticky="w", pady=(6, 12))

        ttk.Radiobutton(
            outer,
            text="White keys: singles, moving thirds, then widest pairs inward",
            variable=self.key_color_var,
            value="white",
            style="Dialog.TRadiobutton",
        ).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Radiobutton(
            outer,
            text="Black keys: singles, moving thirds, then widest pairs inward",
            variable=self.key_color_var,
            value="black",
            style="Dialog.TRadiobutton",
        ).grid(row=3, column=0, sticky="w", pady=2)
        ttk.Radiobutton(
            outer,
            text="Sustain pedal: strength ramp on configured channel",
            variable=self.key_color_var,
            value="pedal",
            style="Dialog.TRadiobutton",
        ).grid(row=4, column=0, sticky="w", pady=2)
        ttk.Radiobutton(
            outer,
            text="Full sweep: soft, medium, and hard chromatic passes",
            variable=self.key_color_var,
            value="full",
            style="Dialog.TRadiobutton",
        ).grid(row=5, column=0, sticky="w", pady=2)

        button_row = ttk.Frame(outer, style="App.TFrame")
        button_row.grid(row=6, column=0, sticky="e", pady=(14, 0))
        ttk.Button(button_row, text="Cancel", style="Secondary.TButton", command=self.cancel).grid(row=0, column=0)
        ttk.Button(button_row, text="Run", style="Primary.TButton", command=self.accept).grid(row=0, column=1, padx=(8, 0))

    def accept(self):
        self.result = self.key_color_var.get()
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


class PedalStrengthDialog(tk.Toplevel):
    def __init__(self, parent, defaults):
        super().__init__(parent)
        self.title("Sustain Pedal Strength Test")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=APP_BG)

        self.result = None
        self.start_pwm_var = tk.StringVar(value=str(defaults["start_pwm"]))
        self.end_pwm_var = tk.StringVar(value=str(defaults["end_pwm"]))
        self.step_pwm_var = tk.StringVar(value=str(defaults["step_pwm"]))
        self.hold_ms_var = tk.StringVar(value=str(defaults["hold_ms"]))
        self.rest_ms_var = tk.StringVar(value=str(defaults["rest_ms"]))
        self.scan_channels_var = tk.BooleanVar(value=defaults["scan_channels"])

        outer = ttk.Frame(self, padding=18, style="App.TFrame")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(1, weight=1)

        ttk.Label(outer, text="Tune sustain pedal strength", style="DialogTitle.TLabel").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
        )
        ttk.Label(
            outer,
            text=(
                "This ramps PWM upward so you can find the lowest value that depresses the pedal. "
                "Use short holds and let the solenoid cool between runs."
            ),
            style="Muted.TLabel",
            wraplength=440,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 12))

        fields = [
            ("Start PWM", self.start_pwm_var),
            ("End PWM", self.end_pwm_var),
            ("Step PWM", self.step_pwm_var),
            ("Hold ms", self.hold_ms_var),
            ("Rest ms", self.rest_ms_var),
        ]
        for row_index, (label, variable) in enumerate(fields, start=2):
            ttk.Label(outer, text=label, style="App.TLabel").grid(row=row_index, column=0, sticky="w", pady=3)
            ttk.Entry(outer, textvariable=variable, style="Panel.TEntry", width=16).grid(
                row=row_index,
                column=1,
                sticky="ew",
                padx=(14, 0),
                pady=3,
            )

        ttk.Checkbutton(
            outer,
            text="Also scan final-board candidate channels",
            variable=self.scan_channels_var,
            style="Dialog.TCheckbutton",
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))

        button_row = ttk.Frame(outer, style="App.TFrame")
        button_row.grid(row=8, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(button_row, text="Cancel", style="Secondary.TButton", command=self.cancel).grid(row=0, column=0)
        ttk.Button(button_row, text="Run Ramp", style="Primary.TButton", command=self.accept).grid(row=0, column=1, padx=(8, 0))

    def _parse_int(self, variable, label, minimum, maximum):
        raw = variable.get().strip()
        try:
            value = int(raw)
        except ValueError as error:
            raise ValueError(f"{label} must be a whole number.") from error
        if value < minimum or value > maximum:
            raise ValueError(f"{label} must be between {minimum} and {maximum}.")
        return value

    def accept(self):
        try:
            start_pwm = self._parse_int(self.start_pwm_var, "Start PWM", 0, 4095)
            end_pwm = self._parse_int(self.end_pwm_var, "End PWM", 0, 4095)
            step_pwm = self._parse_int(self.step_pwm_var, "Step PWM", 1, 4095)
            hold_ms = self._parse_int(self.hold_ms_var, "Hold ms", 50, 5000)
            rest_ms = self._parse_int(self.rest_ms_var, "Rest ms", 250, 10000)
            if end_pwm < start_pwm:
                raise ValueError("End PWM must be greater than or equal to Start PWM.")
            test_count = ((end_pwm - start_pwm + step_pwm - 1) // step_pwm) + 1
            if test_count > 30:
                raise ValueError("Use a larger Step PWM or narrower range so the ramp has 30 tests or fewer.")
            self.result = {
                "start_pwm": start_pwm,
                "end_pwm": end_pwm,
                "step_pwm": step_pwm,
                "hold_ms": hold_ms,
                "rest_ms": rest_ms,
                "scan_channels": self.scan_channels_var.get(),
            }
        except ValueError as error:
            messagebox.showerror("Invalid pedal strength value", str(error), parent=self)
            return
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


class MosfetTestDialog(tk.Toplevel):
    def __init__(self, parent, defaults):
        super().__init__(parent)
        self.title("Channel Test")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=APP_BG)

        self.result = None
        self.channel_var = tk.StringVar(value=str(defaults["channel"]))
        self.velocity_var = tk.StringVar(value=str(defaults["velocity"]))

        outer = ttk.Frame(self, padding=18, style="App.TFrame")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(1, weight=1)

        ttk.Label(outer, text="Pulse one mapped channel", style="DialogTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(
            outer,
            text="This sends one FIRE command using the same actuation math as regular song playback, then turns all PCA outputs off.",
            style="Muted.TLabel",
            wraplength=420,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 12))

        fields = [
            ("Global channel", self.channel_var),
            ("Velocity", self.velocity_var),
        ]
        for row_index, (label, variable) in enumerate(fields, start=2):
            ttk.Label(outer, text=label, style="App.TLabel").grid(row=row_index, column=0, sticky="w", pady=3)
            ttk.Entry(outer, textvariable=variable, style="Panel.TEntry", width=16).grid(
                row=row_index,
                column=1,
                sticky="ew",
                padx=(14, 0),
                pady=3,
            )

        button_row = ttk.Frame(outer, style="App.TFrame")
        button_row.grid(row=4, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(button_row, text="Cancel", style="Secondary.TButton", command=self.cancel).grid(row=0, column=0)
        ttk.Button(button_row, text="Fire Test", style="Primary.TButton", command=self.accept).grid(row=0, column=1, padx=(8, 0))

    def _parse_int(self, variable, label, minimum, maximum):
        raw = variable.get().strip()
        try:
            value = int(raw)
        except ValueError as error:
            raise ValueError(f"{label} must be a whole number.") from error
        if value < minimum or value > maximum:
            raise ValueError(f"{label} must be between {minimum} and {maximum}.")
        return value

    def accept(self):
        try:
            self.result = {
                "channel": self._parse_int(self.channel_var, "Global channel", 0, 63),
                "velocity": self._parse_int(self.velocity_var, "Velocity", 1, 127),
            }
        except ValueError as error:
            messagebox.showerror("Invalid channel test value", str(error), parent=self)
            return
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


class SolenoidSpeedTestDialog(tk.Toplevel):
    def __init__(self, parent, note_rows, defaults):
        super().__init__(parent)
        self.parent_app = parent
        self.note_rows = [dict(row) for row in note_rows]
        self.current_index = 0
        self.running = False
        self.log_entries = parent.load_speed_test_log_entries()

        self.title("Solenoid Speed Test")
        self.resizable(True, True)
        self.transient(parent)
        self.configure(bg=APP_BG)

        self.note_var = tk.StringVar()
        self.current_note_var = tk.StringVar()
        self.current_channel_var = tk.StringVar()
        self.speed_var = tk.StringVar(value=defaults.get("speed_label", SPEED_TEST_SPEED_LABELS[0]))
        self.bpm_var = tk.StringVar(value=str(defaults.get("bpm", 120)))
        self.repeats_var = tk.StringVar(value=str(defaults.get("repeats", 10)))
        self.velocity_var = tk.StringVar(value=str(defaults.get("velocity", engine.DIAGNOSTIC_MEDIUM_VELOCITY)))
        self.save_config_var = tk.BooleanVar(value=True)
        self.benchmark_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready.")
        self.slower_summary_var = tk.StringVar()

        outer = ttk.Frame(self, padding=18, style="App.TFrame")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        ttk.Label(outer, text="Single-solenoid speed test", style="DialogTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            outer,
            text="Walk the mapped notes, play repeated bursts at a selected rhythmic speed, then log whether each note meets the benchmark or blends.",
            style="Muted.TLabel",
            wraplength=620,
        ).grid(row=1, column=0, sticky="w", pady=(6, 12))

        control_frame = ttk.Frame(outer, style="App.TFrame")
        control_frame.grid(row=2, column=0, sticky="ew")
        control_frame.columnconfigure(1, weight=1)

        ttk.Label(control_frame, text="Current note", style="App.TLabel").grid(row=0, column=0, sticky="w", pady=3)
        self.note_box = ttk.Combobox(
            control_frame,
            state="readonly",
            values=[self.format_note_choice(row) for row in self.note_rows],
            textvariable=self.note_var,
            style="Panel.TCombobox",
        )
        self.note_box.grid(row=0, column=1, sticky="ew", padx=(14, 0), pady=3)
        self.note_box.bind("<<ComboboxSelected>>", self.select_note_from_box)

        ttk.Label(control_frame, text="Speed", style="App.TLabel").grid(row=1, column=0, sticky="w", pady=3)
        self.speed_box = ttk.Combobox(
            control_frame,
            state="readonly",
            values=SPEED_TEST_SPEED_LABELS,
            textvariable=self.speed_var,
            style="Panel.TCombobox",
            width=12,
        )
        self.speed_box.grid(row=1, column=1, sticky="w", padx=(14, 0), pady=3)

        ttk.Label(control_frame, text="BPM", style="App.TLabel").grid(row=2, column=0, sticky="w", pady=3)
        self.bpm_entry = ttk.Entry(control_frame, textvariable=self.bpm_var, style="Panel.TEntry", width=12)
        self.bpm_entry.grid(row=2, column=1, sticky="w", padx=(14, 0), pady=3)

        ttk.Label(control_frame, text="Repeats", style="App.TLabel").grid(row=3, column=0, sticky="w", pady=3)
        self.repeats_entry = ttk.Entry(control_frame, textvariable=self.repeats_var, style="Panel.TEntry", width=12)
        self.repeats_entry.grid(row=3, column=1, sticky="w", padx=(14, 0), pady=3)

        ttk.Label(control_frame, text="Velocity", style="App.TLabel").grid(row=4, column=0, sticky="w", pady=3)
        self.velocity_entry = ttk.Entry(control_frame, textvariable=self.velocity_var, style="Panel.TEntry", width=12)
        self.velocity_entry.grid(row=4, column=1, sticky="w", padx=(14, 0), pady=3)

        ttk.Label(control_frame, textvariable=self.current_note_var, style="Value.Panel.TLabel").grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(12, 2),
        )
        ttk.Label(control_frame, textvariable=self.current_channel_var, style="Muted.TLabel", wraplength=620).grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="w",
        )
        ttk.Label(control_frame, textvariable=self.benchmark_var, style="Muted.TLabel", wraplength=620).grid(
            row=7,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(6, 0),
        )

        note_button_row = ttk.Frame(outer, style="App.TFrame")
        note_button_row.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        note_button_row.columnconfigure(0, weight=1)
        note_button_row.columnconfigure(1, weight=1)
        note_button_row.columnconfigure(2, weight=1)
        ttk.Button(note_button_row, text="Start Lowest", style="Secondary.TButton", command=self.start_lowest).grid(
            row=0,
            column=0,
            sticky="ew",
        )
        ttk.Button(note_button_row, text="Previous Note", style="Secondary.TButton", command=self.previous_note).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(8, 0),
        )
        ttk.Button(note_button_row, text="Next Note", style="Secondary.TButton", command=self.next_note).grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(8, 0),
        )

        action_row = ttk.Frame(outer, style="App.TFrame")
        action_row.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        action_row.columnconfigure(0, weight=1)
        action_row.columnconfigure(1, weight=1)
        action_row.columnconfigure(2, weight=1)
        action_row.columnconfigure(3, weight=1)
        self.run_button = ttk.Button(action_row, text="Play Burst", style="Primary.TButton", command=self.run_current_test)
        self.run_button.grid(row=0, column=0, sticky="ew")
        ttk.Button(action_row, text="Meets Benchmark", style="Secondary.TButton", command=lambda: self.record_result("meets")).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(8, 0),
        )
        ttk.Button(action_row, text="Slower / Blends", style="Secondary.TButton", command=lambda: self.record_result("slower_blends")).grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(8, 0),
        )
        ttk.Button(action_row, text="Save Current Settings", style="Secondary.TButton", command=self.save_current_settings).grid(
            row=0,
            column=3,
            sticky="ew",
            padx=(8, 0),
        )

        ttk.Checkbutton(
            outer,
            text="Save velocity and repeat speed to this solenoid's global config when logging",
            variable=self.save_config_var,
            style="Dialog.TCheckbutton",
        ).grid(row=5, column=0, sticky="w", pady=(10, 0))

        ttk.Label(outer, textvariable=self.status_var, style="Status.Panel.TLabel").grid(row=6, column=0, sticky="w", pady=(12, 4))
        ttk.Label(outer, textvariable=self.slower_summary_var, style="Muted.TLabel", wraplength=620).grid(
            row=7,
            column=0,
            sticky="w",
            pady=(0, 10),
        )

        results_frame = ttk.Frame(outer, style="App.TFrame")
        results_frame.grid(row=8, column=0, sticky="nsew")
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        outer.rowconfigure(8, weight=1)
        self.results_listbox = tk.Listbox(
            results_frame,
            height=8,
            bg=INPUT_BG,
            fg=TEXT_COLOR,
            selectbackground=ACCENT_SOFT,
            selectforeground=TEXT_COLOR,
            highlightthickness=1,
            highlightbackground=INPUT_BORDER,
            relief="flat",
            activestyle="none",
            font=("Consolas", 9),
        )
        self.results_listbox.grid(row=0, column=0, sticky="nsew")
        results_scrollbar = ttk.Scrollbar(
            results_frame,
            orient="vertical",
            style="Panel.Vertical.TScrollbar",
            command=self.results_listbox.yview,
        )
        results_scrollbar.grid(row=0, column=1, sticky="ns", padx=(10, 0))
        self.results_listbox.configure(yscrollcommand=results_scrollbar.set)

        self.speed_var.trace_add("write", lambda *_args: self.refresh_benchmark())
        self.bpm_var.trace_add("write", lambda *_args: self.refresh_benchmark())

        self.set_note_index(0)
        self.refresh_benchmark()
        self.refresh_log_view()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda _event: self.close())
        self.update_idletasks()
        x = parent.winfo_rootx() + max(40, (parent.winfo_width() - self.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(40, (parent.winfo_height() - self.winfo_height()) // 4)
        self.geometry(f"+{x}+{y}")
        self.lift(parent)
        self.focus_set()

    def format_note_choice(self, row):
        return f"{row['note_label']} ({row['note']}) | channel {row['channel']}"

    def current_row(self):
        return self.note_rows[self.current_index]

    def format_saved_settings(self, row):
        saved_parts = []
        saved_velocity = row.get("saved_playback_velocity_override")
        saved_period = row.get("saved_minimum_repeat_period_ms")
        if saved_velocity not in (None, ""):
            saved_parts.append(f"saved velocity {saved_velocity}")
        if saved_period not in (None, "") and int(saved_period) > 0:
            saved_parts.append(f"minimum repeat {saved_period} ms")
        if not saved_parts:
            return "Saved solenoid settings: none yet"
        return "Saved solenoid settings: " + ", ".join(saved_parts)

    def set_note_index(self, index):
        if not self.note_rows:
            return
        self.current_index = max(0, min(len(self.note_rows) - 1, int(index)))
        row = self.current_row()
        self.note_var.set(self.format_note_choice(row))
        self.current_note_var.set(f"{row['note_label']} ({row['note']})")
        saved_velocity = row.get("saved_playback_velocity_override")
        if saved_velocity not in (None, ""):
            self.velocity_var.set(str(saved_velocity))
        else:
            self.velocity_var.set(str(engine.DIAGNOSTIC_MEDIUM_VELOCITY))
        self.current_channel_var.set(
            f"{row['channel_target']} | {row['channel_label']}\n{self.format_saved_settings(row)}"
        )

    def select_note_from_box(self, _event=None):
        selected = self.note_var.get()
        for index, row in enumerate(self.note_rows):
            if self.format_note_choice(row) == selected:
                self.set_note_index(index)
                break

    def start_lowest(self):
        self.set_note_index(0)

    def previous_note(self):
        self.set_note_index(self.current_index - 1)

    def next_note(self):
        self.set_note_index(self.current_index + 1)

    def parse_request(self):
        row = self.current_row()
        try:
            bpm = float(self.bpm_var.get().strip())
        except ValueError as error:
            raise ValueError("BPM must be a number.") from error
        if bpm < 20 or bpm > 400:
            raise ValueError("BPM must be between 20 and 400.")

        try:
            repeats = int(self.repeats_var.get().strip())
        except ValueError as error:
            raise ValueError("Repeats must be a whole number.") from error
        if repeats < 1 or repeats > 64:
            raise ValueError("Repeats must be between 1 and 64.")

        try:
            velocity = int(self.velocity_var.get().strip())
        except ValueError as error:
            raise ValueError("Velocity must be a whole number.") from error
        if velocity < 1 or velocity > 127:
            raise ValueError("Velocity must be between 1 and 127.")

        speed_label = self.speed_var.get()
        division = speed_test_division_for_label(speed_label)
        period_ms = speed_test_period_ms(bpm, division)
        return {
            "note": int(row["note"]),
            "note_label": row["note_label"],
            "channel": int(row["channel"]),
            "channel_label": row["channel_label"],
            "channel_target": row["channel_target"],
            "speed_label": speed_label,
            "division": division,
            "bpm": bpm,
            "period_ms": period_ms,
            "repeats": repeats,
            "velocity": velocity,
        }

    def refresh_benchmark(self):
        try:
            request = self.parse_request()
        except Exception:
            self.benchmark_var.set("Benchmark timing updates after BPM and speed are valid.")
            return
        self.benchmark_var.set(
            f"Benchmark: {request['speed_label']} at {request['bpm']:.2f} BPM "
            f"= {request['period_ms']:.1f} ms between strikes."
        )

    def run_current_test(self):
        try:
            request = self.parse_request()
        except ValueError as error:
            messagebox.showerror("Invalid speed test value", str(error), parent=self)
            return
        self.parent_app.start_speed_test_burst(request)

    def set_running(self, running):
        self.running = bool(running)
        self.run_button.configure(state="disabled" if self.running else "normal")
        if self.running:
            self.status_var.set("Playing burst...")

    def speed_test_finished(self, result=None, error_message=None):
        self.set_running(False)
        if error_message:
            self.status_var.set(f"Speed test failed: {error_message}")
            return
        if not result:
            self.status_var.set("Ready.")
            return
        self.status_var.set(
            f"Played {result['note_label']} at {result['speed_label']} "
            f"({result['period_ms']:.1f} ms between strikes)."
        )

    def record_result(self, status):
        try:
            request = self.parse_request()
        except ValueError as error:
            messagebox.showerror("Invalid speed test value", str(error), parent=self)
            return
        entry = self.parent_app.build_speed_test_log_entry(request, status)
        saved_settings = None
        if self.save_config_var.get():
            saved_settings = self.parent_app.save_speed_test_solenoid_settings(request, status)
            entry["saved_to_config"] = True
            entry["saved_minimum_repeat_period_ms"] = saved_settings["minimum_repeat_period_ms"]
            entry["saved_playback_velocity_override"] = saved_settings["playback_velocity_override"]
        self.log_entries = self.parent_app.append_speed_test_log_entry(entry)
        if saved_settings is not None:
            self.apply_saved_settings_to_current_row(saved_settings)
        self.refresh_log_view()
        status_label = "meets benchmark" if status == "meets" else "slower / blends"
        config_text = " and saved to solenoid config" if saved_settings is not None else ""
        self.status_var.set(f"Logged {entry['note_label']} as {status_label} at {entry['speed_label']}{config_text}.")

    def save_current_settings(self):
        try:
            request = self.parse_request()
        except ValueError as error:
            messagebox.showerror("Invalid speed test value", str(error), parent=self)
            return
        saved_settings = self.parent_app.save_speed_test_solenoid_settings(request, "manual_save")
        self.apply_saved_settings_to_current_row(saved_settings)
        self.status_var.set(
            f"Saved {request['note_label']} velocity {saved_settings['playback_velocity_override']} "
            f"and minimum repeat {saved_settings['minimum_repeat_period_ms']} ms to solenoid config."
        )

    def apply_saved_settings_to_current_row(self, saved_settings):
        row = self.current_row()
        row["saved_playback_velocity_override"] = saved_settings["playback_velocity_override"]
        row["saved_minimum_repeat_period_ms"] = saved_settings["minimum_repeat_period_ms"]
        self.set_note_index(self.current_index)

    def refresh_log_view(self):
        self.results_listbox.delete(0, tk.END)
        visible_entries = self.log_entries[-100:]
        for entry in visible_entries:
            status = "OK" if entry.get("status") == "meets" else "SLOW"
            self.results_listbox.insert(
                tk.END,
                (
                    f"{entry.get('timestamp', '')[:19]}  {status:<4}  "
                    f"{entry.get('note_label', '?'):>4} ch {entry.get('channel', '?'):>2}  "
                    f"{entry.get('speed_label', '?'):>5} @ {float(entry.get('bpm', 0)):.1f} BPM"
                ),
            )
        if visible_entries:
            self.results_listbox.see(tk.END)

        slow_entries = [entry for entry in self.log_entries if entry.get("status") == "slower_blends"]
        if not slow_entries:
            self.slower_summary_var.set("Slower/blending notes logged: none")
            return

        unique = []
        seen = set()
        for entry in reversed(slow_entries):
            key = (entry.get("note"), entry.get("speed_label"), entry.get("bpm"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(f"{entry.get('note_label')} @ {entry.get('speed_label')}")
            if len(unique) >= 12:
                break
        summary = ", ".join(reversed(unique))
        extra = "" if len(slow_entries) <= len(unique) else f" ({len(slow_entries)} total slow logs)"
        self.slower_summary_var.set(f"Slower/blending notes logged: {summary}{extra}")

    def close(self):
        self.parent_app.speed_test_dialog = None
        self.destroy()


class DefectiveNoteDebugDialog(tk.Toplevel):
    def __init__(self, parent, note_rows):
        super().__init__(parent)
        self.parent_app = parent
        self.note_rows = [dict(row) for row in note_rows]
        self.current_index = 0

        self.title("Defective Note Debug")
        self.resizable(True, True)
        self.transient(parent)
        self.configure(bg=APP_BG)

        self.note_var = tk.StringVar()
        self.current_note_var = tk.StringVar()
        self.current_channel_var = tk.StringVar()
        self.current_settings_var = tk.StringVar()
        self.speed_var = tk.StringVar(value="32nds")
        self.bpm_var = tk.StringVar(value="80")
        self.repeats_var = tk.StringVar(value="10")
        self.velocity_var = tk.StringVar(value=str(engine.DIAGNOSTIC_MEDIUM_VELOCITY))
        self.strike_min_pwm_var = tk.StringVar()
        self.rearm_gap_ms_var = tk.StringVar()
        self.min_repeat_ms_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready.")

        outer = ttk.Frame(self, padding=18, style="App.TFrame")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        ttk.Label(outer, text="Defective note debug", style="DialogTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            outer,
            text=(
                "This walks only the notes whose latest speed-test result is slower / blends. "
                "For clicky notes at velocity 1, lower strike min PWM. For blending notes, raise the minimum repeat period."
            ),
            style="Muted.TLabel",
            wraplength=680,
        ).grid(row=1, column=0, sticky="w", pady=(6, 12))

        control_frame = ttk.Frame(outer, style="App.TFrame")
        control_frame.grid(row=2, column=0, sticky="ew")
        control_frame.columnconfigure(1, weight=1)

        ttk.Label(control_frame, text="Current note", style="App.TLabel").grid(row=0, column=0, sticky="w", pady=3)
        self.note_box = ttk.Combobox(
            control_frame,
            state="readonly",
            values=[self.format_note_choice(row) for row in self.note_rows],
            textvariable=self.note_var,
            style="Panel.TCombobox",
        )
        self.note_box.grid(row=0, column=1, sticky="ew", padx=(14, 0), pady=3)
        self.note_box.bind("<<ComboboxSelected>>", self.select_note_from_box)

        ttk.Label(control_frame, textvariable=self.current_note_var, style="Value.Panel.TLabel").grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(12, 2),
        )
        ttk.Label(control_frame, textvariable=self.current_channel_var, style="Muted.TLabel", wraplength=680).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
        )
        ttk.Label(control_frame, textvariable=self.current_settings_var, style="Muted.TLabel", wraplength=680).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(4, 0),
        )

        test_frame = ttk.LabelFrame(outer, text="Playback Test", style="Section.TLabelframe")
        test_frame.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        test_body = ttk.Frame(test_frame, padding=12, style="Panel.TFrame")
        test_body.grid(row=0, column=0, sticky="ew")
        test_body.columnconfigure(1, weight=1)
        test_body.columnconfigure(3, weight=1)

        test_fields = [
            ("Speed", self.speed_var, SPEED_TEST_SPEED_LABELS, 0),
            ("BPM", self.bpm_var, None, 1),
            ("Repeats", self.repeats_var, None, 2),
            ("Velocity", self.velocity_var, None, 3),
        ]
        for label, variable, choices, column in test_fields:
            ttk.Label(test_body, text=label, style="Panel.TLabel").grid(row=0, column=column * 2, sticky="w", pady=3)
            if choices is None:
                widget = ttk.Entry(test_body, textvariable=variable, style="Panel.TEntry", width=10)
            else:
                widget = ttk.Combobox(
                    test_body,
                    state="readonly",
                    values=choices,
                    textvariable=variable,
                    style="Panel.TCombobox",
                    width=10,
                )
            widget.grid(row=0, column=column * 2 + 1, sticky="w", padx=(8, 14), pady=3)

        test_button_row = ttk.Frame(test_body, style="Panel.TFrame")
        test_button_row.grid(row=1, column=0, columnspan=8, sticky="ew", pady=(10, 0))
        test_button_row.columnconfigure(0, weight=1)
        test_button_row.columnconfigure(1, weight=1)
        ttk.Button(test_button_row, text="Play Single Pulse", style="Secondary.TButton", command=self.play_single_pulse).grid(
            row=0,
            column=0,
            sticky="ew",
        )
        ttk.Button(test_button_row, text="Play Repeat Burst", style="Primary.TButton", command=self.play_repeat_burst).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(8, 0),
        )

        tune_frame = ttk.LabelFrame(outer, text="Scoped Fixes", style="Section.TLabelframe")
        tune_frame.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        tune_body = ttk.Frame(tune_frame, padding=12, style="Panel.TFrame")
        tune_body.grid(row=0, column=0, sticky="ew")
        tune_body.columnconfigure(1, weight=1)

        ttk.Label(tune_body, text="Clicky fix: strike min PWM", style="Panel.TLabel").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(tune_body, textvariable=self.strike_min_pwm_var, style="Panel.TEntry", width=12).grid(
            row=0,
            column=1,
            sticky="w",
            padx=(14, 0),
            pady=3,
        )
        click_button_row = ttk.Frame(tune_body, style="Panel.TFrame")
        click_button_row.grid(row=0, column=2, sticky="w", padx=(8, 0), pady=3)
        ttk.Button(click_button_row, text="-25", style="Secondary.TButton", command=lambda: self.adjust_strike_min_pwm(-25)).grid(row=0, column=0)
        ttk.Button(click_button_row, text="-100", style="Secondary.TButton", command=lambda: self.adjust_strike_min_pwm(-100)).grid(row=0, column=1, padx=(6, 0))
        ttk.Button(click_button_row, text="Save Click Fix", style="Primary.TButton", command=self.save_click_fix).grid(row=0, column=2, padx=(6, 0))

        ttk.Label(tune_body, text="Retraction gap ms", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(tune_body, textvariable=self.rearm_gap_ms_var, style="Panel.TEntry", width=12).grid(
            row=1,
            column=1,
            sticky="w",
            padx=(14, 0),
            pady=3,
        )
        blend_button_row = ttk.Frame(tune_body, style="Panel.TFrame")
        blend_button_row.grid(row=1, column=2, sticky="w", padx=(8, 0), pady=3)
        ttk.Button(blend_button_row, text="+10", style="Secondary.TButton", command=lambda: self.adjust_rearm_gap_ms(10)).grid(row=0, column=0)
        ttk.Button(blend_button_row, text="+25", style="Secondary.TButton", command=lambda: self.adjust_rearm_gap_ms(25)).grid(row=0, column=1, padx=(6, 0))

        ttk.Label(tune_body, text="Minimum repeat ms", style="Panel.TLabel").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(tune_body, textvariable=self.min_repeat_ms_var, style="Panel.TEntry", width=12).grid(
            row=2,
            column=1,
            sticky="w",
            padx=(14, 0),
            pady=3,
        )
        repeat_button_row = ttk.Frame(tune_body, style="Panel.TFrame")
        repeat_button_row.grid(row=2, column=2, sticky="w", padx=(8, 0), pady=3)
        ttk.Button(repeat_button_row, text="+10", style="Secondary.TButton", command=lambda: self.adjust_min_repeat_ms(10)).grid(row=0, column=0)
        ttk.Button(repeat_button_row, text="+25", style="Secondary.TButton", command=lambda: self.adjust_min_repeat_ms(25)).grid(row=0, column=1, padx=(6, 0))
        ttk.Button(repeat_button_row, text="Save Blend Fix", style="Primary.TButton", command=self.save_blend_fix).grid(row=0, column=2, padx=(6, 0))

        nav_row = ttk.Frame(outer, style="App.TFrame")
        nav_row.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        nav_row.columnconfigure(0, weight=1)
        nav_row.columnconfigure(1, weight=1)
        nav_row.columnconfigure(2, weight=1)
        ttk.Button(nav_row, text="Previous Note", style="Secondary.TButton", command=self.previous_note).grid(row=0, column=0, sticky="ew")
        ttk.Button(nav_row, text="Next Note", style="Secondary.TButton", command=self.next_note).grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(nav_row, text="Close", style="Secondary.TButton", command=self.close).grid(row=0, column=2, sticky="ew", padx=(8, 0))

        ttk.Label(outer, textvariable=self.status_var, style="Status.Panel.TLabel").grid(
            row=6,
            column=0,
            sticky="w",
            pady=(12, 0),
        )

        self.set_note_index(0)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda _event: self.close())
        self.update_idletasks()
        x = parent.winfo_rootx() + max(40, (parent.winfo_width() - self.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(40, (parent.winfo_height() - self.winfo_height()) // 5)
        self.geometry(f"+{x}+{y}")
        self.lift(parent)
        self.focus_set()

    def format_note_choice(self, row):
        reason = row.get("source_speed_label", "32nds")
        return f"{row['note_label']} ({row['note']}) | channel {row['channel']} | {reason}"

    def current_row(self):
        return self.note_rows[self.current_index]

    def set_note_index(self, index):
        if not self.note_rows:
            return
        self.current_index = max(0, min(len(self.note_rows) - 1, int(index)))
        row = self.current_row()
        self.note_var.set(self.format_note_choice(row))
        self.current_note_var.set(f"{row['note_label']} ({row['note']})")
        self.speed_var.set(row.get("source_speed_label") or "32nds")
        self.bpm_var.set(f"{float(row.get('source_bpm', 80.0)):.2f}".rstrip("0").rstrip("."))
        self.repeats_var.set(str(int(row.get("source_repeats", 10))))
        velocity = row.get("saved_playback_velocity_override")
        if velocity in (None, ""):
            velocity = row.get("source_velocity", engine.DIAGNOSTIC_MEDIUM_VELOCITY)
        self.velocity_var.set(str(int(velocity)))
        self.strike_min_pwm_var.set(str(int(row["strike_min_pwm"])))
        self.rearm_gap_ms_var.set(str(int(row["minimum_rearm_gap_ms"])))
        self.min_repeat_ms_var.set(str(int(row.get("minimum_repeat_period_ms") or 0)))
        self.refresh_current_labels()

    def refresh_current_labels(self):
        row = self.current_row()
        self.current_channel_var.set(
            f"{row['channel_target']} | {row['channel_label']} | latest failed test: "
            f"{row.get('source_speed_label', '32nds')} at {float(row.get('source_bpm', 80.0)):.2f} BPM"
        )
        self.current_settings_var.set(
            "Current scoped settings: "
            f"velocity override {row.get('saved_playback_velocity_override', 'none')}, "
            f"strike min/max {row['strike_min_pwm']}/{row['strike_max_pwm']}, "
            f"strike {row['strike_ms']} ms, hold {row['hold_min_pwm']}-{row['hold_max_pwm']} "
            f"ratio {row['hold_ratio']}, release {row['release_delay_ms']} ms, "
            f"retraction gap {row['minimum_rearm_gap_ms']} ms, "
            f"minimum repeat {row.get('minimum_repeat_period_ms') or 0} ms"
        )

    def select_note_from_box(self, _event=None):
        selected = self.note_var.get()
        for index, row in enumerate(self.note_rows):
            if self.format_note_choice(row) == selected:
                self.set_note_index(index)
                break

    def previous_note(self):
        self.set_note_index(self.current_index - 1)

    def next_note(self):
        self.set_note_index(self.current_index + 1)

    def _parse_int(self, variable, label, minimum, maximum):
        raw = variable.get().strip()
        try:
            value = int(raw)
        except ValueError as error:
            raise ValueError(f"{label} must be a whole number.") from error
        if value < minimum or value > maximum:
            raise ValueError(f"{label} must be between {minimum} and {maximum}.")
        return value

    def parse_speed_request(self):
        row = self.current_row()
        try:
            bpm = float(self.bpm_var.get().strip())
        except ValueError as error:
            raise ValueError("BPM must be a number.") from error
        if bpm < 20 or bpm > 400:
            raise ValueError("BPM must be between 20 and 400.")
        repeats = self._parse_int(self.repeats_var, "Repeats", 1, 64)
        velocity = self._parse_int(self.velocity_var, "Velocity", 1, 127)
        speed_label = self.speed_var.get()
        division = speed_test_division_for_label(speed_label)
        period_ms = speed_test_period_ms(bpm, division)
        return {
            "note": int(row["note"]),
            "note_label": row["note_label"],
            "channel": int(row["channel"]),
            "channel_label": row["channel_label"],
            "channel_target": row["channel_target"],
            "speed_label": speed_label,
            "division": division,
            "bpm": bpm,
            "period_ms": period_ms,
            "repeats": repeats,
            "velocity": velocity,
        }

    def play_single_pulse(self):
        try:
            velocity = self._parse_int(self.velocity_var, "Velocity", 1, 127)
        except ValueError as error:
            messagebox.showerror("Invalid debug value", str(error), parent=self)
            return
        row = self.current_row()
        self.status_var.set(f"Playing one pulse for {row['note_label']}...")
        self.parent_app.start_defective_note_single_pulse(row, velocity)

    def play_repeat_burst(self):
        try:
            request = self.parse_speed_request()
        except ValueError as error:
            messagebox.showerror("Invalid debug value", str(error), parent=self)
            return
        self.status_var.set(f"Playing repeat burst for {request['note_label']}...")
        self.parent_app.start_speed_test_burst(request)

    def adjust_strike_min_pwm(self, delta):
        try:
            value = self._parse_int(self.strike_min_pwm_var, "Strike min PWM", 0, 4095)
        except ValueError:
            value = int(self.current_row()["strike_min_pwm"])
        self.strike_min_pwm_var.set(str(max(0, min(4095, value + int(delta)))))

    def adjust_min_repeat_ms(self, delta):
        try:
            value = self._parse_int(self.min_repeat_ms_var, "Minimum repeat ms", 0, 2000)
        except ValueError:
            value = int(self.current_row().get("minimum_repeat_period_ms") or 0)
        self.min_repeat_ms_var.set(str(max(0, min(2000, value + int(delta)))))

    def adjust_rearm_gap_ms(self, delta):
        try:
            value = self._parse_int(self.rearm_gap_ms_var, "Retraction gap ms", 0, 2000)
        except ValueError:
            value = int(self.current_row()["minimum_rearm_gap_ms"])
        self.rearm_gap_ms_var.set(str(max(0, min(2000, value + int(delta)))))

    def save_click_fix(self):
        row = self.current_row()
        try:
            strike_min_pwm = self._parse_int(self.strike_min_pwm_var, "Strike min PWM", 0, 4095)
        except ValueError as error:
            messagebox.showerror("Invalid click fix", str(error), parent=self)
            return
        if strike_min_pwm > int(row["strike_max_pwm"]):
            messagebox.showerror(
                "Invalid click fix",
                "Strike min PWM cannot be higher than this solenoid's strike max PWM.",
                parent=self,
            )
            return
        saved_settings = self.parent_app.save_defect_debug_solenoid_settings(
            row,
            {"strike_min_pwm": strike_min_pwm},
            "click_fix",
        )
        self.apply_saved_settings(saved_settings)
        self.status_var.set(f"Saved click fix for {row['note_label']}: strike min PWM {strike_min_pwm}.")

    def save_blend_fix(self):
        row = self.current_row()
        try:
            rearm_gap_ms = self._parse_int(self.rearm_gap_ms_var, "Retraction gap ms", 0, 2000)
            minimum_repeat_ms = self._parse_int(self.min_repeat_ms_var, "Minimum repeat ms", 0, 2000)
        except ValueError as error:
            messagebox.showerror("Invalid blend fix", str(error), parent=self)
            return
        saved_settings = self.parent_app.save_defect_debug_solenoid_settings(
            row,
            {
                "minimum_rearm_gap_ms": rearm_gap_ms,
                "retrigger_gap_ms": min(rearm_gap_ms, max(0, int(round(rearm_gap_ms * 0.75)))),
                "minimum_repeat_period_ms": minimum_repeat_ms,
            },
            "blend_fix",
        )
        self.apply_saved_settings(saved_settings)
        self.status_var.set(
            f"Saved blend fix for {row['note_label']}: retraction gap {rearm_gap_ms} ms, "
            f"minimum repeat {minimum_repeat_ms} ms."
        )

    def apply_saved_settings(self, saved_settings):
        row = self.current_row()
        row.update(saved_settings)
        self.strike_min_pwm_var.set(str(int(row["strike_min_pwm"])))
        self.rearm_gap_ms_var.set(str(int(row["minimum_rearm_gap_ms"])))
        self.min_repeat_ms_var.set(str(int(row.get("minimum_repeat_period_ms") or 0)))
        self.refresh_current_labels()

    def close(self):
        self.parent_app.defect_debug_dialog = None
        self.destroy()


class PlaybackControlState:
    def __init__(self):
        self.lock = threading.Lock()
        self._pause_requested = False
        self._paused = False
        self._action = None
        self._note_marker_plan = []
        self._note_marker_started_at = None
        self._marked_note_steps = []
        self._marked_step_indexes = set()

    def request_pause(self):
        with self.lock:
            self._pause_requested = True

    def request_resume(self):
        with self.lock:
            self._pause_requested = False

    def request_skip(self):
        with self.lock:
            self._action = "skip"
            self._pause_requested = False

    def request_replay(self):
        with self.lock:
            self._action = "replay"
            self._pause_requested = False

    def pause_requested(self):
        with self.lock:
            return self._pause_requested

    def consume_action(self):
        with self.lock:
            action = self._action
            self._action = None
            return action

    def set_paused(self, paused):
        with self.lock:
            self._paused = bool(paused)

    def is_paused(self):
        with self.lock:
            return self._paused

    def is_pause_requested(self):
        with self.lock:
            return self._pause_requested

    def configure_note_marker_plan(self, step_plan):
        with self.lock:
            self._note_marker_plan = [dict(step) for step in step_plan]
            self._note_marker_started_at = None
            self._marked_note_steps = []
            self._marked_step_indexes = set()

    def playback_started(self):
        with self.lock:
            if self._note_marker_plan:
                self._note_marker_started_at = time.monotonic()

    def note_marker_active(self):
        with self.lock:
            return bool(self._note_marker_plan) and self._note_marker_started_at is not None

    def mark_previous_note_step(self):
        with self.lock:
            if not self._note_marker_plan:
                return None, "No full-sweep note marker plan is active."
            if self._note_marker_started_at is None:
                return None, "Full-sweep playback has not started yet."

            elapsed_ms = int(round((time.monotonic() - self._note_marker_started_at) * 1000))
            previous_step = None
            for step in self._note_marker_plan:
                if int(step["start_ms"]) <= elapsed_ms:
                    previous_step = step
                else:
                    break

            if previous_step is None:
                return None, "No note has played yet."

            step_index = int(previous_step["index"])
            if step_index in self._marked_step_indexes:
                return previous_step, "already_marked"

            self._marked_step_indexes.add(step_index)
            self._marked_note_steps.append(dict(previous_step))
            return previous_step, None

    def get_marked_note_steps(self):
        with self.lock:
            return [dict(step) for step in self._marked_note_steps]

    def get_marked_note_lines(self):
        lines = []
        for step in self.get_marked_note_steps():
            notes = " + ".join(step.get("note_labels", []))
            velocity = step.get("velocity")
            phase = step.get("phase_name", "sweep")
            lines.append(f"{notes} (velocity {velocity}, {phase})")
        return lines


class PianoPlayerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Autonomous Piano Player")
        self.geometry("1020x920")
        self.minsize(900, 780)
        self._configure_theme()

        self.user_preferences = engine.load_user_preferences()
        self.config_data = engine.load_config()
        self.song_catalog = None
        self.selected_song_path = None
        self.selection_reason = ""
        self.song_selection_is_manual = False
        self.worker = None
        self.message_queue = queue.Queue()
        self.filtered_song_entries = []
        self.song_catalog_refresh_in_progress = False
        self.pending_song_catalog_refresh = None
        self.selection_flash_after_id = None
        self.completion_dialog = None
        self.playback_queue = []
        self.queue_lock = threading.Lock()
        self.current_queue_item = None
        self.queue_is_playing = False
        self.playback_control = None
        self.note_marker_control = None
        self.sweep_marker_dialog = None
        self.speed_test_dialog = None
        self.defect_debug_dialog = None
        self.sweep_marker_text_var = tk.StringVar(value="")
        self.playback_locked_widgets = []
        self.mosfet_test_defaults = None
        playback_preferences = self.user_preferences.get("playback", {})
        default_active_channels = playback_preferences.get(
            "default_active_channels",
            len(engine.get_mapping_channel_order(self.config_data["mapping"])),
        )
        default_playable_range = playback_preferences.get("default_playable_range", "")
        default_fit_mode = playback_preferences.get("default_fit_mode", "strict")
        if default_fit_mode not in {"strict", "transpose"}:
            default_fit_mode = "strict"

        self.song_name_var = tk.StringVar(value="No song selected")
        self.song_reason_var = tk.StringVar(value="")
        self.song_info_var = tk.StringVar(value="No MIDI selected yet.")
        self.song_catalog_status_var = tk.StringVar(value="Loading available songs...")
        self.song_search_var = tk.StringVar(value="")
        self.queue_status_var = tk.StringVar(value="Queue empty.")
        self.active_channels_var = tk.StringVar(value=str(default_active_channels))
        self.tempo_var = tk.StringVar(value="")
        self.range_var = tk.StringVar(value=str(default_playable_range))
        self.fit_mode_var = tk.StringVar(value=default_fit_mode)
        self.performance_feel_var = tk.BooleanVar(value=False)
        self.auto_measure_pedal_var = tk.BooleanVar(value=False)
        self.export_only_var = tk.BooleanVar(value=False)

        self._build_layout()
        self.bind_all("<Return>", self.handle_note_marker_return, add="+")
        self.bind_all("<KP_Enter>", self.handle_note_marker_return, add="+")
        self.bind_all("<space>", self.handle_note_marker_return, add="+")
        self.refresh_song_catalog(use_suggested=True, recursive_downloads=False)
        self.refresh_song_catalog_async(use_suggested=True)
        self.after(100, self.process_worker_messages)

    def _configure_theme(self):
        self.configure(bg=APP_BG)

        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Segoe UI", size=10)
        tkfont.nametofont("TkTextFont").configure(family="Segoe UI", size=10)
        tkfont.nametofont("TkFixedFont").configure(family="Consolas", size=10)
        tkfont.nametofont("TkHeadingFont").configure(family="Segoe UI", size=10, weight="bold")

        style = ttk.Style(self)
        self.style = style
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("App.TFrame", background=APP_BG)
        style.configure("Hero.TFrame", background=HERO_BG)
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure("Section.TLabelframe", background=APP_BG, borderwidth=1, relief="solid")
        style.configure(
            "Section.TLabelframe.Label",
            background=APP_BG,
            foreground=TEXT_COLOR,
            font=("Segoe UI", 10, "bold"),
        )

        style.configure("HeroTitle.TLabel", background=HERO_BG, foreground="#ffffff", font=("Segoe UI", 19, "bold"))
        style.configure("HeroSubtitle.TLabel", background=HERO_BG, foreground="#c1cad6", font=("Segoe UI", 10))
        style.configure("HeroMeta.TLabel", background=HERO_BG, foreground="#9fb0c5", font=("Segoe UI", 9))

        style.configure("Panel.TLabel", background=PANEL_BG, foreground=TEXT_COLOR, font=("Segoe UI", 10))
        style.configure("Muted.Panel.TLabel", background=PANEL_BG, foreground=MUTED_TEXT, font=("Segoe UI", 9))
        style.configure("Status.Panel.TLabel", background=PANEL_BG, foreground=ACCENT_COLOR, font=("Segoe UI", 9, "bold"))
        style.configure("Value.Panel.TLabel", background=PANEL_BG, foreground=TEXT_COLOR, font=("Segoe UI", 12, "bold"))
        style.configure("Selected.Value.Panel.TLabel", background=ACCENT_SOFT, foreground=TEXT_COLOR, font=("Segoe UI", 12, "bold"))
        style.configure("Selected.Status.Panel.TLabel", background=ACCENT_SOFT, foreground=ACCENT_COLOR, font=("Segoe UI", 9, "bold"))

        style.configure("App.TLabel", background=APP_BG, foreground=TEXT_COLOR, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=APP_BG, foreground=MUTED_TEXT, font=("Segoe UI", 9))
        style.configure("DialogTitle.TLabel", background=APP_BG, foreground=TEXT_COLOR, font=("Segoe UI", 11, "bold"))

        button_padding = (14, 9)
        style.configure(
            "Primary.TButton",
            background=ACCENT_COLOR,
            foreground="#ffffff",
            borderwidth=0,
            focusthickness=0,
            padding=button_padding,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER), ("disabled", "#b9cdc5")],
            foreground=[("disabled", "#eef4f1")],
        )

        style.configure(
            "Secondary.TButton",
            background=PANEL_BG,
            foreground=TEXT_COLOR,
            borderwidth=1,
            relief="solid",
            bordercolor=BORDER_COLOR,
            lightcolor=BORDER_COLOR,
            darkcolor=BORDER_COLOR,
            padding=button_padding,
            font=("Segoe UI", 10),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#f6f8fa"), ("pressed", "#edf2f6"), ("disabled", "#f3f5f7")],
            foreground=[("disabled", "#9aa5b1")],
            bordercolor=[("focus", ACCENT_COLOR), ("active", INPUT_BORDER)],
        )

        style.configure(
            "Panel.TEntry",
            fieldbackground=INPUT_BG,
            foreground=TEXT_COLOR,
            bordercolor=INPUT_BORDER,
            lightcolor=INPUT_BORDER,
            darkcolor=INPUT_BORDER,
            insertcolor=TEXT_COLOR,
            padding=(10, 8),
        )
        style.map("Panel.TEntry", bordercolor=[("focus", ACCENT_COLOR)])

        style.configure(
            "Panel.TCombobox",
            fieldbackground=INPUT_BG,
            foreground=TEXT_COLOR,
            bordercolor=INPUT_BORDER,
            lightcolor=INPUT_BORDER,
            darkcolor=INPUT_BORDER,
            arrowcolor=MUTED_TEXT,
            padding=(8, 6),
        )
        style.map(
            "Panel.TCombobox",
            bordercolor=[("focus", ACCENT_COLOR)],
            fieldbackground=[("readonly", INPUT_BG)],
            selectbackground=[("readonly", INPUT_BG)],
            selectforeground=[("readonly", TEXT_COLOR)],
        )

        style.configure("Panel.TCheckbutton", background=PANEL_BG, foreground=TEXT_COLOR, font=("Segoe UI", 10))
        style.map("Panel.TCheckbutton", background=[("active", PANEL_BG)])
        style.configure("Dialog.TRadiobutton", background=APP_BG, foreground=TEXT_COLOR, font=("Segoe UI", 10))
        style.map("Dialog.TRadiobutton", background=[("active", APP_BG)])
        style.configure("Dialog.TCheckbutton", background=APP_BG, foreground=TEXT_COLOR, font=("Segoe UI", 10))
        style.map("Dialog.TCheckbutton", background=[("active", APP_BG)])

        style.configure(
            "Panel.Vertical.TScrollbar",
            background="#cfd7e0",
            troughcolor="#f4f7fa",
            bordercolor=BORDER_COLOR,
            arrowcolor=MUTED_TEXT,
            lightcolor="#cfd7e0",
            darkcolor="#cfd7e0",
        )

    def _create_section_body(self, parent, padding=(16, 16, 16, 16)):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        body = ttk.Frame(parent, style="Panel.TFrame", padding=padding)
        body.grid(row=0, column=0, sticky="nsew")
        return body

    def _sync_canvas_scrollregion(self, _event=None):
        self.page_canvas.configure(scrollregion=self.page_canvas.bbox("all"))

    def _sync_canvas_width(self, event):
        self.page_canvas.itemconfigure(self.page_window, width=event.width)

    def _widget_is_descendant(self, widget, ancestor):
        current = widget
        while current is not None:
            if current == ancestor:
                return True
            current = getattr(current, "master", None)
        return False

    def _dispatch_mousewheel(self, event):
        widget = event.widget
        delta = int(-event.delta / 120) if event.delta else 0
        if delta == 0:
            return None

        if self._widget_is_descendant(widget, self.song_listbox):
            self.song_listbox.yview_scroll(delta, "units")
            return "break"

        if hasattr(self, "queue_listbox") and self._widget_is_descendant(widget, self.queue_listbox):
            self.queue_listbox.yview_scroll(delta, "units")
            return "break"

        if self._widget_is_descendant(widget, self.log_text):
            self.log_text.yview_scroll(delta, "units")
            return "break"

        if self._widget_is_descendant(widget, self.page_content):
            self.page_canvas.yview_scroll(delta, "units")
            return "break"

        return None

    def scroll_page_to_top(self):
        if hasattr(self, "page_canvas"):
            self.page_canvas.yview_moveto(0)

    def flash_selected_song_summary(self):
        if not hasattr(self, "song_name_label"):
            return

        if self.selection_flash_after_id is not None:
            self.after_cancel(self.selection_flash_after_id)

        self.song_name_label.configure(style="Selected.Value.Panel.TLabel")
        self.song_reason_label.configure(style="Selected.Status.Panel.TLabel")
        self.selection_flash_after_id = self.after(1400, self.clear_selected_song_flash)

    def clear_selected_song_flash(self):
        self.selection_flash_after_id = None
        if hasattr(self, "song_name_label"):
            self.song_name_label.configure(style="Value.Panel.TLabel")
            self.song_reason_label.configure(style="Status.Panel.TLabel")

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        shell = ttk.Frame(self, style="App.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)

        self.page_canvas = tk.Canvas(
            shell,
            bg=APP_BG,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.page_canvas.grid(row=0, column=0, sticky="nsew")

        page_scrollbar = ttk.Scrollbar(
            shell,
            orient="vertical",
            style="Panel.Vertical.TScrollbar",
            command=self.page_canvas.yview,
        )
        page_scrollbar.grid(row=0, column=1, sticky="ns")
        self.page_canvas.configure(yscrollcommand=page_scrollbar.set)

        outer = ttk.Frame(self.page_canvas, padding=18, style="App.TFrame")
        self.page_window = self.page_canvas.create_window((0, 0), window=outer, anchor="nw")
        self.page_content = outer

        outer.bind("<Configure>", self._sync_canvas_scrollregion)
        self.page_canvas.bind("<Configure>", self._sync_canvas_width)
        self.bind_all("<MouseWheel>", self._dispatch_mousewheel, add="+")

        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=4, minsize=320)
        outer.rowconfigure(5, weight=1, minsize=160)

        header = ttk.Frame(outer, style="Hero.TFrame", padding=(22, 20, 22, 20))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Autonomous Piano Player", style="HeroTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Song choice, playback controls, and debugging live together in one clean workspace.",
            style="HeroSubtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 4))
        ttk.Label(
            header,
            text="Choose a song, adjust playback, then run or troubleshoot without jumping between windows.",
            style="HeroMeta.TLabel",
        ).grid(row=2, column=0, sticky="w")

        info_frame = ttk.LabelFrame(outer, text="Information", style="Section.TLabelframe")
        info_frame.grid(row=1, column=0, sticky="ew", pady=(14, 10))
        info_body = self._create_section_body(info_frame)
        info_body.columnconfigure(1, weight=1)
        ttk.Label(info_body, text="Current selected song", style="Muted.Panel.TLabel").grid(row=0, column=0, sticky="w")
        self.song_name_label = ttk.Label(info_body, textvariable=self.song_name_var, style="Value.Panel.TLabel")
        self.song_name_label.grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(2, 4)
        )
        self.song_reason_label = ttk.Label(info_body, textvariable=self.song_reason_var, style="Status.Panel.TLabel")
        self.song_reason_label.grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        ttk.Label(info_body, textvariable=self.song_info_var, wraplength=900, style="Muted.Panel.TLabel").grid(
            row=3, column=0, columnspan=2, sticky="w"
        )

        options_frame = ttk.LabelFrame(outer, text="Controls", style="Section.TLabelframe")
        options_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        options_body = self._create_section_body(options_frame)
        options_body.columnconfigure(1, weight=1)

        ttk.Label(options_body, text="Installed solenoids", style="Panel.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.active_channels_entry = ttk.Entry(options_body, textvariable=self.active_channels_var, style="Panel.TEntry")
        self.active_channels_entry.grid(
            row=0, column=1, sticky="ew", padx=(16, 0), pady=(0, 4)
        )
        ttk.Label(
            options_body,
            text="How many hardware channels are active right now. The current bench default is 62, including the sustain pedal.",
            style="Muted.Panel.TLabel",
            wraplength=620,
        ).grid(row=1, column=1, sticky="w", padx=(16, 0), pady=(0, 12))

        ttk.Label(options_body, text="Tempo override", style="Panel.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.tempo_entry = ttk.Entry(options_body, textvariable=self.tempo_var, style="Panel.TEntry")
        self.tempo_entry.grid(
            row=2, column=1, sticky="ew", padx=(16, 0), pady=(0, 4)
        )
        ttk.Label(
            options_body,
            text="Leave blank for the original timing. You can enter 140, 0.85x, or 92bpm.",
            style="Muted.Panel.TLabel",
        ).grid(row=3, column=1, sticky="w", padx=(16, 0), pady=(0, 12))

        ttk.Label(options_body, text="Available note range", style="Panel.TLabel").grid(row=4, column=0, sticky="w", pady=(0, 4))
        self.range_entry = ttk.Entry(options_body, textvariable=self.range_var, style="Panel.TEntry")
        self.range_entry.grid(
            row=4, column=1, sticky="ew", padx=(16, 0), pady=(0, 4)
        )
        ttk.Label(
            options_body,
            text=(
                "Leave blank to use the saved note mapping. "
                "For calibration and for your current 62-actuator bench, blank is the correct default "
                "unless you intentionally want a temporary contiguous override."
            ),
            style="Muted.Panel.TLabel",
            wraplength=620,
        ).grid(row=5, column=1, sticky="w", padx=(16, 0), pady=(0, 12))

        ttk.Label(options_body, text="Out-of-range notes", style="Panel.TLabel").grid(row=6, column=0, sticky="w", pady=(0, 4))
        self.fit_mode_box = ttk.Combobox(
            options_body,
            state="readonly",
            values=("transpose", "strict"),
            textvariable=self.fit_mode_var,
            style="Panel.TCombobox",
        )
        self.fit_mode_box.grid(row=6, column=1, sticky="w", padx=(16, 0), pady=(0, 12))
        self.performance_feel_checkbutton = ttk.Checkbutton(
            options_body,
            text="Performance feel (rubato, articulation, accents, pedal breathing)",
            variable=self.performance_feel_var,
            style="Panel.TCheckbutton",
        )
        self.performance_feel_checkbutton.grid(row=7, column=1, sticky="w", padx=(16, 0), pady=(0, 4))
        self.auto_measure_pedal_checkbutton = ttk.Checkbutton(
            options_body,
            text="Add sustain every measure when MIDI has no pedal",
            variable=self.auto_measure_pedal_var,
            style="Panel.TCheckbutton",
        )
        self.auto_measure_pedal_checkbutton.grid(row=8, column=1, sticky="w", padx=(16, 0), pady=(0, 4))
        self.export_only_checkbutton = ttk.Checkbutton(
            options_body,
            text="Export only (prepare files but do not send to Arduino)",
            variable=self.export_only_var,
            style="Panel.TCheckbutton",
        )
        self.export_only_checkbutton.grid(row=9, column=1, sticky="w", padx=(16, 0))
        self.playback_locked_widgets.extend(
            [
                self.active_channels_entry,
                self.tempo_entry,
                self.range_entry,
                self.fit_mode_box,
                self.performance_feel_checkbutton,
                self.auto_measure_pedal_checkbutton,
                self.export_only_checkbutton,
            ]
        )

        run_frame = ttk.LabelFrame(outer, text="Run Options", style="Section.TLabelframe")
        run_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        run_body = self._create_section_body(run_frame)
        run_body.columnconfigure(0, weight=1)
        run_body.columnconfigure(1, weight=1)
        ttk.Label(
            run_body,
            text="Start with a dry check if you want to inspect the plan before sending anything to the Arduino.",
            style="Muted.Panel.TLabel",
            wraplength=860,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self.dry_run_button = ttk.Button(
            run_body,
            text="Run Dry Check",
            style="Secondary.TButton",
            command=lambda: self.start_run(dry_run=True),
        )
        self.dry_run_button.grid(
            row=1, column=0, sticky="ew"
        )
        self.play_button = ttk.Button(
            run_body,
            text="Play Selected / Queue",
            style="Primary.TButton",
            command=lambda: self.start_run(dry_run=False),
        )
        self.play_button.grid(
            row=1, column=1, sticky="ew", padx=(12, 0)
        )
        self.playback_locked_widgets.extend([self.dry_run_button, self.play_button])

        song_selection_frame = ttk.LabelFrame(outer, text="Song Selection", style="Section.TLabelframe")
        song_selection_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        song_body = self._create_section_body(song_selection_frame)
        song_body.columnconfigure(0, weight=1)
        song_body.rowconfigure(3, weight=1, minsize=180)

        ttk.Label(
            song_body,
            text="Search the project library below, refresh the list, or browse to an outside MIDI file.",
            style="Muted.Panel.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Label(song_body, textvariable=self.song_catalog_status_var, style="Status.Panel.TLabel").grid(
            row=1, column=0, sticky="w", pady=(0, 10)
        )

        search_row = ttk.Frame(song_body, style="Panel.TFrame")
        search_row.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        search_row.columnconfigure(0, weight=1)
        search_entry = ttk.Entry(search_row, textvariable=self.song_search_var, style="Panel.TEntry")
        search_entry.grid(row=0, column=0, sticky="ew")
        search_entry.bind("<KeyRelease>", self.refresh_song_list)
        ttk.Button(
            search_row,
            text="Refresh List",
            style="Secondary.TButton",
            command=self.refresh_song_catalog_from_button,
        ).grid(
            row=0, column=1, padx=(8, 0)
        )
        ttk.Button(search_row, text="Browse for MIDI...", style="Secondary.TButton", command=self.browse_for_song).grid(
            row=0, column=2, padx=(8, 0)
        )
        ttk.Button(search_row, text="Use Selected Song", style="Primary.TButton", command=self.use_selected_song_from_list).grid(
            row=0, column=3, padx=(8, 0)
        )

        song_list_frame = ttk.Frame(song_body, style="Panel.TFrame")
        song_list_frame.grid(row=3, column=0, sticky="nsew")
        song_list_frame.columnconfigure(0, weight=1)
        song_list_frame.rowconfigure(0, weight=1)

        self.song_listbox = tk.Listbox(
            song_list_frame,
            height=12,
            bg=INPUT_BG,
            fg=TEXT_COLOR,
            selectbackground=ACCENT_SOFT,
            selectforeground=TEXT_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_COLOR,
            highlightthickness=1,
            relief="flat",
            bd=0,
            activestyle="none",
            font=("Segoe UI", 10),
        )
        self.song_listbox.grid(row=0, column=0, sticky="nsew")
        self.song_listbox.bind("<Double-Button-1>", self.use_selected_song_from_list)

        song_scrollbar = ttk.Scrollbar(
            song_list_frame,
            orient="vertical",
            style="Panel.Vertical.TScrollbar",
            command=self.song_listbox.yview,
        )
        song_scrollbar.grid(row=0, column=1, sticky="ns")
        self.song_listbox.configure(yscrollcommand=song_scrollbar.set)

        queue_frame = ttk.LabelFrame(song_body, text="Queue", style="Section.TLabelframe")
        queue_frame.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        queue_body = self._create_section_body(queue_frame, padding=(14, 14, 14, 14))
        queue_body.columnconfigure(0, weight=1)

        ttk.Label(queue_body, textvariable=self.queue_status_var, style="Status.Panel.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )

        queue_button_row = ttk.Frame(queue_body, style="Panel.TFrame")
        queue_button_row.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        queue_button_row.columnconfigure(6, weight=1)
        ttk.Button(
            queue_button_row,
            text="Add Selected to Queue",
            style="Secondary.TButton",
            command=self.add_selected_song_to_queue,
        ).grid(row=0, column=0, sticky="w")
        self.play_queue_button = ttk.Button(
            queue_button_row,
            text="Play Queue",
            style="Primary.TButton",
            command=self.start_queue_playback,
        )
        self.play_queue_button.grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Button(
            queue_button_row,
            text="Remove",
            style="Secondary.TButton",
            command=self.remove_selected_queue_item,
        ).grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.move_queue_item_up_button = ttk.Button(
            queue_button_row,
            text="Move Up",
            style="Secondary.TButton",
            command=lambda: self.move_selected_queue_item(-1),
        )
        self.move_queue_item_up_button.grid(row=0, column=3, sticky="w", padx=(8, 0))
        self.move_queue_item_down_button = ttk.Button(
            queue_button_row,
            text="Move Down",
            style="Secondary.TButton",
            command=lambda: self.move_selected_queue_item(1),
        )
        self.move_queue_item_down_button.grid(row=0, column=4, sticky="w", padx=(8, 0))
        self.move_queue_item_up_button.configure(state="disabled")
        self.move_queue_item_down_button.configure(state="disabled")
        ttk.Button(
            queue_button_row,
            text="Clear Queue",
            style="Secondary.TButton",
            command=self.clear_playback_queue,
        ).grid(row=0, column=5, sticky="w", padx=(8, 0))
        self.playback_locked_widgets.append(self.play_queue_button)

        queue_list_frame = ttk.Frame(queue_body, style="Panel.TFrame")
        queue_list_frame.grid(row=2, column=0, sticky="ew")
        queue_list_frame.columnconfigure(0, weight=1)
        self.queue_listbox = tk.Listbox(
            queue_list_frame,
            height=4,
            bg=INPUT_BG,
            fg=TEXT_COLOR,
            selectbackground=ACCENT_SOFT,
            selectforeground=TEXT_COLOR,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_COLOR,
            highlightthickness=1,
            relief="flat",
            bd=0,
            activestyle="none",
            font=("Segoe UI", 10),
        )
        self.queue_listbox.grid(row=0, column=0, sticky="ew")
        self.queue_listbox.bind("<<ListboxSelect>>", self.refresh_queue_reorder_buttons)
        self.queue_listbox.bind("<Alt-Up>", lambda event: self.move_selected_queue_item(-1))
        self.queue_listbox.bind("<Alt-Down>", lambda event: self.move_selected_queue_item(1))
        queue_scrollbar = ttk.Scrollbar(
            queue_list_frame,
            orient="vertical",
            style="Panel.Vertical.TScrollbar",
            command=self.queue_listbox.yview,
        )
        queue_scrollbar.grid(row=0, column=1, sticky="ns")
        self.queue_listbox.configure(yscrollcommand=queue_scrollbar.set)

        playback_control_row = ttk.Frame(queue_body, style="Panel.TFrame")
        playback_control_row.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        playback_control_row.columnconfigure(3, weight=1)
        self.pause_resume_button = ttk.Button(
            playback_control_row,
            text="Pause",
            style="Secondary.TButton",
            command=self.toggle_queue_pause,
        )
        self.pause_resume_button.grid(row=0, column=0, sticky="w")
        self.replay_current_button = ttk.Button(
            playback_control_row,
            text="Replay Current",
            style="Secondary.TButton",
            command=self.replay_current_queue_item,
        )
        self.replay_current_button.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.skip_current_button = ttk.Button(
            playback_control_row,
            text="Skip to Next",
            style="Secondary.TButton",
            command=self.skip_current_queue_item,
        )
        self.skip_current_button.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.refresh_playback_control_buttons()

        debug_frame = ttk.LabelFrame(outer, text="Debugging", style="Section.TLabelframe")
        debug_frame.grid(row=5, column=0, sticky="nsew", pady=(0, 0))
        debug_body = self._create_section_body(debug_frame)
        debug_body.columnconfigure(0, weight=1)
        debug_body.rowconfigure(3, weight=1, minsize=140)

        ttk.Label(
            debug_body,
            text="Use these tools when you are calibrating, validating, or diagnosing the bench.",
            style="Muted.Panel.TLabel",
            wraplength=860,
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        debug_button_row = ttk.Frame(debug_body, style="Panel.TFrame")
        debug_button_row.grid(row=1, column=0, sticky="w", pady=(0, 10))
        self.calibrate_button = ttk.Button(
            debug_button_row,
            text="Calibrate Note Mapping...",
            style="Secondary.TButton",
            command=self.start_note_mapping_calibration,
        )
        self.calibrate_button.grid(
            row=0, column=0, sticky="w"
        )
        self.troubleshoot_button = ttk.Button(
            debug_button_row,
            text="Troubleshoot Keys...",
            style="Secondary.TButton",
            command=self.start_troubleshooting_run,
        )
        self.troubleshoot_button.grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        self.mosfet_test_button = ttk.Button(
            debug_button_row,
            text="Test Channel...",
            style="Secondary.TButton",
            command=self.start_mosfet_test,
        )
        self.mosfet_test_button.grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )
        self.speed_test_button = ttk.Button(
            debug_button_row,
            text="Speed Test...",
            style="Secondary.TButton",
            command=self.start_speed_test_dialog,
        )
        self.speed_test_button.grid(
            row=0, column=3, sticky="w", padx=(8, 0)
        )
        self.defect_debug_button = ttk.Button(
            debug_button_row,
            text="Defective Note Debug...",
            style="Secondary.TButton",
            command=self.start_defective_note_debug_dialog,
        )
        self.defect_debug_button.grid(
            row=0, column=4, sticky="w", padx=(8, 0)
        )
        self.playback_locked_widgets.extend(
            [
                self.calibrate_button,
                self.troubleshoot_button,
                self.mosfet_test_button,
                self.speed_test_button,
                self.defect_debug_button,
            ]
        )

        sweep_stop_row = ttk.Frame(debug_body, style="Panel.TFrame")
        sweep_stop_row.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        sweep_stop_row.columnconfigure(0, weight=1)
        sweep_stop_row.columnconfigure(1, weight=1)
        self.mark_current_note_button = ttk.Button(
            sweep_stop_row,
            text="Mark Current Note",
            style="Secondary.TButton",
            command=self.mark_current_full_sweep_note,
            state="disabled",
        )
        self.mark_current_note_button.grid(
            row=0, column=0, sticky="ew"
        )
        self.stop_troubleshooting_button = ttk.Button(
            sweep_stop_row,
            text="End Full Sweep and Show Marked Notes",
            style="Primary.TButton",
            command=self.stop_active_full_sweep,
            state="disabled",
        )
        self.stop_troubleshooting_button.grid(
            row=0, column=1, sticky="ew", padx=(8, 0)
        )

        log_frame = ttk.LabelFrame(debug_body, text="Status", style="Section.TLabelframe")
        log_frame.grid(row=3, column=0, sticky="nsew")
        log_body = self._create_section_body(log_frame, padding=(14, 14, 14, 14))
        log_body.columnconfigure(0, weight=1)
        log_body.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_body,
            height=7,
            wrap="word",
            bg=LOG_BG,
            fg=LOG_TEXT,
            insertbackground=LOG_TEXT,
            selectbackground="#31485e",
            selectforeground=LOG_TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Consolas", 10),
            padx=10,
            pady=10,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.configure(state="disabled")

        scrollbar = ttk.Scrollbar(log_body, orient="vertical", style="Panel.Vertical.TScrollbar", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(10, 0))
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def set_controls_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for child in self.winfo_children():
            self._set_child_state_recursive(child, state)

    def set_playback_controls_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for widget in self.playback_locked_widgets:
            self._set_widget_state(widget, state)

    def _set_widget_state(self, widget, state):
        try:
            if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton)):
                widget.configure(state=state if not isinstance(widget, ttk.Combobox) else ("readonly" if state == "normal" else "disabled"))
            elif isinstance(widget, tk.Listbox):
                widget.configure(state=state)
        except tk.TclError:
            pass

    def _set_child_state_recursive(self, widget, state):
        self._set_widget_state(widget, state)
        for child in widget.winfo_children():
            self._set_child_state_recursive(child, state)

    def append_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def show_completion_dialog(self, title, summary):
        if self.completion_dialog is not None and self.completion_dialog.winfo_exists():
            self.completion_dialog.destroy()

        dialog = tk.Toplevel(self)
        self.completion_dialog = dialog
        dialog.title(title)
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.configure(bg=APP_BG)

        def dismiss():
            if self.completion_dialog == dialog:
                self.completion_dialog = None
            dialog.destroy()

        def refresh_and_dismiss():
            dismiss()
            self.refresh_song_catalog_from_button()

        dialog.protocol("WM_DELETE_WINDOW", dismiss)

        outer = ttk.Frame(dialog, padding=18, style="App.TFrame")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)

        ttk.Label(outer, text=title, style="DialogTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            outer,
            text=summary,
            style="App.TLabel",
            justify="left",
            wraplength=520,
        ).grid(row=1, column=0, sticky="ew", pady=(8, 16))

        button_row = ttk.Frame(outer, style="App.TFrame")
        button_row.grid(row=2, column=0, sticky="e")
        ttk.Button(button_row, text="Refresh List", style="Secondary.TButton", command=refresh_and_dismiss).grid(
            row=0, column=0
        )
        ttk.Button(button_row, text="Dismiss", style="Primary.TButton", command=dismiss).grid(
            row=0, column=1, padx=(8, 0)
        )

        dialog.bind("<Escape>", lambda _event: dismiss())
        dialog.bind("<Return>", lambda _event: dismiss())
        dialog.update_idletasks()
        x = self.winfo_rootx() + max(40, (self.winfo_width() - dialog.winfo_width()) // 2)
        y = self.winfo_rooty() + max(40, (self.winfo_height() - dialog.winfo_height()) // 3)
        dialog.geometry(f"+{x}+{y}")
        dialog.lift(self)
        dialog.focus_set()

    def update_song_catalog_status(self):
        entries = self.song_catalog.get("entries", []) if self.song_catalog else []
        download_count = sum(1 for entry in entries if entry.get("source") == "Downloads")
        library_count = sum(1 for entry in entries if entry.get("source") == "Library")

        if not entries:
            status = "No MIDI files found yet."
        else:
            source_parts = []
            if library_count:
                source_parts.append(f"{library_count} in Library")
            if download_count:
                source_parts.append(f"{download_count} in Downloads")
            status = f"{len(entries)} song(s) available"
            if source_parts:
                status += f" ({', '.join(source_parts)})"

        if self.song_catalog_refresh_in_progress:
            status += " Scanning Downloads in the background..."
            if self.pending_song_catalog_refresh is not None:
                status += " Refresh queued."

        self.song_catalog_status_var.set(status)

    def apply_song_catalog(self, catalog, use_suggested=False, force_suggested=False, reveal_selection=False):
        self.song_catalog = catalog
        previous_selected_path = self.selected_song_path.resolve() if self.selected_song_path is not None else None
        selected_suggested_song = False

        if use_suggested and (force_suggested or not self.song_selection_is_manual):
            suggested_path = self.song_catalog.get("suggested_path")
            suggested_reason = self.song_catalog.get("suggested_reason")
            if suggested_path is not None:
                self.set_selected_song(suggested_path, suggested_reason, manual=False)
                selected_suggested_song = True

        if self.selected_song_path is None:
            self.song_name_var.set("No MIDI files found")
            latest_zip = self.song_catalog.get("latest_zip")
            if latest_zip is not None:
                self.song_reason_var.set(f"Newest download looks like a ZIP archive: {latest_zip.name}")
            else:
                self.song_reason_var.set("Use the Song Selection section below to choose or browse for a MIDI file.")
            self.song_info_var.set("No project-library or Downloads MIDI files were found yet.")

        self.update_song_catalog_status()
        if hasattr(self, "song_listbox"):
            self.refresh_song_list()
        if reveal_selection:
            self.scroll_page_to_top()
            current_selected_path = self.selected_song_path.resolve() if self.selected_song_path is not None else None
            if selected_suggested_song and current_selected_path is not None:
                self.flash_selected_song_summary()
                if current_selected_path != previous_selected_path:
                    self.append_log(f"Refresh List selected newest detected song: {self.selected_song_path.name}")
                else:
                    self.append_log(f"Refresh List kept newest detected song selected: {self.selected_song_path.name}")
            elif current_selected_path is None:
                self.flash_selected_song_summary()
                self.append_log("Refresh List found no MIDI files to select.")
            else:
                self.append_log("Refresh List found no new suggested MIDI to select.")
        return self.song_catalog.get("entries", [])

    def refresh_song_catalog(self, use_suggested=False, recursive_downloads=True, force_suggested=False, reveal_selection=False):
        catalog = engine.build_song_catalog(
            self.user_preferences,
            recursive_downloads=recursive_downloads,
        )
        return self.apply_song_catalog(
            catalog,
            use_suggested=use_suggested,
            force_suggested=force_suggested,
            reveal_selection=reveal_selection,
        )

    def refresh_song_catalog_from_button(self):
        self.scroll_page_to_top()
        self.refresh_song_catalog_async(use_suggested=True, force_suggested=True, reveal_selection=True)

    def refresh_song_catalog_async(self, use_suggested=False, force_suggested=False, reveal_selection=False):
        if self.song_catalog_refresh_in_progress:
            if reveal_selection:
                self.scroll_page_to_top()
            self.pending_song_catalog_refresh = {
                "use_suggested": use_suggested,
                "force_suggested": force_suggested,
                "reveal_selection": reveal_selection,
            }
            self.update_song_catalog_status()
            return

        self.song_catalog_refresh_in_progress = True
        self.update_song_catalog_status()
        worker = threading.Thread(
            target=self._refresh_song_catalog_worker,
            args=(use_suggested, force_suggested, reveal_selection),
            daemon=True,
        )
        worker.start()

    def _refresh_song_catalog_worker(self, use_suggested, force_suggested, reveal_selection):
        try:
            catalog = engine.build_song_catalog(
                self.user_preferences,
                recursive_downloads=True,
            )
        except Exception as error:
            self.message_queue.put(("song_catalog_error", str(error)))
            return

        self.message_queue.put(
            (
                "song_catalog",
                {
                    "catalog": catalog,
                    "use_suggested": use_suggested,
                    "force_suggested": force_suggested,
                    "reveal_selection": reveal_selection,
                },
            )
        )

    def refresh_song_list(self, _event=None):
        entries = self.song_catalog.get("entries", []) if self.song_catalog else []
        query = self.song_search_var.get().strip().lower()
        self.filtered_song_entries = [
            entry
            for entry in entries
            if not query or query in entry["description"].lower() or query in entry["display_name"].lower()
        ]

        self.song_listbox.delete(0, tk.END)
        selected_index = None
        selected_path = self.selected_song_path.resolve() if self.selected_song_path is not None else None
        for index, entry in enumerate(self.filtered_song_entries):
            self.song_listbox.insert(tk.END, entry["description"])
            if selected_path is not None and Path(entry["path"]).resolve() == selected_path:
                selected_index = index

        if selected_index is None and self.filtered_song_entries:
            selected_index = 0

        if selected_index is not None:
            self.song_listbox.selection_set(selected_index)
            self.song_listbox.see(selected_index)

    def browse_for_song(self):
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Choose a MIDI File",
            filetypes=[("MIDI files", "*.mid *.midi"), ("All files", "*.*")],
        )
        if not chosen:
            return

        chosen_path = Path(chosen)
        self.set_selected_song(chosen_path, "manually chosen from an external file", manual=True)

    def use_selected_song_from_list(self, _event=None):
        selection = self.song_listbox.curselection()
        if not selection:
            messagebox.showinfo("Choose a song", "Select a song from the list or browse for a MIDI file.", parent=self)
            return

        entry = self.filtered_song_entries[selection[0]]
        self.set_selected_song(entry["path"], f"manually chosen from {entry['source']}", manual=True)

    def set_selected_song(self, midi_path, reason, manual=False):
        self.selected_song_path = Path(midi_path)
        self.selection_reason = reason
        self.song_selection_is_manual = manual
        self.song_name_var.set(self.selected_song_path.name)
        self.song_reason_var.set(reason)
        self.update_song_preview()

    def build_queue_item(self, midi_path, reason, source="Selection"):
        path = Path(midi_path)
        return {
            "path": path,
            "reason": reason,
            "source": source,
            "display_name": path.name,
        }

    def get_queue_item_from_song_list_selection(self):
        if not hasattr(self, "song_listbox"):
            return None

        selection = self.song_listbox.curselection()
        if not selection:
            return None

        index = selection[0]
        if index >= len(self.filtered_song_entries):
            return None

        entry = self.filtered_song_entries[index]
        return self.build_queue_item(
            entry["path"],
            f"queued from {entry['source']}",
            source=entry["source"],
        )

    def get_current_queue_selection(self):
        list_item = self.get_queue_item_from_song_list_selection()
        if list_item is not None:
            return list_item

        if self.selected_song_path is None:
            return None

        return self.build_queue_item(
            self.selected_song_path,
            self.selection_reason or "queued from the current selection",
            source="Current selection",
        )

    def add_selected_song_to_queue(self):
        item = self.get_current_queue_selection()
        if item is None:
            messagebox.showinfo("Choose a song", "Select a song from the list or browse for a MIDI file.", parent=self)
            return

        with self.queue_lock:
            self.playback_queue.append(item)

        self.refresh_queue_list()
        self.append_log(f"Queued: {item['display_name']}")

    def remove_selected_queue_item(self):
        if not hasattr(self, "queue_listbox"):
            return

        selection = self.queue_listbox.curselection()
        if not selection:
            messagebox.showinfo("Choose a queued song", "Select an upcoming queue item to remove.", parent=self)
            return

        selected_index = selection[0]
        selected_now_playing = False
        removed = None
        with self.queue_lock:
            current_offset = 1 if self.current_queue_item is not None else 0
            if selected_index == 0 and current_offset:
                selected_now_playing = True
            else:
                queue_index = selected_index - current_offset
                if 0 <= queue_index < len(self.playback_queue):
                    removed = self.playback_queue.pop(queue_index)

        if selected_now_playing:
            messagebox.showinfo("Now playing", "The currently playing song cannot be removed.", parent=self)
            return
        if removed is None:
            return

        self.refresh_queue_list()
        self.append_log(f"Removed from queue: {removed['display_name']}")

    def move_selected_queue_item(self, direction):
        if not hasattr(self, "queue_listbox"):
            return "break"

        selection = self.queue_listbox.curselection()
        if not selection:
            messagebox.showinfo("Choose a queued song", "Select an upcoming queue item to move.", parent=self)
            return "break"

        selected_index = selection[0]
        selected_now_playing = False
        moved = None
        new_list_index = None
        with self.queue_lock:
            current_offset = 1 if self.current_queue_item is not None else 0
            if selected_index == 0 and current_offset:
                selected_now_playing = True
            else:
                queue_index = selected_index - current_offset
                target_index = queue_index + direction
                if 0 <= queue_index < len(self.playback_queue) and 0 <= target_index < len(self.playback_queue):
                    moved = self.playback_queue.pop(queue_index)
                    self.playback_queue.insert(target_index, moved)
                    new_list_index = target_index + current_offset

        if selected_now_playing:
            messagebox.showinfo("Now playing", "The currently playing song cannot be moved.", parent=self)
            return "break"
        if moved is None:
            self.refresh_queue_reorder_buttons()
            return "break"

        self.refresh_queue_list(select_index=new_list_index)
        direction_label = "up" if direction < 0 else "down"
        self.append_log(f"Moved queued song {direction_label}: {moved['display_name']}")
        return "break"

    def clear_playback_queue(self):
        with self.queue_lock:
            removed_count = len(self.playback_queue)
            self.playback_queue.clear()

        self.refresh_queue_list()
        if removed_count:
            self.append_log(f"Cleared {removed_count} queued song(s).")

    def refresh_queue_list(self, select_index=None):
        if not hasattr(self, "queue_listbox"):
            return

        with self.queue_lock:
            current_item = self.current_queue_item
            queued_items = list(self.playback_queue)
            queue_is_playing = self.queue_is_playing

        self.queue_listbox.delete(0, tk.END)
        if current_item is not None:
            self.queue_listbox.insert(tk.END, f"Now playing | {current_item['display_name']}")

        for index, item in enumerate(queued_items, start=1):
            self.queue_listbox.insert(tk.END, f"{index}. {item['display_name']} ({item['source']})")

        row_count = self.queue_listbox.size()
        if select_index is not None and 0 <= select_index < row_count:
            self.queue_listbox.selection_set(select_index)
            self.queue_listbox.see(select_index)
        elif current_item is not None:
            self.queue_listbox.selection_set(0)
            self.queue_listbox.see(0)

        if queue_is_playing:
            if current_item is not None and queued_items:
                status = f"Playing {current_item['display_name']} | {len(queued_items)} queued"
            elif current_item is not None:
                status = f"Playing {current_item['display_name']} | add songs now to continue"
            elif queued_items:
                status = f"Waiting 3 seconds | {len(queued_items)} queued"
            else:
                status = "Waiting for the current queue run to finish..."
        elif queued_items:
            status = f"{len(queued_items)} song(s) queued."
        else:
            status = "Queue empty."

        self.queue_status_var.set(status)
        self.refresh_queue_reorder_buttons()
        self.refresh_playback_control_buttons()

    def refresh_queue_reorder_buttons(self, _event=None):
        if not hasattr(self, "move_queue_item_up_button"):
            return

        selection = self.queue_listbox.curselection()
        can_move_up = False
        can_move_down = False
        if selection:
            selected_index = selection[0]
            with self.queue_lock:
                current_offset = 1 if self.current_queue_item is not None else 0
                queue_index = selected_index - current_offset
                queued_count = len(self.playback_queue)

            if 0 <= queue_index < queued_count:
                can_move_up = queue_index > 0
                can_move_down = queue_index < queued_count - 1

        self.move_queue_item_up_button.configure(state="normal" if can_move_up else "disabled")
        self.move_queue_item_down_button.configure(state="normal" if can_move_down else "disabled")

    def refresh_playback_control_buttons(self):
        if not hasattr(self, "pause_resume_button"):
            return

        with self.queue_lock:
            queue_is_playing = self.queue_is_playing
            has_current_item = self.current_queue_item is not None

        control = self.playback_control
        is_paused = bool(control and control.is_paused())
        pause_requested = bool(control and control.is_pause_requested())
        can_control = queue_is_playing and control is not None
        pause_text = "Resume" if is_paused or pause_requested else "Pause"

        self.pause_resume_button.configure(
            text=pause_text,
            state="normal" if can_control and has_current_item else "disabled",
        )
        self.replay_current_button.configure(
            state="normal" if can_control and has_current_item else "disabled"
        )
        self.skip_current_button.configure(
            state="normal" if can_control and has_current_item else "disabled"
        )
        self.refresh_note_marker_controls()

    def refresh_note_marker_controls(self):
        if not hasattr(self, "stop_troubleshooting_button"):
            return

        control = self.note_marker_control
        can_stop = bool(control)
        can_mark = bool(control and control.note_marker_active())
        self.mark_current_note_button.configure(state="normal" if can_mark else "disabled")
        self.stop_troubleshooting_button.configure(state="normal" if can_stop else "disabled")

    def toggle_queue_pause(self):
        control = self.playback_control
        if control is None:
            return

        if control.is_paused() or control.is_pause_requested():
            control.request_resume()
            self.append_log("Resume requested.")
        else:
            control.request_pause()
            self.append_log("Pause requested.")
        self.refresh_playback_control_buttons()

    def replay_current_queue_item(self):
        control = self.playback_control
        if control is None:
            return

        with self.queue_lock:
            current_item = self.current_queue_item
        if current_item is None:
            return

        control.request_replay()
        self.append_log(f"Replay requested for {current_item['display_name']}.")
        self.refresh_playback_control_buttons()

    def skip_current_queue_item(self):
        control = self.playback_control
        if control is None:
            return

        with self.queue_lock:
            current_item = self.current_queue_item
        if current_item is None:
            return

        control.request_skip()
        self.append_log(f"Skip requested for {current_item['display_name']}.")
        self.refresh_playback_control_buttons()

    def handle_note_marker_return(self, _event=None):
        return self.mark_current_full_sweep_note()

    def show_sweep_marker_dialog(self):
        self.close_sweep_marker_dialog()

        dialog = tk.Toplevel(self)
        dialog.title("Full Sweep Marker")
        dialog.resizable(False, False)
        dialog.configure(bg=APP_BG)
        dialog.transient(self)
        dialog.attributes("-topmost", True)
        dialog.protocol("WM_DELETE_WINDOW", self.stop_active_full_sweep)

        outer = ttk.Frame(dialog, padding=18, style="App.TFrame")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)

        ttk.Label(
            outer,
            text="Full sweep marker",
            style="DialogTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            outer,
            text="Press Enter, Space, or Mark Current Note when the note you want to remember has just played.",
            style="Muted.TLabel",
            wraplength=420,
        ).grid(row=1, column=0, sticky="w", pady=(6, 12))

        button_row = ttk.Frame(outer, style="App.TFrame")
        button_row.grid(row=2, column=0, sticky="ew")
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)
        ttk.Button(
            button_row,
            text="Mark Current Note",
            style="Primary.TButton",
            command=self.mark_current_full_sweep_note,
        ).grid(row=0, column=0, sticky="ew")
        ttk.Button(
            button_row,
            text="End Sweep",
            style="Secondary.TButton",
            command=self.stop_active_full_sweep,
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(
            outer,
            textvariable=self.sweep_marker_text_var,
            style="Muted.TLabel",
            wraplength=420,
        ).grid(row=3, column=0, sticky="w", pady=(12, 0))

        dialog.bind("<Return>", self.handle_note_marker_return)
        dialog.bind("<KP_Enter>", self.handle_note_marker_return)
        dialog.bind("<space>", self.handle_note_marker_return)
        self.sweep_marker_dialog = dialog
        self.refresh_sweep_marker_dialog()
        dialog.lift()
        dialog.focus_force()

    def refresh_sweep_marker_dialog(self):
        if self.sweep_marker_dialog is None:
            return
        control = self.note_marker_control
        if control is None:
            self.sweep_marker_text_var.set("No full sweep is active.")
            return

        marked_lines = control.get_marked_note_lines()
        if not marked_lines:
            self.sweep_marker_text_var.set("Marked notes: none yet")
            return

        visible_lines = marked_lines[-6:]
        prefix = f"Marked notes ({len(marked_lines)}):"
        self.sweep_marker_text_var.set(prefix + "\n" + "\n".join(visible_lines))

    def close_sweep_marker_dialog(self):
        dialog = self.sweep_marker_dialog
        self.sweep_marker_dialog = None
        if dialog is not None:
            try:
                dialog.destroy()
            except tk.TclError:
                pass

    def mark_current_full_sweep_note(self):
        control = self.note_marker_control
        if control is None:
            self.refresh_sweep_marker_dialog()
            return None

        step, status = control.mark_previous_note_step()
        if step is None:
            self.append_log(f"Full sweep marker: {status}")
            self.refresh_sweep_marker_dialog()
            return "break"

        notes = " + ".join(step.get("note_labels", []))
        if status == "already_marked":
            self.append_log(f"Full sweep marker already saved: {notes}")
        else:
            self.append_log(
                f"Full sweep marker saved: {notes} "
                f"(velocity {step.get('velocity')}, {step.get('phase_name')})"
            )
        self.refresh_sweep_marker_dialog()
        return "break"

    def stop_active_full_sweep(self):
        control = self.note_marker_control
        if control is None:
            return

        control.request_skip()
        marked_lines = control.get_marked_note_lines()
        self.append_log("End requested for full sweep.")
        if marked_lines:
            self.append_log("Marked notes so far:")
            for line in marked_lines:
                self.append_log(f"  {line}")
        else:
            self.append_log("Marked notes so far: none")
        self.refresh_note_marker_controls()
        self.refresh_sweep_marker_dialog()

    def update_song_preview(self):
        if self.selected_song_path is None:
            self.song_info_var.set("No MIDI selected yet.")
            return

        try:
            preview = engine.inspect_midi_file(self.selected_song_path)
        except Exception as error:
            self.song_info_var.set(f"Unable to preview this MIDI file: {error}")
            return

        self.song_info_var.set(
            f"{preview['track_count']} track(s) | "
            f"{preview['tempo_bpm']:.2f} BPM | "
            f"Range: {preview['range_label']} | "
            f"Playable note events detected: {preview['note_count']}"
        )

    def get_active_channel_count(self):
        active_channel_count = self.active_channels_var.get().strip()
        return engine.parse_active_channel_count(
            active_channel_count,
            self.config_data["pca9685"],
        )

    def build_active_calibration_config(self, active_channel_count):
        config = engine.load_config()
        return piano_tools.build_calibration_config(config, active_channel_count)

    def build_sweep_mapping_config(self, active_channel_count):
        config = engine.load_config()
        mapping, active_sequence = engine.apply_active_channel_limit(
            config["mapping"],
            config["pca9685"],
            active_channel_count=active_channel_count,
        )
        config["mapping"] = mapping
        return config, active_sequence

    def build_patch_mapping_config(self, active_channel_count):
        config = engine.load_config()
        return piano_tools.build_patch_mapping_config(config, active_channel_count)

    def build_speed_test_note_rows(self):
        active_channel_count = self.get_active_channel_count()
        config, _active_sequence = self.build_sweep_mapping_config(active_channel_count)
        rows = []
        channel_labels = config["mapping"].get("channel_labels", {})
        for note, channel in piano_tools.iter_mapping_in_note_order(config["mapping"]):
            actuation = engine.resolve_note_actuation(note, channel, config)
            rows.append(
                {
                    "note": int(note),
                    "note_label": engine.midi_note_name(int(note)),
                    "channel": int(channel),
                    "channel_label": channel_labels.get(str(channel), f"Channel {channel}"),
                    "channel_target": engine.describe_global_channel(channel, config["pca9685"]),
                    "saved_playback_velocity_override": actuation.get("playback_velocity_override"),
                    "saved_minimum_repeat_period_ms": actuation.get("minimum_repeat_period_ms"),
                }
            )
        if not rows:
            raise RuntimeError("No mapped piano notes are available for speed testing.")
        return rows

    def start_speed_test_dialog(self):
        if self.speed_test_dialog is not None and self.speed_test_dialog.winfo_exists():
            self.speed_test_dialog.lift(self)
            self.speed_test_dialog.focus_set()
            return

        try:
            note_rows = self.build_speed_test_note_rows()
        except ValueError as error:
            messagebox.showerror("Invalid hardware count", str(error), parent=self)
            return
        except RuntimeError as error:
            messagebox.showerror("Speed test unavailable", str(error), parent=self)
            return

        defaults = {
            "speed_label": SPEED_TEST_SPEED_LABELS[0],
            "bpm": 120,
            "repeats": 10,
            "velocity": engine.DIAGNOSTIC_MEDIUM_VELOCITY,
        }
        self.speed_test_dialog = SolenoidSpeedTestDialog(self, note_rows, defaults)

    def build_defective_note_debug_rows(self):
        entries = self.load_speed_test_log_entries()
        latest_by_note = {}
        for entry in entries:
            try:
                note = int(entry["note"])
            except (KeyError, TypeError, ValueError):
                continue
            latest_by_note[note] = entry

        slow_entries = [
            entry
            for _note, entry in sorted(latest_by_note.items())
            if entry.get("status") == "slower_blends"
        ]
        if not slow_entries:
            raise RuntimeError("No notes currently have a latest speed-test result of slower / blends.")

        config = engine.load_config()
        channel_labels = config["mapping"].get("channel_labels", {})
        rows = []
        for entry in slow_entries:
            note = int(entry["note"])
            channel = entry.get("channel")
            if channel in (None, ""):
                channel = engine.map_note_to_channel(note, config["mapping"])
            if channel is None:
                continue
            channel = int(channel)
            actuation = engine.resolve_note_actuation(note, channel, config)
            rows.append(
                {
                    "note": note,
                    "note_label": engine.midi_note_name(note),
                    "channel": channel,
                    "channel_label": channel_labels.get(str(channel), f"Channel {channel}"),
                    "channel_target": engine.describe_global_channel(channel, config["pca9685"]),
                    "source_speed_label": entry.get("speed_label", "32nds"),
                    "source_bpm": float(entry.get("bpm", 80.0)),
                    "source_repeats": int(entry.get("repeats", 10)),
                    "source_velocity": int(entry.get("velocity", engine.DIAGNOSTIC_MEDIUM_VELOCITY)),
                    "saved_playback_velocity_override": actuation.get("playback_velocity_override"),
                    "strike_min_pwm": int(actuation["strike_min_pwm"]),
                    "strike_max_pwm": int(actuation["strike_max_pwm"]),
                    "strike_ms": int(actuation["strike_ms"]),
                    "hold_min_pwm": int(actuation["hold_min_pwm"]),
                    "hold_max_pwm": int(actuation["hold_max_pwm"]),
                    "hold_ratio": float(actuation["hold_ratio"]),
                    "release_delay_ms": int(actuation["release_delay_ms"]),
                    "minimum_rearm_gap_ms": int(actuation["minimum_rearm_gap_ms"]),
                    "retrigger_gap_ms": int(actuation["retrigger_gap_ms"]),
                    "minimum_repeat_period_ms": int(actuation.get("minimum_repeat_period_ms", 0)),
                }
            )
        if not rows:
            raise RuntimeError("The slower / blending speed-test notes no longer match the current note map.")
        return rows

    def start_defective_note_debug_dialog(self):
        if self.defect_debug_dialog is not None and self.defect_debug_dialog.winfo_exists():
            self.defect_debug_dialog.lift(self)
            self.defect_debug_dialog.focus_set()
            return

        try:
            note_rows = self.build_defective_note_debug_rows()
        except RuntimeError as error:
            messagebox.showerror("Defective note debug unavailable", str(error), parent=self)
            return

        self.defect_debug_dialog = DefectiveNoteDebugDialog(self, note_rows)

    def start_speed_test_burst(self, request):
        if self.worker is not None and self.worker.is_alive():
            messagebox.showinfo("Already running", "Wait for the current playback job to finish first.", parent=self)
            return

        self.append_log("")
        self.append_log(
            f"Starting speed test burst: {request['note_label']} on channel {request['channel']} "
            f"at {request['speed_label']} / {request['bpm']:.2f} BPM "
            f"({request['period_ms']:.1f} ms between strikes)."
        )
        if self.speed_test_dialog is not None and self.speed_test_dialog.winfo_exists():
            self.speed_test_dialog.set_running(True)
        self.set_playback_controls_enabled(False)

        worker_args = {
            "workflow_kind": "speed_test",
            "test_request": dict(request),
            "reporter": lambda message: self.message_queue.put(("log", message)),
        }
        self.worker = threading.Thread(target=self._run_workflow, args=(worker_args,), daemon=True)
        self.worker.start()

    def start_defective_note_single_pulse(self, row, velocity):
        if self.worker is not None and self.worker.is_alive():
            messagebox.showinfo("Already running", "Wait for the current playback job to finish first.", parent=self)
            return

        pulse = {
            "channel": int(row["channel"]),
            "velocity": int(velocity),
        }
        self.append_log("")
        self.append_log(
            f"Starting defective-note pulse: {row['note_label']} on channel {row['channel']} "
            f"at velocity {velocity}..."
        )
        self.set_controls_enabled(False)

        worker_args = {
            "workflow_kind": "mosfet_test",
            "pulse": pulse,
            "reporter": lambda message: self.message_queue.put(("log", message)),
        }
        self.worker = threading.Thread(target=self._run_workflow, args=(worker_args,), daemon=True)
        self.worker.start()

    def run_speed_test_workflow(self, test_request, reporter):
        config = engine.load_config()
        note = int(test_request["note"])
        channel = int(test_request["channel"])
        capacity = engine.get_global_channel_capacity(config["pca9685"])
        if channel < 0 or channel >= capacity:
            raise RuntimeError(f"Channel {channel} is outside the configured PCA9685 range 0-{capacity - 1}.")

        events, pulse_info = build_speed_test_delta_events(
            note,
            channel,
            float(test_request["bpm"]),
            int(test_request["division"]),
            int(test_request["repeats"]),
            int(test_request["velocity"]),
            config,
        )
        reporter(
            "Speed test pulse: "
            f"velocity {int(test_request['velocity'])}, "
            f"strike {pulse_info['strike_pwm']}/4095 for {pulse_info['strike_ms']} ms, "
            f"hold {pulse_info['hold_pwm']}/4095, "
            f"retraction gap {pulse_info['release_gap_ms']} ms."
        )
        deployment_config = engine.load_deployment_config()
        serial_config = deployment_config.get("serial_runtime", {})
        status_poll_ms = int(serial_config.get("status_poll_ms", 25))

        connection = None
        playback_done_response = None
        try:
            connection, port, ready_info = piano_tools.open_runtime_connection()
            piano_tools.ensure_calibration_hardware_ready(ready_info, config["pca9685"], [channel])

            begin_response = engine.send_serial_command(
                connection,
                f"BEGIN {len(events)}",
                ("OK BEGIN",),
                timeout_seconds=2.0,
            )
            begin_fields = engine.parse_runtime_key_values(begin_response)
            buffer_capacity = int(begin_fields.get("capacity", ready_info["buffer_capacity"]))
            sent_event_count = engine.send_event_chunk(connection, events, 0, buffer_capacity)
            engine.send_serial_command(connection, "COMMIT", ("OK ACCEPTED",), timeout_seconds=2.0)
            play_response = engine.send_serial_command(connection, "PLAY", ("OK PLAYING",), timeout_seconds=2.0)

            while sent_event_count < len(events):
                status_response = engine.send_serial_command(connection, "STATUS", ("STATUS",), timeout_seconds=2.0)
                status_fields = engine.parse_status_response(status_response)
                free_slots = int(status_fields.get("free", 0))
                if free_slots <= 0:
                    time.sleep(status_poll_ms / 1000.0)
                    continue
                sent_event_count = engine.send_event_chunk(connection, events, sent_event_count, free_slots)
                engine.send_serial_command(connection, "COMMIT", ("OK ACCEPTED",), timeout_seconds=2.0)

            total_runtime_seconds = sum(event["dt_ms"] for event in events) / 1000.0
            playback_done_response, _control_action, _paused = engine.wait_for_playback_done(
                connection,
                timeout_seconds=max(8.0, total_runtime_seconds + 5.0),
            )

            reporter(
                f"Speed test burst complete: {test_request['note_label']} "
                f"at {test_request['speed_label']} / {float(test_request['bpm']):.2f} BPM."
            )
            return {
                "cancelled": False,
                "workflow_kind": "speed_test",
                "note": note,
                "note_label": test_request["note_label"],
                "channel": channel,
                "channel_target": test_request["channel_target"],
                "speed_label": test_request["speed_label"],
                "bpm": float(test_request["bpm"]),
                "period_ms": float(test_request["period_ms"]),
                "repeats": int(test_request["repeats"]),
                "velocity": int(test_request["velocity"]),
                "pulse": pulse_info,
                "event_count": len(events),
                "sent_event_count": sent_event_count,
                "port": port,
                "protocol_version": ready_info["protocol_version"],
                "buffer_capacity": buffer_capacity,
                "stream_response": play_response,
                "playback_done_response": playback_done_response,
            }
        finally:
            if connection is not None:
                try:
                    engine.send_serial_command(connection, "ALL_OFF", ("OK ALL_OFF",), timeout_seconds=2.0)
                except Exception:
                    pass
                connection.close()

    def load_speed_test_log_entries(self):
        if not SPEED_TEST_LOG_JSON_PATH.exists():
            return []
        try:
            payload = json.loads(SPEED_TEST_LOG_JSON_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if isinstance(payload, list):
            return [entry for entry in payload if isinstance(entry, dict)]
        return [entry for entry in payload.get("entries", []) if isinstance(entry, dict)]

    def save_speed_test_log_entries(self, entries):
        engine.METADATA_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "entries": entries,
        }
        SPEED_TEST_LOG_JSON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        with SPEED_TEST_LOG_CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=SPEED_TEST_LOG_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for entry in entries:
                writer.writerow({column: entry.get(column, "") for column in SPEED_TEST_LOG_COLUMNS})

    def build_speed_test_log_entry(self, request, status):
        if status not in {"meets", "slower_blends"}:
            raise ValueError(f"Unsupported speed test status: {status}")

        config = engine.load_config()
        _events, pulse_info = build_speed_test_delta_events(
            int(request["note"]),
            int(request["channel"]),
            float(request["bpm"]),
            int(request["division"]),
            int(request["repeats"]),
            int(request["velocity"]),
            config,
        )
        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "status": status,
            "note_label": request["note_label"],
            "note": int(request["note"]),
            "channel": int(request["channel"]),
            "channel_label": request["channel_label"],
            "channel_target": request["channel_target"],
            "speed_label": request["speed_label"],
            "division": int(request["division"]),
            "bpm": float(request["bpm"]),
            "period_ms": round(float(request["period_ms"]), 3),
            "repeats": int(request["repeats"]),
            "velocity": int(request["velocity"]),
            "strike_pwm": int(pulse_info["strike_pwm"]),
            "hold_pwm": int(pulse_info["hold_pwm"]),
            "strike_ms": int(pulse_info["strike_ms"]),
            "release_gap_ms": int(pulse_info["release_gap_ms"]),
            "saved_to_config": False,
            "saved_minimum_repeat_period_ms": "",
            "saved_playback_velocity_override": "",
        }

    def append_speed_test_log_entry(self, entry):
        entries = self.load_speed_test_log_entries()
        entries.append(dict(entry))
        self.save_speed_test_log_entries(entries)
        self.append_log(
            f"Speed test logged: {entry['note_label']} {entry['speed_label']} "
            f"at {entry['bpm']:.2f} BPM -> {entry['status']}."
        )
        return entries

    def save_speed_test_solenoid_settings(self, request, status):
        with engine.CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)

        channel = int(request["channel"])
        velocity = int(request["velocity"])
        minimum_repeat_period_ms = max(1, int(round(float(request["period_ms"]))))
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")

        actuation = config.setdefault("actuation", {})
        channel_overrides = actuation.setdefault("channel_overrides", {})
        override = channel_overrides.setdefault(str(channel), {})
        override["playback_velocity_override"] = velocity
        override["minimum_repeat_period_ms"] = minimum_repeat_period_ms
        override["speed_test_note"] = request["note_label"]
        override["speed_test_saved_status"] = status
        override["speed_test_speed_label"] = request["speed_label"]
        override["speed_test_bpm"] = round(float(request["bpm"]), 3)
        override["speed_test_period_ms"] = round(float(request["period_ms"]), 3)
        override["speed_test_saved_at"] = timestamp

        engine.CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        self.config_data = engine.load_config()
        self.append_log(
            f"Saved solenoid config for {request['note_label']} on channel {channel}: "
            f"velocity {velocity}, minimum repeat {minimum_repeat_period_ms} ms."
        )
        return {
            "playback_velocity_override": velocity,
            "minimum_repeat_period_ms": minimum_repeat_period_ms,
            "timestamp": timestamp,
        }

    def save_defect_debug_solenoid_settings(self, row, updates, reason):
        allowed_keys = {
            "strike_min_pwm",
            "minimum_rearm_gap_ms",
            "retrigger_gap_ms",
            "minimum_repeat_period_ms",
        }
        with engine.CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)

        channel = int(row["channel"])
        note = int(row["note"])
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")

        actuation = config.setdefault("actuation", {})
        channel_overrides = actuation.setdefault("channel_overrides", {})
        override = channel_overrides.setdefault(str(channel), {})
        for key, value in updates.items():
            if key not in allowed_keys:
                raise ValueError(f"Unsupported defective-note setting: {key}")
            override[key] = int(value)

        override["defect_debug_note"] = row["note_label"]
        override["defect_debug_last_reason"] = reason
        override["defect_debug_saved_at"] = timestamp

        engine.CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        self.config_data = engine.load_config()
        resolved = engine.resolve_note_actuation(note, channel, self.config_data)
        saved_settings = {
            "saved_playback_velocity_override": resolved.get("playback_velocity_override"),
            "strike_min_pwm": int(resolved["strike_min_pwm"]),
            "strike_max_pwm": int(resolved["strike_max_pwm"]),
            "strike_ms": int(resolved["strike_ms"]),
            "hold_min_pwm": int(resolved["hold_min_pwm"]),
            "hold_max_pwm": int(resolved["hold_max_pwm"]),
            "hold_ratio": float(resolved["hold_ratio"]),
            "release_delay_ms": int(resolved["release_delay_ms"]),
            "minimum_rearm_gap_ms": int(resolved["minimum_rearm_gap_ms"]),
            "retrigger_gap_ms": int(resolved["retrigger_gap_ms"]),
            "minimum_repeat_period_ms": int(resolved.get("minimum_repeat_period_ms", 0)),
        }
        changed = ", ".join(f"{key} {value}" for key, value in updates.items())
        self.append_log(f"Saved defective-note {reason} for {row['note_label']} on channel {channel}: {changed}.")
        return saved_settings

    def log_mapping_lines(self, mapping_lines):
        for line in mapping_lines:
            self.append_log(f"  {line}")

    def run_sweep_calibration(self, connection, config):
        self.append_log("Sweeping saved note mapping in musical order with regular playback actuation.")
        for note, channel in piano_tools.iter_mapping_in_note_order(config["mapping"]):
            pulse = piano_tools.build_regular_playback_pulse(note, channel, config)
            label = config["mapping"].get("channel_labels", {}).get(str(channel), f"Channel {channel}")
            channel_target = engine.describe_global_channel(channel, config["pca9685"])
            if note is not None:
                self.append_log(
                    f"  Testing {engine.midi_note_name(note)} on {channel_target}: {label} "
                    f"(velocity {engine.DIAGNOSTIC_MEDIUM_VELOCITY}, strike {pulse['strike_pwm']}, hold {pulse['hold_pwm']})"
                )
            else:
                self.append_log(f"  Firing {channel_target}: {label}")
            piano_tools.fire_channel(connection, channel, pulse)
            self.update()
            time.sleep(piano_tools.CALIBRATION_INTER_FIRE_DELAY_SECONDS)

    def calibrate_contiguous_octave_gui(self, connection, config, port, ready_info):
        self.run_sweep_calibration(connection, config)
        bottom_note_text = simpledialog.askstring(
            "Bottom Note",
            "Enter the bottom note of the contiguous keyboard range, such as C4.",
            parent=self,
        )
        if bottom_note_text is None:
            raise RuntimeError("Calibration cancelled before saving the contiguous range.")

        bottom_note = engine.parse_note_token(bottom_note_text.strip())
        mapping = piano_tools.contiguous_octave_mapping(config, bottom_note)
        mapping_lines = piano_tools.build_mapping_lines(mapping)

        if not messagebox.askyesno(
            "Save Contiguous Map",
            "Save this contiguous mapping?\n\n" + "\n".join(mapping_lines),
            parent=self,
        ):
            raise RuntimeError("Calibration cancelled before saving the contiguous range.")

        report_payload = {
            "mode": "contiguous_octave",
            "port": port,
            "protocol_version": ready_info["protocol_version"],
            "mapping_lines": mapping_lines,
            "mapping": mapping,
        }
        piano_tools.save_calibrated_mapping(mapping, report_payload)
        self.append_log("Saved contiguous mapping:")
        self.log_mapping_lines(mapping_lines)

    def calibrate_manual_mapping_gui(self, connection, config, port, ready_info):
        note_to_channel = {}
        note_labels = {}
        channel_labels = dict(config["mapping"].get("channel_labels", {}))
        channel_sequence = engine.get_mapping_channel_order(config["mapping"])
        pedal_channel = engine.get_pedal_channel(config["mapping"])

        self.append_log("Manual channel mapping started.")
        self.append_log("Each channel will fire once. Enter the piano note it moved, or leave blank to skip it.")

        for channel in channel_sequence:
            pulse = piano_tools.build_regular_playback_channel_pulse(channel, config)
            label = channel_labels.get(str(channel), f"Channel {channel}")
            channel_target = engine.describe_global_channel(channel, config["pca9685"])
            self.append_log(
                f"Firing {channel_target}: {label} "
                f"(regular playback pulse, velocity {engine.DIAGNOSTIC_MEDIUM_VELOCITY}, "
                f"strike {pulse['strike_pwm']}, hold {pulse['hold_pwm']})"
            )
            piano_tools.fire_channel(connection, channel, pulse)
            self.update()
            time.sleep(piano_tools.CALIBRATION_INTER_FIRE_DELAY_SECONDS)
            if pedal_channel is not None and int(channel) == int(pedal_channel):
                self.append_log("  Saved as the sustain pedal channel, not a piano note.")
                continue

            while True:
                raw = simpledialog.askstring(
                    "Manual Mapping",
                    f"{channel_target}\n{label}\n\nWhich piano note moved? Use a name like C4 or F#3.\nLeave blank to skip this channel.",
                    parent=self,
                )
                if raw is None or not raw.strip():
                    break
                try:
                    note = engine.parse_note_token(raw.strip())
                except ValueError as error:
                    messagebox.showerror("Invalid note", str(error), parent=self)
                    continue
                if str(note) in note_to_channel:
                    messagebox.showerror(
                        "Duplicate note",
                        "That note was already assigned. Enter a different note or leave this channel blank.",
                        parent=self,
                    )
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
            "pedal": copy.deepcopy(config["mapping"].get("pedal", {})),
        }
        mapping_lines = piano_tools.build_mapping_lines(mapping)

        if not messagebox.askyesno(
            "Save Manual Map",
            "Save this manual mapping?\n\n" + "\n".join(mapping_lines),
            parent=self,
        ):
            raise RuntimeError("Calibration cancelled before saving the manual mapping.")

        report_payload = {
            "mode": "manual_mapping",
            "port": port,
            "protocol_version": ready_info["protocol_version"],
            "mapping_lines": mapping_lines,
            "mapping": mapping,
        }
        piano_tools.save_calibrated_mapping(mapping, report_payload)
        self.append_log("Saved manual mapping:")
        self.log_mapping_lines(mapping_lines)

    def patch_manual_mapping_gui(self, connection, config, port, ready_info, patch_channels):
        existing_mapping = dict(config["mapping"])
        note_to_channel = dict(existing_mapping.get("note_to_channel", {}))
        note_labels = dict(existing_mapping.get("note_labels", {}))
        channel_labels = dict(existing_mapping.get("channel_labels", {}))
        channel_sequence = [int(channel) for channel in existing_mapping.get("channel_sequence", [])]
        pedal_channel = engine.get_pedal_channel(existing_mapping)
        missing_notes = piano_tools.infer_missing_notes(existing_mapping)
        added_assignments = []

        self.append_log("Patch existing note mapping started.")
        self.append_log(f"Unused channels to test: {', '.join(str(channel) for channel in patch_channels)}")
        if missing_notes:
            self.append_log(
                "Missing notes inferred from the saved span: "
                + ", ".join(engine.midi_note_name(note) for note in missing_notes)
            )
        self.append_log("Each unused channel will fire once. Enter the piano note it moved, or leave blank to skip it.")

        for channel in patch_channels:
            pulse = piano_tools.build_regular_playback_channel_pulse(channel, config)
            label = channel_labels.get(str(channel), f"Channel {channel}")
            channel_target = engine.describe_global_channel(channel, config["pca9685"])
            self.append_log(
                f"Firing {channel_target}: {label} "
                f"(regular playback pulse, velocity {engine.DIAGNOSTIC_MEDIUM_VELOCITY}, "
                f"strike {pulse['strike_pwm']}, hold {pulse['hold_pwm']})"
            )
            piano_tools.fire_channel(connection, channel, pulse)
            self.update()
            time.sleep(piano_tools.CALIBRATION_INTER_FIRE_DELAY_SECONDS)
            if pedal_channel is not None and int(channel) == int(pedal_channel):
                self.append_log("  This is the sustain pedal channel, so it stays out of the note map.")
                continue

            while True:
                prompt_lines = [
                    channel_target,
                    label,
                ]
                if missing_notes:
                    prompt_lines.extend(
                        [
                            "",
                            "Likely missing notes from the saved span:",
                            ", ".join(engine.midi_note_name(note) for note in missing_notes),
                        ]
                    )
                prompt_lines.extend(
                    [
                        "",
                        "Which piano note moved? Use a name like C4 or F#3.",
                        "Leave blank to skip this channel for now.",
                    ]
                )
                raw = simpledialog.askstring(
                    "Patch Saved Mapping",
                    "\n".join(prompt_lines),
                    parent=self,
                )
                if raw is None or not raw.strip():
                    break
                try:
                    note = engine.parse_note_token(raw.strip())
                except ValueError as error:
                    messagebox.showerror("Invalid note", str(error), parent=self)
                    continue
                if str(note) in note_to_channel:
                    messagebox.showerror(
                        "Duplicate note",
                        "That note is already assigned in the saved mapping. Enter a different note or leave this channel blank.",
                        parent=self,
                    )
                    continue
                note_to_channel[str(note)] = channel
                note_labels[str(note)] = engine.midi_note_name(note)
                added_assignments.append((note, channel))
                break

        if not added_assignments:
            raise RuntimeError("No new patch assignments were entered, so nothing was saved.")

        mapping = {
            "mode": "explicit_note_map",
            "note_to_channel": dict(sorted(note_to_channel.items(), key=lambda item: int(item[0]))),
            "note_labels": note_labels,
            "channel_labels": channel_labels,
            "channel_sequence": channel_sequence,
            "pedal": copy.deepcopy(existing_mapping.get("pedal", {})),
        }
        mapping_lines = piano_tools.build_mapping_lines(mapping)

        if not messagebox.askyesno(
            "Save Patched Map",
            "Save the updated mapping?\n\n" + "\n".join(mapping_lines),
            parent=self,
        ):
            raise RuntimeError("Patch mapping cancelled before saving the updated map.")

        report_payload = {
            "mode": "manual_patch",
            "port": port,
            "protocol_version": ready_info["protocol_version"],
            "mapping_lines": mapping_lines,
            "mapping": mapping,
            "patched_channels": [int(channel) for channel in patch_channels],
            "added_assignments": [
                {
                    "note": int(note),
                    "note_label": engine.midi_note_name(int(note)),
                    "channel": int(channel),
                }
                for note, channel in added_assignments
            ],
            "missing_notes_before": missing_notes,
        }
        piano_tools.save_calibrated_mapping(mapping, report_payload)
        self.append_log("Saved patched mapping:")
        self.log_mapping_lines(mapping_lines)

    def start_note_mapping_calibration(self):
        if self.worker is not None and self.worker.is_alive():
            messagebox.showinfo("Already running", "Wait for the current playback job to finish first.", parent=self)
            return

        dialog = CalibrationActionDialog(self)
        self.wait_window(dialog)
        if dialog.result is None:
            return

        try:
            active_channel_count = self.get_active_channel_count()
            if dialog.result == "patch":
                calibration_config, patch_channels, missing_notes = self.build_patch_mapping_config(active_channel_count)
                if not patch_channels:
                    raise RuntimeError("The saved mapping does not have any unused channels to patch.")
            elif dialog.result == "sweep":
                calibration_config, active_sequence = self.build_sweep_mapping_config(active_channel_count)
            else:
                calibration_config, active_sequence = self.build_active_calibration_config(active_channel_count)
        except ValueError as error:
            messagebox.showerror("Invalid hardware count", str(error), parent=self)
            return
        except RuntimeError as error:
            messagebox.showerror("Patch mapping unavailable", str(error), parent=self)
            return

        self.append_log("")
        self.append_log("Starting note mapping calibration...")
        if dialog.result == "patch":
            self.append_log(f"Unused channels to patch: {', '.join(str(channel) for channel in patch_channels)}")
            if missing_notes:
                self.append_log(
                    "Missing notes inferred from the saved span: "
                    + ", ".join(engine.midi_note_name(note) for note in missing_notes)
                )
            self.append_log(engine.summarize_active_channel_sequence(patch_channels, calibration_config["pca9685"]))
        else:
            self.append_log(engine.summarize_active_channel_sequence(active_sequence, calibration_config["pca9685"]))
        self.set_controls_enabled(False)
        self.update()

        connection = None
        try:
            connection, port, ready_info = piano_tools.open_runtime_connection()
            self.append_log(f"Connected to Arduino runtime on {port} (protocol v{ready_info['protocol_version']}).")
            if ready_info.get("i2c_warning"):
                self.append_log(f"I2C warning: {ready_info['i2c_warning']}")
            elif ready_info.get("i2c_info") and ready_info["i2c_info"].get("detected_addresses"):
                self.append_log(
                    "Detected PCA9685 addresses: "
                    f"{engine.format_i2c_address_list(ready_info['i2c_info']['detected_addresses'])}"
                )

            if dialog.result == "patch":
                piano_tools.ensure_calibration_hardware_ready(
                    ready_info,
                    calibration_config["pca9685"],
                    patch_channels,
                )
            else:
                piano_tools.ensure_calibration_hardware_ready(
                    ready_info,
                    calibration_config["pca9685"],
                    active_sequence,
                )

            if dialog.result == "sweep":
                self.run_sweep_calibration(connection, calibration_config)
                messagebox.showinfo("Sweep Complete", "Channel sweep complete.", parent=self)
            elif dialog.result == "contiguous":
                self.calibrate_contiguous_octave_gui(connection, calibration_config, port, ready_info)
                messagebox.showinfo(
                    "Calibration Saved",
                    f"Saved contiguous note mapping to {engine.CALIBRATED_MAPPING_PATH.name}.",
                    parent=self,
                )
            elif dialog.result == "manual":
                self.calibrate_manual_mapping_gui(connection, calibration_config, port, ready_info)
                messagebox.showinfo(
                    "Calibration Saved",
                    f"Saved manual note mapping to {engine.CALIBRATED_MAPPING_PATH.name}.",
                    parent=self,
                )
            else:
                self.patch_manual_mapping_gui(connection, calibration_config, port, ready_info, patch_channels)
                messagebox.showinfo(
                    "Patch Saved",
                    f"Saved patched note mapping to {engine.CALIBRATED_MAPPING_PATH.name}.",
                    parent=self,
                )

            self.config_data = engine.load_config()
        except Exception as error:
            self.append_log(f"Calibration error: {error}")
            messagebox.showerror("Calibration failed", str(error), parent=self)
        finally:
            if connection is not None:
                try:
                    engine.send_serial_command(connection, "ALL_OFF", ("OK ALL_OFF",), timeout_seconds=2.0)
                except Exception:
                    pass
                connection.close()
            self.set_controls_enabled(True)

    def start_run(self, dry_run):
        if self.worker is not None and self.worker.is_alive():
            with self.queue_lock:
                queue_is_playing = self.queue_is_playing
            message = (
                "Add songs to the queue while the current playback job runs."
                if queue_is_playing
                else "Wait for the current job to finish first."
            )
            messagebox.showinfo("Already running", message, parent=self)
            return

        if dry_run:
            self.start_single_song_dry_run()
            return

        self.start_queue_playback()

    def build_conversion_worker_args(self, item, run_options, dry_run, preferred_fit_mode=None, playback_control=None):
        if preferred_fit_mode is None:
            preferred_fit_mode = self.fit_mode_var.get()

        return {
            "workflow_kind": "conversion",
            "selected_midi_source": item["path"],
            "selection_reason": item["reason"],
            "active_channel_count": run_options["active_channel_count"],
            "preferred_range": run_options["preferred_range"],
            "preferred_fit_mode": preferred_fit_mode,
            "preferred_tempo": run_options["preferred_tempo"],
            "dry_run": dry_run,
            "export_only": run_options["export_only"],
            "allow_prompts": False,
            "performance_feel_enabled": run_options["performance_feel_enabled"],
            "auto_measure_pedal": run_options["auto_measure_pedal"],
            "playback_control": playback_control,
            "reporter": lambda message: self.message_queue.put(("log", message)),
        }

    def start_single_song_dry_run(self):
        if self.selected_song_path is None:
            messagebox.showinfo("Choose a song", "Pick a MIDI file first.", parent=self)
            return

        run_options = self.collect_run_options(base_tempo_bpm=120.0)
        if run_options is None:
            return

        item = self.build_queue_item(
            self.selected_song_path,
            self.selection_reason or "selected from the GUI",
            source="Current selection",
        )
        self.append_log("")
        self.append_log(f"Starting dry run for {item['display_name']}...")
        self.set_controls_enabled(False)

        worker_args = self.build_conversion_worker_args(item, run_options, dry_run=True)
        self.worker = threading.Thread(target=self._run_workflow, args=(worker_args,), daemon=True)
        self.worker.start()

    def start_queue_playback(self):
        if self.worker is not None and self.worker.is_alive():
            with self.queue_lock:
                queue_is_playing = self.queue_is_playing
            message = (
                "Add songs to the queue while the current playback job runs."
                if queue_is_playing
                else "Wait for the current job to finish first."
            )
            messagebox.showinfo("Already running", message, parent=self)
            return

        with self.queue_lock:
            queue_is_empty = not self.playback_queue

        if queue_is_empty:
            if self.selected_song_path is None:
                messagebox.showinfo("Choose a song", "Pick a MIDI file first or add songs to the queue.", parent=self)
                return

        run_options = self.collect_run_options(base_tempo_bpm=120.0)
        if run_options is None:
            return

        if queue_is_empty:
            with self.queue_lock:
                self.playback_queue.append(
                    self.build_queue_item(
                        self.selected_song_path,
                        self.selection_reason or "selected from the GUI",
                        source="Current selection",
                    )
                )

        self.append_log("")
        with self.queue_lock:
            queued_count = len(self.playback_queue)
            self.queue_is_playing = True
        self.playback_control = PlaybackControlState()
        self.append_log(f"Starting playback queue with {queued_count} song(s).")
        self.set_playback_controls_enabled(False)
        self.refresh_queue_list()

        worker_args = {
            "run_options": run_options,
            "preferred_fit_mode": self.fit_mode_var.get(),
        }
        self.worker = threading.Thread(target=self._run_queue_workflow, args=(worker_args,), daemon=True)
        self.worker.start()

    def collect_run_options(self, base_tempo_bpm):
        try:
            active_channel_count = self.get_active_channel_count()
        except ValueError as error:
            messagebox.showerror("Invalid hardware count", str(error), parent=self)
            return None

        preferred_range = self.range_var.get().strip()
        if preferred_range:
            try:
                engine.parse_inclusive_note_range(preferred_range)
            except ValueError as error:
                messagebox.showerror("Invalid note range", str(error), parent=self)
                return None
        else:
            preferred_range = ""

        preferred_tempo = self.tempo_var.get().strip()
        if preferred_tempo:
            try:
                engine.parse_tempo_override_input(preferred_tempo, base_tempo_bpm)
            except ValueError as error:
                messagebox.showerror("Invalid tempo", str(error), parent=self)
                return None
        else:
            preferred_tempo = ""

        return {
            "active_channel_count": active_channel_count,
            "preferred_range": preferred_range,
            "preferred_tempo": preferred_tempo,
            "performance_feel_enabled": self.performance_feel_var.get(),
            "auto_measure_pedal": self.auto_measure_pedal_var.get(),
            "export_only": self.export_only_var.get(),
        }

    def build_pedal_troubleshooting_channels(self, config, active_channel_count):
        capacity = engine.get_global_channel_capacity(config["pca9685"])
        configured_channel = engine.get_pedal_channel(config["mapping"])
        if configured_channel is None:
            configured_channel = max(0, int(active_channel_count) - 1)

        final_board_start = (configured_channel // engine.PCA9685_CHANNELS_PER_BOARD) * engine.PCA9685_CHANNELS_PER_BOARD
        final_board_end = min(final_board_start + engine.PCA9685_CHANNELS_PER_BOARD, capacity)
        candidates = [configured_channel, final_board_end - 1]
        candidates.extend(range(final_board_start, final_board_end))

        seen = set()
        return [
            int(channel)
            for channel in candidates
            if 0 <= int(channel) < capacity and not (int(channel) in seen or seen.add(int(channel)))
        ]

    def build_pedal_strength_defaults(self):
        config = engine.load_config()
        pedal_config = engine.get_pedal_config(config)
        down_pwm = int(pedal_config.get("down_pwm", config["actuation"]["strike_max_pwm"]))
        start_pwm = max(0, min(4095, down_pwm // 2))
        start_pwm = (start_pwm // 100) * 100
        return {
            "start_pwm": start_pwm,
            "end_pwm": max(start_pwm, min(4095, down_pwm)),
            "step_pwm": 250,
            "hold_ms": 900,
            "rest_ms": 1200,
            "scan_channels": False,
        }

    def build_pedal_strength_values(self, pedal_test):
        start_pwm = int(pedal_test["start_pwm"])
        end_pwm = int(pedal_test["end_pwm"])
        step_pwm = int(pedal_test["step_pwm"])
        values = list(range(start_pwm, end_pwm + 1, step_pwm))
        if values[-1] != end_pwm:
            values.append(end_pwm)
        return values

    def run_pedal_troubleshooting_workflow(self, active_channel_count, pedal_test, reporter):
        config = engine.load_config()
        if pedal_test["scan_channels"]:
            candidates = self.build_pedal_troubleshooting_channels(config, active_channel_count)
        else:
            configured = engine.get_pedal_channel(config["mapping"])
            candidates = [configured if configured is not None else max(0, int(active_channel_count) - 1)]
        configured_channel = engine.get_pedal_channel(config["mapping"])
        channel_labels = config["mapping"].get("channel_labels", {})
        strength_values = self.build_pedal_strength_values(pedal_test)

        connection = None
        try:
            connection, port, ready_info = piano_tools.open_runtime_connection()
            piano_tools.ensure_calibration_hardware_ready(ready_info, config["pca9685"], candidates)
            reporter("")
            reporter("Sustain pedal troubleshooting")
            reporter(f"Serial port: {port}")
            if configured_channel is None:
                reporter("No pedal channel is configured, so testing around the last active channel.")
            else:
                reporter(f"Configured pedal channel: {engine.describe_global_channel(configured_channel, config['pca9685'])}")
            reporter(
                "Watch the pedal linkage and note the first PWM that fully depresses sustain. "
                f"Ramp: {strength_values[0]}-{strength_values[-1]}/4095 in {pedal_test['step_pwm']} PWM steps, "
                f"{pedal_test['hold_ms']} ms hold, {pedal_test['rest_ms']} ms rest."
            )

            tested_channels = []
            tested_strengths = []
            for channel in candidates:
                actuation = engine.resolve_channel_actuation(channel, config)
                label = channel_labels.get(str(channel), f"Channel {channel}")
                channel_target = engine.describe_global_channel(channel, config["pca9685"])
                reporter(f"Testing {channel_target}: {label}")
                for strength_pwm in strength_values:
                    pulse = {
                        "strike_pwm": strength_pwm,
                        "hold_pwm": strength_pwm,
                        "strike_ms": max(120, int(actuation["strike_ms"])),
                        "hold_ms": int(pedal_test["hold_ms"]),
                        "release_ms": int(pedal_test["rest_ms"]),
                    }
                    reporter(f"  Sustain strength {strength_pwm}/4095")
                    piano_tools.fire_channel(connection, channel, pulse)
                    tested_strengths.append(strength_pwm)
                tested_channels.append(channel)

            reporter("Pedal troubleshooting complete.")
            return {
                "cancelled": False,
                "workflow_kind": "pedal_troubleshooting",
                "configured_channel": configured_channel,
                "tested_channels": tested_channels,
                "tested_strengths": tested_strengths,
                "pedal_test": dict(pedal_test),
                "port": port,
            }
        finally:
            if connection is not None:
                try:
                    engine.send_serial_command(connection, "ALL_OFF", ("OK ALL_OFF",), timeout_seconds=2.0)
                except Exception:
                    pass
                connection.close()

    def build_mosfet_test_defaults(self):
        if self.mosfet_test_defaults is not None:
            defaults = dict(self.mosfet_test_defaults)
            defaults.setdefault("velocity", engine.DIAGNOSTIC_MEDIUM_VELOCITY)
            return defaults

        return {
            "channel": 0,
            "velocity": engine.DIAGNOSTIC_MEDIUM_VELOCITY,
        }

    def run_mosfet_test_workflow(self, pulse, reporter):
        config = engine.load_config()
        channel = int(pulse["channel"])
        velocity = int(pulse.get("velocity", engine.DIAGNOSTIC_MEDIUM_VELOCITY))
        capacity = engine.get_global_channel_capacity(config["pca9685"])
        if channel < 0 or channel >= capacity:
            raise RuntimeError(f"Channel {channel} is outside the configured PCA9685 range 0-{capacity - 1}.")
        playback_pulse = piano_tools.build_regular_playback_channel_pulse(channel, config, velocity=velocity)
        mapped_note = piano_tools.mapped_note_for_channel(config["mapping"], channel)

        connection = None
        try:
            connection, port, ready_info = piano_tools.open_runtime_connection()
            piano_tools.ensure_calibration_hardware_ready(ready_info, config["pca9685"], [channel])

            channel_target = engine.describe_global_channel(channel, config["pca9685"])
            label = config["mapping"].get("channel_labels", {}).get(str(channel), f"Channel {channel}")
            reporter("")
            reporter("Channel test")
            reporter(f"Serial port: {port}")
            reporter(f"Testing {channel_target}: {label}")
            if mapped_note is not None:
                reporter(f"Mapped note: {engine.midi_note_name(mapped_note)} ({mapped_note})")
            else:
                reporter("Mapped note: none; using channel actuation with regular playback math")
            reporter(
                "Regular playback pulse: "
                f"velocity {velocity}, "
                f"strike {playback_pulse['strike_pwm']}/4095 for {playback_pulse['strike_ms']} ms, "
                f"hold {playback_pulse['hold_pwm']}/4095 for {playback_pulse['hold_ms']} ms, "
                f"release wait {playback_pulse['release_ms']} ms."
            )

            piano_tools.fire_channel(connection, channel, playback_pulse)
            reporter("Channel test complete. All outputs are off.")
            return {
                "cancelled": False,
                "workflow_kind": "mosfet_test",
                "channel": channel,
                "channel_target": channel_target,
                "velocity": velocity,
                "pulse": dict(playback_pulse),
                "port": port,
            }
        finally:
            if connection is not None:
                try:
                    engine.send_serial_command(connection, "ALL_OFF", ("OK ALL_OFF",), timeout_seconds=2.0)
                except Exception:
                    pass
                connection.close()

    def start_mosfet_test(self):
        if self.worker is not None and self.worker.is_alive():
            messagebox.showinfo("Already running", "Wait for the current playback job to finish first.", parent=self)
            return

        dialog = MosfetTestDialog(self, self.build_mosfet_test_defaults())
        self.wait_window(dialog)
        if dialog.result is None:
            return
        self.mosfet_test_defaults = dict(dialog.result)

        self.append_log("")
        self.append_log(
            f"Starting regular-playback channel test on global channel {dialog.result['channel']} "
            f"at velocity {dialog.result['velocity']}..."
        )
        self.set_controls_enabled(False)

        worker_args = {
            "workflow_kind": "mosfet_test",
            "pulse": dialog.result,
            "reporter": lambda message: self.message_queue.put(("log", message)),
        }
        self.worker = threading.Thread(target=self._run_workflow, args=(worker_args,), daemon=True)
        self.worker.start()

    def start_troubleshooting_run(self):
        if self.worker is not None and self.worker.is_alive():
            messagebox.showinfo("Already running", "Wait for the current playback job to finish first.", parent=self)
            return

        dialog = TroubleshootingActionDialog(self)
        self.wait_window(dialog)
        if dialog.result is None:
            return

        run_options = self.collect_run_options(base_tempo_bpm=engine.DIAGNOSTIC_BASE_BPM)
        if run_options is None:
            return
        pedal_test = None
        if dialog.result == "pedal":
            pedal_dialog = PedalStrengthDialog(self, self.build_pedal_strength_defaults())
            self.wait_window(pedal_dialog)
            if pedal_dialog.result is None:
                return
            pedal_test = dict(pedal_dialog.result)

        key_label = "Full sweep" if dialog.result == "full" else dialog.result.title()
        self.append_log("")
        if dialog.result == "pedal":
            self.append_log(
                "Starting sustain pedal strength ramp "
                f"({pedal_test['start_pwm']}-{pedal_test['end_pwm']}/4095)..."
            )
        elif dialog.result == "full":
            self.append_log("Starting full sweep troubleshooting...")
        else:
            self.append_log(f"Starting {key_label.lower()} key troubleshooting...")
        self.set_controls_enabled(False)
        self.note_marker_control = None

        if dialog.result == "pedal":
            worker_args = {
                "workflow_kind": "pedal_troubleshooting",
                "active_channel_count": run_options["active_channel_count"],
                "pedal_test": pedal_test,
                "reporter": lambda message: self.message_queue.put(("log", message)),
            }
        else:
            playback_control = None
            if dialog.result == "full" and not run_options["export_only"]:
                playback_control = PlaybackControlState()
                self.note_marker_control = playback_control
                self.append_log(
                    "During the full sweep, press Mark Current Note, Enter, or Space to save the most recently played note."
                )
                self.refresh_note_marker_controls()
                self.show_sweep_marker_dialog()
                self.focus_force()
            worker_args = {
                "workflow_kind": "troubleshooting",
                "key_color": dialog.result,
                "active_channel_count": run_options["active_channel_count"],
                "preferred_range": run_options["preferred_range"],
                "preferred_tempo": run_options["preferred_tempo"],
                "dry_run": False,
                "export_only": run_options["export_only"],
                "allow_prompts": False,
                "playback_control": playback_control,
                "reporter": lambda message: self.message_queue.put(("log", message)),
            }

        self.worker = threading.Thread(target=self._run_workflow, args=(worker_args,), daemon=True)
        self.worker.start()

    def _run_workflow(self, worker_args):
        workflow_kind = worker_args.get("workflow_kind", "conversion")
        try:
            workflow_kind = worker_args.pop("workflow_kind", "conversion")
            if workflow_kind == "troubleshooting":
                result = engine.run_troubleshooting_workflow(**worker_args)
            elif workflow_kind == "pedal_troubleshooting":
                result = self.run_pedal_troubleshooting_workflow(**worker_args)
            elif workflow_kind == "mosfet_test":
                result = self.run_mosfet_test_workflow(**worker_args)
            elif workflow_kind == "speed_test":
                result = self.run_speed_test_workflow(**worker_args)
            else:
                result = engine.run_conversion_workflow(**worker_args)
        except Exception as error:
            self.message_queue.put(("error", {"workflow_kind": workflow_kind, "message": str(error)}))
            return

        self.message_queue.put(("done", result))

    def pop_next_queue_item_for_playback(self):
        with self.queue_lock:
            if not self.playback_queue:
                return None
            return self.playback_queue.pop(0)

    def wait_for_late_queue_item(self, previous_song_finished_at):
        while time.time() - previous_song_finished_at < QUEUE_INTER_SONG_DELAY_SECONDS:
            item = self.pop_next_queue_item_for_playback()
            if item is not None:
                return item
            time.sleep(0.1)
        return None

    def _run_queue_workflow(self, worker_args):
        run_options = worker_args["run_options"]
        preferred_fit_mode = worker_args["preferred_fit_mode"]
        playback_control = self.playback_control
        results = []
        previous_song_finished_at = None

        try:
            while True:
                item = self.pop_next_queue_item_for_playback()
                if item is None and previous_song_finished_at is not None:
                    self.message_queue.put(("queue_wait", {"seconds": QUEUE_INTER_SONG_DELAY_SECONDS, "waiting_for_song": True}))
                    item = self.wait_for_late_queue_item(previous_song_finished_at)
                if item is None:
                    break

                if previous_song_finished_at is not None:
                    remaining_delay = QUEUE_INTER_SONG_DELAY_SECONDS - (time.time() - previous_song_finished_at)
                    if remaining_delay > 0:
                        self.message_queue.put(("queue_wait", {"seconds": remaining_delay, "waiting_for_song": False}))
                        time.sleep(remaining_delay)

                with self.queue_lock:
                    self.current_queue_item = item
                self.message_queue.put(("queue_item_started", item))
                conversion_args = self.build_conversion_worker_args(
                    item,
                    run_options,
                    dry_run=False,
                    preferred_fit_mode=preferred_fit_mode,
                    playback_control=playback_control,
                )
                conversion_args.pop("workflow_kind", None)
                result = engine.run_conversion_workflow(**conversion_args)
                stream_manifest = result.get("stream_manifest") or {}
                control_action = stream_manifest.get("control_action")
                previous_song_finished_at = time.time()
                with self.queue_lock:
                    if self.current_queue_item == item:
                        self.current_queue_item = None
                if control_action == "replay":
                    with self.queue_lock:
                        self.playback_queue.insert(0, item)
                    self.message_queue.put(("queue_item_replay", item))
                    previous_song_finished_at = None
                    continue
                if control_action == "skip":
                    self.message_queue.put(("queue_item_skipped", item))
                    continue

                results.append(result)
                self.message_queue.put(("queue_item_done", result))
        except Exception as error:
            with self.queue_lock:
                self.current_queue_item = None
            self.message_queue.put(("queue_error", str(error)))
            return

        self.message_queue.put(("queue_done", results))

    def process_worker_messages(self):
        try:
            while True:
                message_type, payload = self.message_queue.get_nowait()
                if message_type == "log":
                    self.append_log(payload)
                elif message_type == "song_catalog":
                    self.song_catalog_refresh_in_progress = False
                    self.apply_song_catalog(
                        payload["catalog"],
                        use_suggested=payload.get("use_suggested", False),
                        force_suggested=payload.get("force_suggested", False),
                        reveal_selection=payload.get("reveal_selection", False),
                    )
                    if self.pending_song_catalog_refresh is not None:
                        pending_refresh = self.pending_song_catalog_refresh
                        self.pending_song_catalog_refresh = None
                        self.refresh_song_catalog_async(**pending_refresh)
                elif message_type == "song_catalog_error":
                    self.song_catalog_refresh_in_progress = False
                    self.update_song_catalog_status()
                    self.append_log(f"Song catalog refresh error: {payload}")
                    if self.pending_song_catalog_refresh is not None:
                        pending_refresh = self.pending_song_catalog_refresh
                        self.pending_song_catalog_refresh = None
                        self.refresh_song_catalog_async(**pending_refresh)
                elif message_type == "error":
                    if isinstance(payload, dict):
                        error_kind = payload.get("workflow_kind")
                        error_message = payload.get("message", "")
                    else:
                        error_kind = None
                        error_message = str(payload)
                    self.set_controls_enabled(True)
                    self.worker = None
                    if error_kind == "speed_test" and self.speed_test_dialog is not None and self.speed_test_dialog.winfo_exists():
                        self.speed_test_dialog.speed_test_finished(error_message=error_message)
                    if self.defect_debug_dialog is not None and self.defect_debug_dialog.winfo_exists():
                        self.defect_debug_dialog.status_var.set(f"Debug run failed: {error_message}")
                    if self.note_marker_control is not None:
                        marked_lines = self.note_marker_control.get_marked_note_lines()
                        if marked_lines:
                            self.append_log("Full sweep marked notes before the error:")
                            for line in marked_lines:
                                self.append_log(f"  {line}")
                        self.note_marker_control = None
                        self.refresh_note_marker_controls()
                        self.close_sweep_marker_dialog()
                    self.append_log(f"Error: {error_message}")
                    messagebox.showerror("Run failed", error_message, parent=self)
                elif message_type == "queue_item_started":
                    self.append_log(f"Queue now playing: {payload['display_name']}")
                    self.refresh_queue_list()
                elif message_type == "queue_item_done":
                    if payload.get("cancelled"):
                        self.append_log("Queued song cancelled before conversion.")
                    else:
                        self.append_log(f"Finished queued song: {payload['selected_midi'].name}")
                    self.refresh_queue_list()
                elif message_type == "queue_item_replay":
                    self.append_log(f"Replaying queued song: {payload['display_name']}")
                    self.refresh_queue_list()
                elif message_type == "queue_item_skipped":
                    self.append_log(f"Skipped queued song: {payload['display_name']}")
                    self.refresh_queue_list()
                elif message_type == "queue_wait":
                    seconds = float(payload.get("seconds", QUEUE_INTER_SONG_DELAY_SECONDS))
                    if payload.get("waiting_for_song"):
                        self.queue_status_var.set(
                            f"Song finished. Add another within {QUEUE_INTER_SONG_DELAY_SECONDS:.0f} seconds to continue."
                        )
                    else:
                        self.queue_status_var.set(f"Waiting {seconds:.1f} seconds before the next queued song...")
                elif message_type == "queue_error":
                    self.set_playback_controls_enabled(True)
                    self.worker = None
                    with self.queue_lock:
                        self.queue_is_playing = False
                        self.current_queue_item = None
                    self.playback_control = None
                    self.refresh_queue_list()
                    self.append_log(f"Queue error: {payload}")
                    messagebox.showerror("Queue failed", payload, parent=self)
                elif message_type == "queue_done":
                    self.set_playback_controls_enabled(True)
                    self.worker = None
                    with self.queue_lock:
                        self.queue_is_playing = False
                        self.current_queue_item = None
                    self.playback_control = None
                    self.refresh_queue_list()
                    results = [result for result in payload if not result.get("cancelled")]
                    self.append_log("Queue complete.")
                    if len(results) == 1:
                        result = results[0]
                        if result["payload"] is None:
                            title = "Dry run complete"
                        elif result["stream_manifest"] is None:
                            title = "Export complete"
                        else:
                            title = "Playback complete"
                        summary = (
                            f"Finished {result['selected_midi'].name}\n"
                            f"Active hardware channels: {result['metadata']['active_hardware_channel_count']}\n"
                            f"Mode: {result['metadata']['fit_mode_label']}\n"
                            f"Effective tempo: {result['tempo_override']['target_bpm']:.2f} BPM"
                        )
                    else:
                        title = "Queue complete"
                        song_lines = [f"{index}. {result['selected_midi'].name}" for index, result in enumerate(results, start=1)]
                        summary = (
                            f"Finished {len(results)} song(s)\n"
                            f"Delay between songs: {QUEUE_INTER_SONG_DELAY_SECONDS:.0f} seconds\n\n"
                            + "\n".join(song_lines[:8])
                        )
                        if len(song_lines) > 8:
                            summary += f"\n...and {len(song_lines) - 8} more"
                    self.show_completion_dialog(title, summary)
                elif message_type == "done":
                    self.set_controls_enabled(True)
                    self.worker = None
                    result = payload
                    if result.get("workflow_kind") == "speed_test":
                        speed_dialog_open = self.speed_test_dialog is not None and self.speed_test_dialog.winfo_exists()
                        if self.speed_test_dialog is not None and self.speed_test_dialog.winfo_exists():
                            self.speed_test_dialog.speed_test_finished(result)
                        if self.defect_debug_dialog is not None and self.defect_debug_dialog.winfo_exists():
                            self.defect_debug_dialog.status_var.set(
                                f"Played {result['note_label']} repeat burst at {result['speed_label']}."
                            )
                        if speed_dialog_open:
                            self.append_log("Use Meets Benchmark or Slower / Blends in the speed test window to log this result.")
                        continue
                    if result.get("cancelled"):
                        self.append_log("Cancelled before conversion.")
                    else:
                        if result["workflow_kind"] == "mosfet_test":
                            if self.defect_debug_dialog is not None and self.defect_debug_dialog.winfo_exists():
                                self.defect_debug_dialog.status_var.set(
                                    f"Played one pulse on channel {result['channel']} at velocity {result.get('velocity')}."
                                )
                            title = "Channel test complete"
                            pulse = result["pulse"]
                            summary = (
                                f"Finished channel test on channel {result['channel']}\n"
                                f"{result['channel_target']}\n"
                                f"Velocity: {result.get('velocity', engine.DIAGNOSTIC_MEDIUM_VELOCITY)}\n"
                                f"Strike: {pulse['strike_pwm']}/4095 for {pulse['strike_ms']} ms\n"
                                f"Hold: {pulse['hold_pwm']}/4095 for {pulse['hold_ms']} ms"
                            )
                        elif result["workflow_kind"] == "pedal_troubleshooting":
                            title = "Pedal troubleshooting complete"
                            tested = ", ".join(str(channel) for channel in result["tested_channels"])
                            configured = result.get("configured_channel")
                            configured_text = "none" if configured is None else str(configured)
                            pedal_test = result["pedal_test"]
                            summary = (
                                "Finished sustain pedal troubleshooting\n"
                                f"Configured channel: {configured_text}\n"
                                f"Tested channels: {tested}\n"
                                f"Strength ramp: {pedal_test['start_pwm']}-{pedal_test['end_pwm']}/4095"
                            )
                        elif result["workflow_kind"] == "troubleshooting":
                            if result["payload"] is None:
                                title = "Troubleshooting dry run complete"
                            elif result["stream_manifest"] is None:
                                title = "Troubleshooting export complete"
                            else:
                                title = "Troubleshooting complete"
                            _diag_color = result["metadata"].get("diagnostic_key_color", "selected")
                            key_label = "Full sweep" if _diag_color == "full" else _diag_color.title()
                            summary = (
                                f"Finished {key_label.lower()} troubleshooting\n"
                                f"Active hardware channels: {result['metadata']['active_hardware_channel_count']}\n"
                                f"Steps: {result['metadata'].get('diagnostic_step_count', 0)}\n"
                                f"Effective tempo: {result['tempo_override']['target_bpm']:.2f} BPM"
                            )
                            if _diag_color == "full" and self.note_marker_control is not None:
                                marked_lines = self.note_marker_control.get_marked_note_lines()
                                if marked_lines:
                                    self.append_log("Full sweep marked notes:")
                                    for line in marked_lines:
                                        self.append_log(f"  {line}")
                                    summary += "\n\nMarked notes:\n" + "\n".join(marked_lines[:12])
                                    if len(marked_lines) > 12:
                                        summary += f"\n...and {len(marked_lines) - 12} more"
                                else:
                                    self.append_log("Full sweep marked notes: none")
                                self.note_marker_control = None
                                self.refresh_note_marker_controls()
                                self.close_sweep_marker_dialog()
                        else:
                            if result["payload"] is None:
                                title = "Dry run complete"
                            elif result["stream_manifest"] is None:
                                title = "Export complete"
                            else:
                                title = "Playback complete"
                            summary = (
                                f"Finished {result['selected_midi'].name}\n"
                                f"Active hardware channels: {result['metadata']['active_hardware_channel_count']}\n"
                                f"Mode: {result['metadata']['fit_mode_label']}\n"
                                f"Effective tempo: {result['tempo_override']['target_bpm']:.2f} BPM"
                            )
                        self.append_log("Done.")
                        self.show_completion_dialog(title, summary)
        except queue.Empty:
            pass

        self.refresh_playback_control_buttons()
        self.after(100, self.process_worker_messages)


def main():
    app = PianoPlayerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
