# Autonomous Piano Player

This project converts MIDI songs into PCA9685-driven solenoid playback data for an autonomous piano player.

The repo now supports two practical test modes:

- `SingleSolenoidBenchTest`: one 5N solenoid on PCA9685 channel `0`
- `three_solenoid_cde_test`: three mapped piano notes using channels `0`, `1`, and `2`

Current three-solenoid mapping:

- Channel `0`: `C3` on the 25N solenoid
- Channel `1`: `D3` on a 5N solenoid
- Channel `2`: `E3` on a 5N solenoid
- Notes outside `C3/D3/E3` are skipped by the converter

## Project layout

```text
Music bot official directory/
|-- arduino/
|   |-- MusicBotOfficial/
|   |-- SingleSolenoidBenchTest/
|   `-- ThreeSolenoidBenchTest/
|-- config/
|   `-- piano_config.json
|-- scripts/
|   |-- convert_midi.py
|   `-- legacy/
|-- songs/
|   |-- midi/
|   `-- metadata/
|-- TODO.md
|-- requirements.txt
`-- README.md
```

## Supported workflow

- `scripts/convert_midi.py` is the active exporter.
- `config/piano_config.json` controls PCA9685 settings, note mapping, and per-channel strike/hold tuning.
- `arduino/MusicBotOfficial/MusicBotOfficial.ino` is the full playback sketch.
- `arduino/MusicBotOfficial/generated/current_song.h` is the active generated playback file.

Each exported note becomes a piano-style actuation pattern:

- `strike`: a short stronger pulse
- `hold`: a lower sustained PWM level for longer notes
- `release`: PWM back to `0`

MIDI velocity affects strike strength, and simultaneous notes are emitted as same-timestamp events so chords like `C + E` play together.

## Quick start

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Confirm the Arduino IDE has the Adafruit PCA9685 library installed:

   - `Adafruit PWM Servo Driver Library`

3. Put MIDI files in `songs/midi/`.

4. Run the converter from the repository root:

   ```bash
   python scripts/convert_midi.py
   ```

5. Follow the prompts:

   - optionally keep the saved key mapping or enter a contiguous playable range like `C4-B4` or `60-71`
   - review the detected MIDI note range
   - choose:
     - `strict`: keep original pitches and skip out-of-range notes
     - `transpose`: shift the whole song by octaves to fit more notes, then skip the rest
     - `cancel`: stop without converting
   - optionally choose a tempo override

6. Open `arduino/MusicBotOfficial/MusicBotOfficial.ino` in the Arduino IDE and upload it.

## Bench tests

### One-solenoid bench test

Upload:

- `arduino/SingleSolenoidBenchTest/SingleSolenoidBenchTest.ino`

Use this first to validate a single 5N solenoid on channel `0`.

### Three-solenoid sync bench test

Upload:

- `arduino/ThreeSolenoidBenchTest/ThreeSolenoidBenchTest.ino`

This sketch tests:

- single-note strikes on `C`, `D`, and `E`
- mixed actuator strengths across the 25N and 5N solenoids
- a simultaneous `C + E` chord
- repeated dynamics and short phrase playback

## Sample MIDI files

These are good first tests for the current `C3/D3/E3` mapping:

- `Hot Cross Buns.mid`
- `CDE_Sync_Showcase.mid`
- `CDE_Dynamics_Etude.mid`

`Hot Cross Buns.mid` is the cleanest real-song fit because it already uses just `C3`, `D3`, and `E3`.

The two custom showcase MIDIs demonstrate:

- velocity changes
- repeated notes
- `C + E` chord hits
- more dramatic rhythmic phrasing than the nursery-rhyme samples

## Generated outputs

The converter writes:

- a versioned header in `arduino/MusicBotOfficial/generated/`
- a stable active header at `arduino/MusicBotOfficial/generated/current_song.h`
- matching metadata JSON in `songs/metadata/`

The metadata includes:

- generated PWM events
- scheduled strike/hold/release notes
- the config snapshot used for that export
- note-to-channel mapping and actuation details

## Range fitting

Before conversion, the Python tool scans the MIDI and reports:

- the detected pitched-note range of the file
- how many note events are playable with the current layout
- the same playability count as a percentage of the total

The coverage is shown in the form:

- `X of Y note events playable (Z%)`

If your physical keys cover one continuous span, you can override the playable range directly in the prompt with:

- note names, like `C4-B4`
- MIDI note numbers, like `60-71`

This contiguous range override assumes every note in that span is wired. If your layout skips keys, keep the saved explicit mapping instead.

## Hardware notes

- The PCA9685 is only generating control PWM. It is not powering the solenoids directly.
- The MOSFET stage must handle the solenoid power.
- Flyback protection is required for each solenoid because the MOSFET board does not include it.
- Arduino ground, PCA9685 ground, MOSFET board ground, and supply ground must all be common.
- Channel `0` currently assumes the stronger 25N actuator and uses a stronger starting PWM profile than channels `1` and `2`.

## Expansion path

- Add more notes by editing `config/piano_config.json`
- Add more solenoids and assign each to a piano key
- Retune strike/hold values per channel
- Add more showcase MIDIs or export your own songs that fit the mapped notes
