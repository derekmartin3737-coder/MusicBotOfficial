"""Tkinter launcher for user-friendly piano playback.

Run this from an IDE or by double-clicking the batch file. It wraps the normal
conversion/playback engine with a small desktop UI so the user can choose a
song, tempo, and current hardware note range without answering terminal prompts.
"""

from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

import convert_midi as engine
import piano_tools


class SongPickerDialog(tk.Toplevel):
    def __init__(self, parent, entries):
        super().__init__(parent)
        self.title("Choose a Song")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.entries = list(entries)
        self.filtered_entries = list(entries)
        self.result = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Available songs", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(14, 6)
        )

        search_frame = ttk.Frame(self)
        search_frame.grid(row=1, column=0, sticky="nsew", padx=14)
        search_frame.columnconfigure(0, weight=1)
        search_frame.rowconfigure(1, weight=1)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        search_entry.bind("<KeyRelease>", self.refresh_list)

        self.listbox = tk.Listbox(search_frame, height=18)
        self.listbox.grid(row=1, column=0, sticky="nsew")
        self.listbox.bind("<Double-Button-1>", self.use_selected)

        scrollbar = ttk.Scrollbar(search_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, sticky="ew", padx=14, pady=14)
        button_frame.columnconfigure(0, weight=1)

        ttk.Button(button_frame, text="Browse for MIDI...", command=self.browse_for_song).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(button_frame, text="Cancel", command=self.cancel).grid(
            row=0, column=1, padx=(8, 0)
        )
        ttk.Button(button_frame, text="Use Selected Song", command=self.use_selected).grid(
            row=0, column=2, padx=(8, 0)
        )

        self.refresh_list()
        search_entry.focus_set()

    def refresh_list(self, _event=None):
        query = self.search_var.get().strip().lower()
        self.filtered_entries = [
            entry
            for entry in self.entries
            if not query or query in entry["description"].lower() or query in entry["display_name"].lower()
        ]

        self.listbox.delete(0, tk.END)
        for entry in self.filtered_entries:
            self.listbox.insert(tk.END, entry["description"])

        if self.filtered_entries:
            self.listbox.selection_set(0)

    def browse_for_song(self):
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Choose a MIDI File",
            filetypes=[("MIDI files", "*.mid *.midi"), ("All files", "*.*")],
        )
        if not chosen:
            return

        chosen_path = Path(chosen)
        self.result = {
            "path": chosen_path,
            "source": "External file",
            "display_name": chosen_path.name,
            "description": f"External file | {chosen_path.name}",
        }
        self.destroy()

    def use_selected(self, _event=None):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("Choose a song", "Select a song from the list or browse for a MIDI file.", parent=self)
            return

        self.result = self.filtered_entries[selection[0]]
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


class CalibrationActionDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Note Mapping Calibration")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.action_var = tk.StringVar(value="manual")

        outer = ttk.Frame(self, padding=16)
        outer.grid(row=0, column=0, sticky="nsew")

        ttk.Label(
            outer,
            text="Choose a note mapping action",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            outer,
            text="Use manual mapping when the installed notes are not one clean contiguous span.",
            wraplength=420,
        ).grid(row=1, column=0, sticky="w", pady=(6, 12))

        ttk.Radiobutton(
            outer,
            text="Sweep channels only",
            variable=self.action_var,
            value="sweep",
        ).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Radiobutton(
            outer,
            text="Save contiguous octave map",
            variable=self.action_var,
            value="contiguous",
        ).grid(row=3, column=0, sticky="w", pady=2)
        ttk.Radiobutton(
            outer,
            text="Save manual channel-to-note map",
            variable=self.action_var,
            value="manual",
        ).grid(row=4, column=0, sticky="w", pady=2)

        button_row = ttk.Frame(outer)
        button_row.grid(row=5, column=0, sticky="e", pady=(14, 0))
        ttk.Button(button_row, text="Cancel", command=self.cancel).grid(row=0, column=0)
        ttk.Button(button_row, text="Continue", command=self.accept).grid(row=0, column=1, padx=(8, 0))

    def accept(self):
        self.result = self.action_var.get()
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


class PianoPlayerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Autonomous Piano Player")
        self.geometry("820x720")
        self.minsize(720, 620)

        self.user_preferences = engine.load_user_preferences()
        self.config_data = engine.load_config()
        self.song_catalog = None
        self.selected_song_path = None
        self.selection_reason = ""
        self.worker = None
        self.message_queue = queue.Queue()
        playback_preferences = self.user_preferences.get("playback", {})
        default_active_channels = playback_preferences.get(
            "default_active_channels",
            len(engine.get_mapping_channel_order(self.config_data["mapping"])),
        )
        default_playable_range = playback_preferences.get("default_playable_range", "")

        self.song_name_var = tk.StringVar(value="No song selected")
        self.song_reason_var = tk.StringVar(value="")
        self.song_info_var = tk.StringVar(value="No MIDI selected yet.")
        self.active_channels_var = tk.StringVar(value=str(default_active_channels))
        self.tempo_var = tk.StringVar(value="")
        self.range_var = tk.StringVar(value=str(default_playable_range))
        self.fit_mode_var = tk.StringVar(value="transpose")
        self.export_only_var = tk.BooleanVar(value=False)

        self._build_layout()
        self.refresh_song_catalog(use_suggested=True)
        self.after(100, self.process_worker_messages)

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        outer = ttk.Frame(self, padding=18)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=1)

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Autonomous Piano Player", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Suggested song first, then a few playback choices.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        song_frame = ttk.LabelFrame(outer, text="Song")
        song_frame.grid(row=1, column=0, sticky="ew", pady=(14, 10))
        song_frame.columnconfigure(1, weight=1)
        ttk.Label(song_frame, text="Latest found MIDI song:").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))
        ttk.Label(song_frame, textvariable=self.song_name_var, font=("Segoe UI", 11, "bold")).grid(
            row=0, column=1, sticky="w", padx=(0, 12), pady=(12, 4)
        )
        ttk.Label(song_frame, textvariable=self.song_reason_var).grid(
            row=1, column=1, sticky="w", padx=(0, 12), pady=(0, 8)
        )
        ttk.Label(song_frame, textvariable=self.song_info_var, wraplength=720).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 12)
        )

        song_button_row = ttk.Frame(song_frame)
        song_button_row.grid(row=0, column=2, rowspan=3, sticky="ne", padx=12, pady=12)
        ttk.Button(song_button_row, text="Choose Different Song...", command=self.choose_song).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(song_button_row, text="Refresh List", command=self.refresh_song_catalog).grid(
            row=1, column=0, sticky="ew", pady=(8, 0)
        )

        options_frame = ttk.LabelFrame(outer, text="Playback Options")
        options_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)

        ttk.Label(options_frame, text="Installed solenoids:").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))
        ttk.Entry(options_frame, textvariable=self.active_channels_var).grid(
            row=0, column=1, sticky="ew", padx=(0, 12), pady=(12, 4)
        )
        ttk.Label(
            options_frame,
            text="How many hardware channels are active right now. The current bench default is 31.",
            wraplength=620,
        ).grid(row=1, column=1, sticky="w", padx=(0, 12), pady=(0, 8))

        ttk.Label(options_frame, text="Tempo override:").grid(row=2, column=0, sticky="w", padx=12, pady=(4, 4))
        ttk.Entry(options_frame, textvariable=self.tempo_var).grid(row=2, column=1, sticky="ew", padx=(0, 12), pady=(4, 4))
        ttk.Label(
            options_frame,
            text="Leave blank for the original timing. You can enter 140, 0.85x, or 92bpm.",
        ).grid(row=3, column=1, sticky="w", padx=(0, 12), pady=(0, 8))

        ttk.Label(options_frame, text="Available note range:").grid(row=4, column=0, sticky="w", padx=12, pady=(4, 4))
        ttk.Entry(options_frame, textvariable=self.range_var).grid(row=4, column=1, sticky="ew", padx=(0, 12), pady=(4, 4))
        ttk.Label(
            options_frame,
            text=(
                "Leave blank to use the saved note mapping. "
                "Your current 31-solenoid setup spans C2 to B4 but is non-contiguous in octave 2, "
                "so blank is the correct default unless you want a temporary contiguous override like C3-B3."
            ),
            wraplength=620,
        ).grid(row=5, column=1, sticky="w", padx=(0, 12), pady=(0, 8))

        ttk.Label(options_frame, text="Out-of-range notes:").grid(row=6, column=0, sticky="w", padx=12, pady=(4, 12))
        fit_mode_box = ttk.Combobox(
            options_frame,
            state="readonly",
            values=("transpose", "strict"),
            textvariable=self.fit_mode_var,
        )
        fit_mode_box.grid(row=6, column=1, sticky="w", padx=(0, 12), pady=(4, 12))
        ttk.Checkbutton(
            options_frame,
            text="Export only (prepare files but do not send to Arduino)",
            variable=self.export_only_var,
        ).grid(row=7, column=1, sticky="w", padx=(0, 12), pady=(0, 12))

        action_frame = ttk.Frame(outer)
        action_frame.grid(row=3, column=0, sticky="ew")
        ttk.Button(action_frame, text="Run Dry Check", command=lambda: self.start_run(dry_run=True)).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(action_frame, text="Play / Send to Arduino", command=lambda: self.start_run(dry_run=False)).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        ttk.Button(action_frame, text="Calibrate Note Mapping...", command=self.start_note_mapping_calibration).grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )

        log_frame = ttk.LabelFrame(outer, text="Status")
        log_frame.grid(row=4, column=0, sticky="nsew", pady=(12, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=18, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.log_text.configure(state="disabled")

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=12)
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def set_controls_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for child in self.winfo_children():
            self._set_child_state_recursive(child, state)

    def _set_child_state_recursive(self, widget, state):
        try:
            if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton)):
                widget.configure(state=state if not isinstance(widget, ttk.Combobox) else ("readonly" if state == "normal" else "disabled"))
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_child_state_recursive(child, state)

    def append_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def refresh_song_catalog(self, use_suggested=False):
        self.song_catalog = engine.build_song_catalog(self.user_preferences)
        if use_suggested or self.selected_song_path is None:
            suggested_path = self.song_catalog.get("suggested_path")
            suggested_reason = self.song_catalog.get("suggested_reason")
            if suggested_path is not None:
                self.set_selected_song(suggested_path, suggested_reason)
                return

        if self.selected_song_path is None:
            self.song_name_var.set("No MIDI files found")
            latest_zip = self.song_catalog.get("latest_zip")
            if latest_zip is not None:
                self.song_reason_var.set(f"Newest download looks like a ZIP archive: {latest_zip.name}")
            else:
                self.song_reason_var.set("Use Choose Different Song... to browse for a MIDI file.")
            self.song_info_var.set("No project-library or Downloads MIDI files were found yet.")

    def choose_song(self):
        entries = self.song_catalog.get("entries", []) if self.song_catalog else []
        dialog = SongPickerDialog(self, entries)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        self.set_selected_song(dialog.result["path"], f"manually chosen from {dialog.result['source']}")

    def set_selected_song(self, midi_path, reason):
        self.selected_song_path = Path(midi_path)
        self.selection_reason = reason
        self.song_name_var.set(self.selected_song_path.name)
        self.song_reason_var.set(reason)
        self.update_song_preview()

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

    def log_mapping_lines(self, mapping_lines):
        for line in mapping_lines:
            self.append_log(f"  {line}")

    def run_sweep_calibration(self, connection, config):
        self.append_log("Sweeping active hardware channels in global channel order.")
        for channel, mapped_notes in piano_tools.iter_calibration_channels(config["mapping"]):
            actuation = engine.resolve_channel_actuation(channel, config)
            pulse = piano_tools.build_calibration_pulse(actuation)
            label = config["mapping"].get("channel_labels", {}).get(str(channel), f"Channel {channel}")
            channel_target = engine.describe_global_channel(channel, config["pca9685"])
            if len(mapped_notes) == 1:
                self.append_log(f"  Testing {engine.midi_note_name(mapped_notes[0])} on {channel_target}: {label}")
            elif len(mapped_notes) > 1:
                notes = ", ".join(engine.midi_note_name(note) for note in mapped_notes)
                self.append_log(f"  Firing {channel_target}: {label} (currently mapped to {notes})")
            else:
                self.append_log(f"  Firing {channel_target}: {label}")
            piano_tools.fire_channel(connection, channel, pulse)
            self.update()
            time.sleep(0.25)

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

        self.append_log("Manual channel mapping started.")
        self.append_log("Each channel will fire once. Enter the piano note it moved, or leave blank to skip it.")

        for channel in channel_sequence:
            actuation = engine.resolve_channel_actuation(channel, config)
            pulse = piano_tools.build_calibration_pulse(actuation)
            label = channel_labels.get(str(channel), f"Channel {channel}")
            channel_target = engine.describe_global_channel(channel, config["pca9685"])
            self.append_log(f"Firing {channel_target}: {label}")
            piano_tools.fire_channel(connection, channel, pulse)
            self.update()

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
            calibration_config, active_sequence = self.build_active_calibration_config(active_channel_count)
        except ValueError as error:
            messagebox.showerror("Invalid hardware count", str(error), parent=self)
            return

        self.append_log("")
        self.append_log("Starting note mapping calibration...")
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
            else:
                self.calibrate_manual_mapping_gui(connection, calibration_config, port, ready_info)
                messagebox.showinfo(
                    "Calibration Saved",
                    f"Saved manual note mapping to {engine.CALIBRATED_MAPPING_PATH.name}.",
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
            messagebox.showinfo("Already running", "Wait for the current playback job to finish first.", parent=self)
            return

        if self.selected_song_path is None:
            messagebox.showinfo("Choose a song", "Pick a MIDI file first.", parent=self)
            return

        try:
            active_channel_count = self.get_active_channel_count()
        except ValueError as error:
            messagebox.showerror("Invalid hardware count", str(error), parent=self)
            return

        preferred_range = self.range_var.get().strip()
        if preferred_range:
            try:
                engine.parse_inclusive_note_range(preferred_range)
            except ValueError as error:
                messagebox.showerror("Invalid note range", str(error), parent=self)
                return
        else:
            preferred_range = ""

        preferred_tempo = self.tempo_var.get().strip()
        if preferred_tempo:
            try:
                engine.parse_tempo_override_input(preferred_tempo, 120.0)
            except ValueError as error:
                messagebox.showerror("Invalid tempo", str(error), parent=self)
                return
        else:
            preferred_tempo = ""

        self.append_log("")
        self.append_log(f"Starting {'dry run' if dry_run else 'playback'} for {self.selected_song_path.name}...")
        self.set_controls_enabled(False)

        worker_args = {
            "selected_midi_source": self.selected_song_path,
            "selection_reason": self.selection_reason or "selected from the GUI",
            "active_channel_count": active_channel_count,
            "preferred_range": preferred_range,
            "preferred_fit_mode": self.fit_mode_var.get(),
            "preferred_tempo": preferred_tempo,
            "dry_run": dry_run,
            "export_only": self.export_only_var.get(),
            "allow_prompts": False,
            "reporter": lambda message: self.message_queue.put(("log", message)),
        }

        self.worker = threading.Thread(target=self._run_workflow, args=(worker_args,), daemon=True)
        self.worker.start()

    def _run_workflow(self, worker_args):
        try:
            result = engine.run_conversion_workflow(**worker_args)
        except Exception as error:
            self.message_queue.put(("error", str(error)))
            return

        self.message_queue.put(("done", result))

    def process_worker_messages(self):
        try:
            while True:
                message_type, payload = self.message_queue.get_nowait()
                if message_type == "log":
                    self.append_log(payload)
                elif message_type == "error":
                    self.set_controls_enabled(True)
                    self.append_log(f"Error: {payload}")
                    messagebox.showerror("Playback failed", payload, parent=self)
                elif message_type == "done":
                    self.set_controls_enabled(True)
                    result = payload
                    if result.get("cancelled"):
                        self.append_log("Cancelled before conversion.")
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
                        messagebox.showinfo(title, summary, parent=self)
        except queue.Empty:
            pass

        self.after(100, self.process_worker_messages)


def main():
    app = PianoPlayerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
