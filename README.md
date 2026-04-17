# Autonomous Piano Player

This project plays MIDI files on a piano using an Arduino Uno, a PCA9685 PWM driver, and solenoid actuators.

The current software flow is:

1. Upload the fixed Arduino runtime once
2. Run the Python playback tool on a MIDI file
3. Python scans the MIDI, asks a few prompts, converts it into timed PWM events, and sends those events over USB serial
4. The Arduino receives the event stream and drives the solenoids through the PCA9685

For normal playback, users should not need to edit Arduino code for each song.

## Current project status

The repo currently targets a 3-note test setup:

- PCA9685 channel `0` -> `C3` -> 25N solenoid
- PCA9685 channel `1` -> `D3` -> 5N solenoid
- PCA9685 channel `2` -> `E3` -> 5N solenoid
- notes outside `C3/D3/E3` are skipped unless octave transposition helps them fit

Important current limitation:

- the Arduino runtime now uses a `48`-event ring buffer and chunked USB streaming
- playback is no longer limited by a single whole-song event ceiling, but extremely dense songs can still be limited by USB timing and Uno RAM constraints

## How it works

There are two main pieces:

- [scripts/play_piano.py](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/scripts/play_piano.py)
  - is the user-facing playback entry point
  - defaults to the newest MIDI in Windows Downloads
  - scans the MIDI note range
  - asks whether to keep pitches strict, transpose by octave, or cancel
  - converts notes into piano-style `strike`, `hold`, and `release` PWM events
  - streams the converted event list to the Arduino over USB serial
  - also writes debug/export artifacts to the repo

- [scripts/convert_midi.py](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/scripts/convert_midi.py)
  - is the conversion engine used by `play_piano.py`
  - can still be run directly for engineering/debug work

- [scripts/piano_tools.py](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/scripts/piano_tools.py)
  - is the calibration/debug entry point
  - sweeps channels
  - saves calibrated mappings
  - fires custom tuning pulses

- [arduino/MusicBotOfficial/MusicBotOfficial.ino](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/arduino/MusicBotOfficial/MusicBotOfficial.ino)
  - is the fixed playback runtime
  - receives serial commands from Python
  - buffers incoming events in a ring buffer
  - accepts calibration/debug commands
  - plays those events on the PCA9685

The active hardware and tuning configuration lives in [config/piano_config.json](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/config/piano_config.json).

## Repo layout

```text
Music bot official directory/
|-- arduino/
|   |-- MusicBotOfficial/
|   |-- SingleSolenoidBenchTest/
|   |-- ThreeSolenoidBenchTest/
|   `-- HeaderPlaybackFallback/
|-- config/
|   |-- calibrated_mapping.json
|   |-- piano_config.json
|   |-- deployment_paths.json
|   `-- user_preferences.json
|-- docs/
|   |-- CALIBRATION.md
|   |-- PLAY_A_SONG.md
|   |-- SERIAL_PROTOCOL.md
|   `-- SETUP.md
|-- scripts/
|   |-- play_piano.py
|   |-- piano_tools.py
|   |-- convert_midi.py
|   `-- legacy/
|-- songs/
|   |-- midi/
|   `-- metadata/
|-- calibrate_piano.bat
|-- play_piano.bat
|-- TODO.md
|-- requirements.txt
`-- README.md
```

## Prerequisites

Software:

- Python 3
- Arduino IDE
- Python packages from [requirements.txt](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/requirements.txt)
- Arduino library:
  - `Adafruit PWM Servo Driver Library`

Hardware:

- Arduino Uno
- PCA9685 PWM driver
- MOSFET driver stage for the solenoids
- external solenoid power supply
- one flyback diode per solenoid
- common ground between Arduino, PCA9685, MOSFET board, and power supply

## Wiring assumptions

Current code assumes:

- Arduino `A4` -> PCA9685 `SDA`
- Arduino `A5` -> PCA9685 `SCL`
- PCA9685 address `0x40`
- PCA9685 PWM frequency `250 Hz`

Important:

- the PCA9685 does not power solenoids directly
- the MOSFET stage must switch the solenoid power
- each solenoid needs flyback protection

## First-time setup

Detailed guides:

- [docs/SETUP.md](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/docs/SETUP.md)
- [docs/PLAY_A_SONG.md](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/docs/PLAY_A_SONG.md)
- [docs/CALIBRATION.md](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/docs/CALIBRATION.md)
- [docs/SERIAL_PROTOCOL.md](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/docs/SERIAL_PROTOCOL.md)

### 1. Clone the repo

Clone the GitHub repo and open it locally.

### 2. Install Python dependencies

From the repo root, run:

```bash
pip install -r requirements.txt
```

### 3. Install the Arduino library

In Arduino IDE, install:

- `Adafruit PWM Servo Driver Library`

### 4. Upload the fixed Arduino runtime once

Open this sketch in Arduino IDE:

- [arduino/MusicBotOfficial/MusicBotOfficial.ino](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/arduino/MusicBotOfficial/MusicBotOfficial.ino)

Then:

1. Plug in the Arduino by USB
2. Select `Arduino Uno`
3. Select the correct COM port
4. Click `Upload`

This only needs to be done again if the Arduino runtime changes.

### 5. Decide whether to use deployment path syncing

[config/deployment_paths.json](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/config/deployment_paths.json) now defaults to the repo-local Arduino sketch path, so it works across cloned copies without editing machine-specific user folders.

If you are just testing the repo directly, you can ignore that file.

If you want Python to mirror generated files into a separate Arduino sketchbook folder, update the `arduino_ide_sync.sketch_path` value on your machine. Absolute and repo-relative paths are both supported.

## Quick test paths

### Option A: Bench-test the actuators first

Use these sketches before trying MIDI playback if you want to validate the hardware:

- [arduino/SingleSolenoidBenchTest/SingleSolenoidBenchTest.ino](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/arduino/SingleSolenoidBenchTest/SingleSolenoidBenchTest.ino)
- [arduino/ThreeSolenoidBenchTest/ThreeSolenoidBenchTest.ino](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/arduino/ThreeSolenoidBenchTest/ThreeSolenoidBenchTest.ino)

What they are for:

- `SingleSolenoidBenchTest`: verify one solenoid moves with soft/medium/hard strikes
- `ThreeSolenoidBenchTest`: verify channels `0`, `1`, and `2` fire correctly, including a `C + E` chord

### Option B: Test full MIDI playback

Recommended first test files:

- [songs/midi/Hot Cross Buns.mid](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/songs/midi/Hot%20Cross%20Buns.mid)
- [songs/midi/CDE_Sync_Showcase.mid](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/songs/midi/CDE_Sync_Showcase.mid)
- [songs/midi/CDE_Dynamics_Etude.mid](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/songs/midi/CDE_Dynamics_Etude.mid)

`Hot Cross Buns.mid` is the safest first musical test because it already fits the current `C3/D3/E3` mapping very well.

## Daily playback workflow

After the Arduino runtime has been uploaded once, normal testing looks like this:

1. Plug the Arduino into USB
2. Power the solenoids
3. Put a MIDI file in your Windows Downloads folder, or use one already in [songs/midi](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/songs/midi)
4. From the repo root, run:

```bash
python scripts/play_piano.py
```

Or double-click:

- [play_piano.bat](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/play_piano.bat)

5. Answer the prompts
6. Python sends the song to the Arduino
7. The Arduino plays it

## What the Python prompts mean

### Song selection

The playback tool defaults to the newest `.mid` or `.midi` file in your Windows Downloads folder.

Optional overrides:

- `--project-song "Hot Cross Buns.mid"`
- `--choose-library`
- `--song "C:\path\to\file.mid"`

### Playable range override

The script can keep the saved note mapping, or let you temporarily enter a contiguous playable range such as:

- `C4-B4`
- `60-71`

Use that only if your current physical solenoids cover every note in that span.

If your solenoids are mapped to specific scattered notes, keep the saved mapping instead.

### MIDI range and fit mode

Before conversion, the script scans the MIDI and reports:

- detected MIDI note range
- strict playability
- transpose-by-octave playability

Coverage is shown like this:

- `23 of 25 note events playable (92.0%)`

Then it asks you to choose:

- `strict`
  - keep original pitches
  - skip notes outside the current playable layout
- `transpose`
  - keep already-playable notes where they are
  - fold each out-of-range note into the nearest playable octave when that note exists in the current layout
  - skip folded notes that would otherwise disturb on-time playback
  - still skip any notes that remain out of range
- `cancel`
  - stop without converting or sending anything

Percussion on MIDI channel 10 is ignored during this scan.

### Tempo override

You can:

- press Enter to keep the original timing
- enter a BPM value such as `140`
- enter a multiplier such as `0.85x`

## What gets generated

Even though playback now uses serial, the script still writes export/debug files:

- versioned headers in [arduino/MusicBotOfficial/generated](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/arduino/MusicBotOfficial/generated)
- active header in [arduino/MusicBotOfficial/generated/current_song.h](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/arduino/MusicBotOfficial/generated/current_song.h)
- versioned metadata JSON in [songs/metadata](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/songs/metadata)
- active metadata in [songs/metadata/current_song.json](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/songs/metadata/current_song.json)

The JSON metadata is useful for debugging because it records:

- the source MIDI
- the selected fit mode
- the effective note mapping
- the generated event list
- per-note scheduling details

## Current configuration

Engineering settings live in [config/piano_config.json](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/config/piano_config.json).

User-safe playback defaults live in [config/user_preferences.json](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/config/user_preferences.json).

If a calibration has been saved, it lives in [config/calibrated_mapping.json](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/config/calibrated_mapping.json) and is loaded automatically.

Right now it defines:

- `project_mode: three_solenoid_cde_test`
- PCA9685 address `0x40`
- PWM frequency `250`
- note mapping:
  - `48 (C3) -> channel 0`
  - `50 (D3) -> channel 1`
  - `52 (E3) -> channel 2`
- stronger strike/hold tuning on channel `0` for the 25N solenoid

## Troubleshooting

### Python says no serial devices were found

- make sure the Arduino is plugged in by USB
- make sure the board is powered and recognized by the computer
- close the Arduino Serial Monitor if it is open

### Python asks you to choose a COM port

That means multiple serial devices were detected. Pick the port that belongs to the Arduino Uno.

### The song converts but nothing moves

Check:

- Arduino runtime was uploaded successfully
- Arduino and Python are using the same board over USB
- PCA9685 wiring on `A4/A5`
- MOSFET board wiring
- common ground
- external solenoid power supply
- flyback diode polarity

### The bench test works but a downloaded MIDI sounds incomplete

That is expected if:

- the MIDI uses notes outside the mapped range
- the fit mode skips many notes
- the file is too dense for the current serial streaming and hardware timing

### The converter reports permission problems syncing Arduino IDE files

That usually means `deployment_paths.json` points to a path that only exists on another machine, or a local Arduino sketch file is currently locked.

This does not matter for serial playback if you already uploaded the runtime from the repo directly.

## Known limitations

- current default note mapping is only `C3/D3/E3`
- a contiguous bottom-note/top-note range only works if every note in that span is actually wired
- calibration still depends on a human confirming which physical key moved
- the Uno still has tight RAM and timing constraints compared with a larger microcontroller

## Recommended first test for engineering partners

If you are opening this project for the first time, use this order:

1. Upload [arduino/SingleSolenoidBenchTest/SingleSolenoidBenchTest.ino](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/arduino/SingleSolenoidBenchTest/SingleSolenoidBenchTest.ino) if you want to verify one actuator
2. Upload [arduino/ThreeSolenoidBenchTest/ThreeSolenoidBenchTest.ino](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/arduino/ThreeSolenoidBenchTest/ThreeSolenoidBenchTest.ino) if you want to verify the 3-channel hardware
3. Upload [arduino/MusicBotOfficial/MusicBotOfficial.ino](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/arduino/MusicBotOfficial/MusicBotOfficial.ino) once as the fixed runtime
4. Run:

```bash
python scripts/play_piano.py --project-song "Hot Cross Buns.mid"
```

5. Keep the saved mapping
6. Choose `strict`
7. Keep the original tempo

That is the most reliable end-to-end test currently in the repo.
