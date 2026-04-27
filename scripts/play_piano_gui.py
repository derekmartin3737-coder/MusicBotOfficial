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
            text="Sweep channels only",
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

        button_row = ttk.Frame(outer, style="App.TFrame")
        button_row.grid(row=4, column=0, sticky="e", pady=(14, 0))
        ttk.Button(button_row, text="Cancel", style="Secondary.TButton", command=self.cancel).grid(row=0, column=0)
        ttk.Button(button_row, text="Run", style="Primary.TButton", command=self.accept).grid(row=0, column=1, padx=(8, 0))

    def accept(self):
        self.result = self.key_color_var.get()
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


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
        self.active_channels_var = tk.StringVar(value=str(default_active_channels))
        self.tempo_var = tk.StringVar(value="")
        self.range_var = tk.StringVar(value=str(default_playable_range))
        self.fit_mode_var = tk.StringVar(value=default_fit_mode)
        self.export_only_var = tk.BooleanVar(value=False)

        self._build_layout()
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

        if self._widget_is_descendant(widget, self.log_text):
            self.log_text.yview_scroll(delta, "units")
            return "break"

        if self._widget_is_descendant(widget, self.page_content):
            self.page_canvas.yview_scroll(delta, "units")
            return "break"

        return None

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
        outer.rowconfigure(4, weight=4, minsize=320)
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
        ttk.Label(info_body, textvariable=self.song_name_var, style="Value.Panel.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(2, 4)
        )
        ttk.Label(info_body, textvariable=self.song_reason_var, style="Status.Panel.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        ttk.Label(info_body, textvariable=self.song_info_var, wraplength=900, style="Muted.Panel.TLabel").grid(
            row=3, column=0, columnspan=2, sticky="w"
        )

        options_frame = ttk.LabelFrame(outer, text="Controls", style="Section.TLabelframe")
        options_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        options_body = self._create_section_body(options_frame)
        options_body.columnconfigure(1, weight=1)

        ttk.Label(options_body, text="Installed solenoids", style="Panel.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(options_body, textvariable=self.active_channels_var, style="Panel.TEntry").grid(
            row=0, column=1, sticky="ew", padx=(16, 0), pady=(0, 4)
        )
        ttk.Label(
            options_body,
            text="How many hardware channels are active right now. The current bench default is 61.",
            style="Muted.Panel.TLabel",
            wraplength=620,
        ).grid(row=1, column=1, sticky="w", padx=(16, 0), pady=(0, 12))

        ttk.Label(options_body, text="Tempo override", style="Panel.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(options_body, textvariable=self.tempo_var, style="Panel.TEntry").grid(
            row=2, column=1, sticky="ew", padx=(16, 0), pady=(0, 4)
        )
        ttk.Label(
            options_body,
            text="Leave blank for the original timing. You can enter 140, 0.85x, or 92bpm.",
            style="Muted.Panel.TLabel",
        ).grid(row=3, column=1, sticky="w", padx=(16, 0), pady=(0, 12))

        ttk.Label(options_body, text="Available note range", style="Panel.TLabel").grid(row=4, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(options_body, textvariable=self.range_var, style="Panel.TEntry").grid(
            row=4, column=1, sticky="ew", padx=(16, 0), pady=(0, 4)
        )
        ttk.Label(
            options_body,
            text=(
                "Leave blank to use the saved note mapping. "
                "For calibration and for your current 61-solenoid bench, blank is the correct default "
                "unless you intentionally want a temporary contiguous override."
            ),
            style="Muted.Panel.TLabel",
            wraplength=620,
        ).grid(row=5, column=1, sticky="w", padx=(16, 0), pady=(0, 12))

        ttk.Label(options_body, text="Out-of-range notes", style="Panel.TLabel").grid(row=6, column=0, sticky="w", pady=(0, 4))
        fit_mode_box = ttk.Combobox(
            options_body,
            state="readonly",
            values=("transpose", "strict"),
            textvariable=self.fit_mode_var,
            style="Panel.TCombobox",
        )
        fit_mode_box.grid(row=6, column=1, sticky="w", padx=(16, 0), pady=(0, 12))
        ttk.Checkbutton(
            options_body,
            text="Export only (prepare files but do not send to Arduino)",
            variable=self.export_only_var,
            style="Panel.TCheckbutton",
        ).grid(row=7, column=1, sticky="w", padx=(16, 0))

        run_frame = ttk.LabelFrame(outer, text="Run Options", style="Section.TLabelframe")
        run_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        run_body = self._create_section_body(run_frame)
        run_body.columnconfigure(0, weight=1)
        run_body.columnconfigure(1, weight=1)
        ttk.Label(
            run_body,
            text="Start with a dry check if you want to inspect the plan before sending anything to the Arduino.",
            style="Muted.Panel.TLabel",
            wraplength=860,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        ttk.Button(run_body, text="Run Dry Check", style="Secondary.TButton", command=lambda: self.start_run(dry_run=True)).grid(
            row=1, column=0, sticky="ew"
        )
        ttk.Button(run_body, text="Play / Send to Arduino", style="Primary.TButton", command=lambda: self.start_run(dry_run=False)).grid(
            row=1, column=1, sticky="ew", padx=(12, 0)
        )

        song_selection_frame = ttk.LabelFrame(outer, text="Song Selection", style="Section.TLabelframe")
        song_selection_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
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
            command=lambda: self.refresh_song_catalog_async(use_suggested=False),
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

        debug_frame = ttk.LabelFrame(outer, text="Debugging", style="Section.TLabelframe")
        debug_frame.grid(row=5, column=0, sticky="nsew", pady=(0, 0))
        debug_body = self._create_section_body(debug_frame)
        debug_body.columnconfigure(0, weight=1)
        debug_body.rowconfigure(2, weight=1, minsize=140)

        ttk.Label(
            debug_body,
            text="Use these tools when you are calibrating, validating, or diagnosing the bench.",
            style="Muted.Panel.TLabel",
            wraplength=860,
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        debug_button_row = ttk.Frame(debug_body, style="Panel.TFrame")
        debug_button_row.grid(row=1, column=0, sticky="w", pady=(0, 10))
        ttk.Button(
            debug_button_row,
            text="Calibrate Note Mapping...",
            style="Secondary.TButton",
            command=self.start_note_mapping_calibration,
        ).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(
            debug_button_row,
            text="Troubleshoot Keys...",
            style="Secondary.TButton",
            command=self.start_troubleshooting_run,
        ).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )

        log_frame = ttk.LabelFrame(debug_body, text="Status", style="Section.TLabelframe")
        log_frame.grid(row=2, column=0, sticky="nsew")
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

    def _set_child_state_recursive(self, widget, state):
        try:
            if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton)):
                widget.configure(state=state if not isinstance(widget, ttk.Combobox) else ("readonly" if state == "normal" else "disabled"))
            elif isinstance(widget, tk.Listbox):
                widget.configure(state=state)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_child_state_recursive(child, state)

    def append_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

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

        self.song_catalog_status_var.set(status)

    def apply_song_catalog(self, catalog, use_suggested=False):
        self.song_catalog = catalog

        if use_suggested and not self.song_selection_is_manual:
            suggested_path = self.song_catalog.get("suggested_path")
            suggested_reason = self.song_catalog.get("suggested_reason")
            if suggested_path is not None:
                self.set_selected_song(suggested_path, suggested_reason, manual=False)

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
        return self.song_catalog.get("entries", [])

    def refresh_song_catalog(self, use_suggested=False, recursive_downloads=True):
        catalog = engine.build_song_catalog(
            self.user_preferences,
            recursive_downloads=recursive_downloads,
        )
        return self.apply_song_catalog(catalog, use_suggested=use_suggested)

    def refresh_song_catalog_async(self, use_suggested=False):
        if self.song_catalog_refresh_in_progress:
            return

        self.song_catalog_refresh_in_progress = True
        self.update_song_catalog_status()
        worker = threading.Thread(
            target=self._refresh_song_catalog_worker,
            args=(use_suggested,),
            daemon=True,
        )
        worker.start()

    def _refresh_song_catalog_worker(self, use_suggested):
        try:
            catalog = engine.build_song_catalog(
                self.user_preferences,
                recursive_downloads=True,
            )
        except Exception as error:
            self.message_queue.put(("song_catalog_error", str(error)))
            return

        self.message_queue.put(("song_catalog", {"catalog": catalog, "use_suggested": use_suggested}))

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

    def build_patch_mapping_config(self, active_channel_count):
        config = engine.load_config()
        return piano_tools.build_patch_mapping_config(config, active_channel_count)

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
            time.sleep(piano_tools.CALIBRATION_INTER_FIRE_DELAY_SECONDS)

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

    def patch_manual_mapping_gui(self, connection, config, port, ready_info, patch_channels):
        existing_mapping = dict(config["mapping"])
        note_to_channel = dict(existing_mapping.get("note_to_channel", {}))
        note_labels = dict(existing_mapping.get("note_labels", {}))
        channel_labels = dict(existing_mapping.get("channel_labels", {}))
        channel_sequence = [int(channel) for channel in existing_mapping.get("channel_sequence", [])]
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
            actuation = engine.resolve_channel_actuation(channel, config)
            pulse = piano_tools.build_calibration_pulse(actuation)
            label = channel_labels.get(str(channel), f"Channel {channel}")
            channel_target = engine.describe_global_channel(channel, config["pca9685"])
            self.append_log(f"Firing {channel_target}: {label}")
            piano_tools.fire_channel(connection, channel, pulse)
            self.update()
            time.sleep(piano_tools.CALIBRATION_INTER_FIRE_DELAY_SECONDS)

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
            messagebox.showinfo("Already running", "Wait for the current playback job to finish first.", parent=self)
            return

        if self.selected_song_path is None:
            messagebox.showinfo("Choose a song", "Pick a MIDI file first.", parent=self)
            return

        run_options = self.collect_run_options(base_tempo_bpm=120.0)
        if run_options is None:
            return

        self.append_log("")
        self.append_log(f"Starting {'dry run' if dry_run else 'playback'} for {self.selected_song_path.name}...")
        self.set_controls_enabled(False)

        worker_args = {
            "workflow_kind": "conversion",
            "selected_midi_source": self.selected_song_path,
            "selection_reason": self.selection_reason or "selected from the GUI",
            "active_channel_count": run_options["active_channel_count"],
            "preferred_range": run_options["preferred_range"],
            "preferred_fit_mode": self.fit_mode_var.get(),
            "preferred_tempo": run_options["preferred_tempo"],
            "dry_run": dry_run,
            "export_only": run_options["export_only"],
            "allow_prompts": False,
            "reporter": lambda message: self.message_queue.put(("log", message)),
        }

        self.worker = threading.Thread(target=self._run_workflow, args=(worker_args,), daemon=True)
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
            "export_only": self.export_only_var.get(),
        }

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

        key_label = dialog.result.title()
        self.append_log("")
        self.append_log(f"Starting {key_label.lower()} key troubleshooting...")
        self.set_controls_enabled(False)

        worker_args = {
            "workflow_kind": "troubleshooting",
            "key_color": dialog.result,
            "active_channel_count": run_options["active_channel_count"],
            "preferred_range": run_options["preferred_range"],
            "preferred_tempo": run_options["preferred_tempo"],
            "dry_run": False,
            "export_only": run_options["export_only"],
            "allow_prompts": False,
            "reporter": lambda message: self.message_queue.put(("log", message)),
        }

        self.worker = threading.Thread(target=self._run_workflow, args=(worker_args,), daemon=True)
        self.worker.start()

    def _run_workflow(self, worker_args):
        try:
            workflow_kind = worker_args.pop("workflow_kind", "conversion")
            if workflow_kind == "troubleshooting":
                result = engine.run_troubleshooting_workflow(**worker_args)
            else:
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
                elif message_type == "song_catalog":
                    self.song_catalog_refresh_in_progress = False
                    self.apply_song_catalog(payload["catalog"], use_suggested=payload.get("use_suggested", False))
                elif message_type == "song_catalog_error":
                    self.song_catalog_refresh_in_progress = False
                    self.update_song_catalog_status()
                    self.append_log(f"Song catalog refresh error: {payload}")
                elif message_type == "error":
                    self.set_controls_enabled(True)
                    self.append_log(f"Error: {payload}")
                    messagebox.showerror("Run failed", payload, parent=self)
                elif message_type == "done":
                    self.set_controls_enabled(True)
                    result = payload
                    if result.get("cancelled"):
                        self.append_log("Cancelled before conversion.")
                    else:
                        if result["workflow_kind"] == "troubleshooting":
                            if result["payload"] is None:
                                title = "Troubleshooting dry run complete"
                            elif result["stream_manifest"] is None:
                                title = "Troubleshooting export complete"
                            else:
                                title = "Troubleshooting complete"
                            key_label = result["metadata"].get("diagnostic_key_color", "selected").title()
                            summary = (
                                f"Finished {key_label.lower()} key troubleshooting\n"
                                f"Active hardware channels: {result['metadata']['active_hardware_channel_count']}\n"
                                f"Steps: {result['metadata'].get('diagnostic_step_count', 0)}\n"
                                f"Effective tempo: {result['tempo_override']['target_bpm']:.2f} BPM"
                            )
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
