"""Tkinter launcher for user-friendly piano playback.

Run this from an IDE or by double-clicking the batch file. It wraps the normal
conversion/playback engine with a small desktop UI so the user can choose a
song, tempo, and current hardware note range without answering terminal prompts.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import convert_midi as engine


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

        self.song_name_var = tk.StringVar(value="No song selected")
        self.song_reason_var = tk.StringVar(value="")
        self.song_info_var = tk.StringVar(value="No MIDI selected yet.")
        self.active_channels_var = tk.StringVar(
            value=str(len(engine.get_mapping_channel_order(self.config_data["mapping"])))
        )
        self.tempo_var = tk.StringVar(value="")
        self.range_var = tk.StringVar(value="")
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
            text="How many hardware channels are active right now. Increase or decrease this as you add or remove keys.",
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
            text="Leave blank to use the saved note mapping. Or enter a contiguous range like C3-B3 or 48-59.",
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

    def start_run(self, dry_run):
        if self.worker is not None and self.worker.is_alive():
            messagebox.showinfo("Already running", "Wait for the current playback job to finish first.", parent=self)
            return

        if self.selected_song_path is None:
            messagebox.showinfo("Choose a song", "Pick a MIDI file first.", parent=self)
            return

        active_channel_count = self.active_channels_var.get().strip()
        try:
            active_channel_count = engine.parse_active_channel_count(
                active_channel_count,
                self.config_data["pca9685"],
            )
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
