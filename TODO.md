# Option B Completion Status

This file now tracks the completed Option B serial-runtime workflow rather than a future plan.

## Final target workflow

The finished user flow is:

1. Download a MIDI file into Windows Downloads
2. Run one Python entry point
3. Let Python pick the newest MIDI automatically
4. Answer simple prompts such as playable range, fit mode, or tempo
5. Watch Python convert and send the song over USB
6. Hear the piano play without reflashing firmware for each song

## Non-negotiable requirement

The final system must not require end users to edit code for normal operation.

That is now satisfied by the normal workflow:

- users do not edit `.ino` files
- users do not edit `.py` files
- users do not edit generated `.h` files
- users do not manually move generated files
- users do not manually change Arduino includes or active song names

Normal operation happens through:

- downloading a MIDI
- running `play_piano.bat` or `python scripts/play_piano.py`
- answering prompts
- optionally using user-safe config values in `config/user_preferences.json`

## Current source of truth

- Playback entry point:
  - `scripts/play_piano.py`
- Conversion engine:
  - `scripts/convert_midi.py`
- Calibration/debug entry point:
  - `scripts/piano_tools.py`
- Double-click launchers:
  - `play_piano.bat`
  - `calibrate_piano.bat`
- Arduino runtime:
  - `arduino/MusicBotOfficial/MusicBotOfficial.ino`
- Engineering config:
  - `config/piano_config.json`
- User-safe playback defaults:
  - `config/user_preferences.json`
- Saved calibrated mapping:
  - `config/calibrated_mapping.json`

## Completed phases

### Phase 0: Separate one-time setup from daily use

- [x] Defined one-time setup steps
- [x] Defined daily playback workflow separately from setup
- [x] Added dedicated setup and daily-use docs:
  - `docs/SETUP.md`
  - `docs/PLAY_A_SONG.md`
- [x] Added double-click entry points:
  - `play_piano.bat`
  - `calibrate_piano.bat`

### Phase 1: Lock down the fixed Arduino runtime

- [x] Kept one stable Arduino runtime sketch in the repo
- [x] Made the runtime independent from compile-time song selection
- [x] Defined the runtime responsibilities:
  - initialize PCA9685
  - receive song packets over serial
  - buffer events
  - start playback
  - stop playback
  - report runtime status back to Python
- [x] Added calibration/debug commands:
  - `FIRE`
  - `ALL_OFF`
  - `STATUS`

### Phase 2: Define the serial song protocol

- [x] Chose a line-based text protocol
- [x] Defined message types:
  - handshake
  - clear
  - begin
  - event packet
  - commit
  - playback begin
  - playback stop
  - runtime status
  - calibration fire
- [x] Included required event data:
  - delta time
  - channel
  - PWM value
- [x] Added chunked transfer support
- [x] Removed the old whole-song event ceiling by streaming into a ring buffer
- [x] Documented the protocol in `docs/SERIAL_PROTOCOL.md`

### Phase 3: Build the Python sender

- [x] Added `pyserial` to dependencies
- [x] Built a serial sender that:
  - opens the COM port
  - handshakes with the Arduino
  - streams events in chunks
  - starts playback
- [x] Auto-detects the Arduino by default
- [x] Prompts if multiple COM ports are present
- [x] Prints clear terminal output for:
  - chosen MIDI
  - selection reason
  - mapped notes
  - skipped notes
  - port used
  - successful transfer
- [x] Made Python the normal operator entry point through `scripts/play_piano.py`

### Phase 4: Keep the converter as the event engine

- [x] Reused the existing converter scheduling logic
- [x] Kept header export mode
- [x] Kept serial streaming mode
- [x] Kept `.json` metadata generation
- [x] Added a manifest of the most recent streamed song

### Phase 5: Reduce the user flow to one command

- [x] Defaults to the newest MIDI in `C:\Users\derek\Downloads`
- [x] Accepts both `.mid` and `.midi`
- [x] Validates that a selected file is readable as MIDI
- [x] Imports external MIDI files into the project library automatically
- [x] Converts the MIDI
- [x] Sends it to the Arduino
- [x] Starts playback
- [x] Supports optional overrides for:
  - explicit project song
  - explicit filepath
  - tempo override
  - playable range override
  - dry run
  - export-only mode
  - explicit COM port
- [x] Uses plain-language prompts

### Phase 6: Handle beginner-proof edge cases

- [x] Handles no MIDI in Downloads with a fallback path and message
- [x] Handles invalid/corrupted MIDI files with a friendly error
- [x] Reports unsupported-note impact with:
  - playable percentage
  - recognizability estimate
  - top skipped notes
- [x] Treats percussion intentionally:
  - ignores MIDI channel 10 by default
  - warns when a file appears percussion-heavy
- [x] Handles ZIP-download confusion with a clear message
- [x] Shows which file was chosen and why
- [x] Confirms Arduino availability through serial detection and handshake

### Phase 6.5: Add calibration and mapping debug tools

- [x] Added a calibration/debug mode that can fire one channel on command
- [x] Added a sweep mode
- [x] Saves a clear mapping report after calibration
- [x] Added a user-safe way to choose a contiguous active range
- [x] Saves calibrated mappings into configuration
- [x] Supports octave transposition during playback
- [x] Added a simple per-channel strike/hold tuning test

### Phase 7: Preserve a fallback path

- [x] Kept `current_song.h` generation working
- [x] Kept Arduino IDE sync support working
- [x] Kept manual runtime upload available as a fallback
- [x] Removed the need for normal users to touch fallback internals

### Phase 8: Externalize all routine user choices

- [x] Moved routine song selection into Python inputs
- [x] Moved routine playback options into prompts and command-line arguments
- [x] Separated engineering tuning from user-facing defaults:
  - engineering config in `config/piano_config.json`
  - user-safe defaults in `config/user_preferences.json`
- [x] Documented user-safe settings in the README and setup/daily-use docs
- [x] Ensured the normal workflow does not require opening source files
- [x] Kept the default mode beginner-safe

## What is operational now

### One-time setup

- install Python dependencies
- install the Adafruit PCA9685 Arduino library
- upload `arduino/MusicBotOfficial/MusicBotOfficial.ino` once
- verify hardware wiring once

### Daily playback

- run `play_piano.bat`

or

- run `python scripts/play_piano.py`

### Calibration

- run `calibrate_piano.bat`

or

- run `python scripts/piano_tools.py`

## Remaining operational caveats

These are not open implementation tasks. They are real-world hardware limits and tuning realities:

- the Arduino Uno still has limited RAM and timing headroom compared with a larger board
- a contiguous bottom-note to top-note range only works if every note in that span is actually wired
- calibration still depends on a person confirming which physical key moved
- downloaded songs can still sound simplified if large parts of the MIDI sit outside the installed note range
- solenoid force tuning is still a hardware/bench process even though the software tools are now in place

## Definition of done

Option B is complete for this repo because a user can now:

1. download a MIDI into Windows Downloads
2. run one Python command or double-click `play_piano.bat`
3. let Python automatically find the newest MIDI
4. answer simple prompts
5. watch Python convert and send the song over USB
6. hear the piano play

without reopening Arduino IDE or re-uploading firmware for each song
