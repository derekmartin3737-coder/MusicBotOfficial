# Calibration

Use the calibration tools when you need to confirm which PCA9685 channel moves which piano key.

Run:

```bash
python scripts/piano_tools.py
```

Or from the normal launcher:

```bash
python scripts/play_piano.py --calibrate
```

Or double-click:

- [calibrate_piano.bat](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/calibrate_piano.bat)

If you launch [play_piano.bat](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/play_piano.bat) or `python scripts/play_piano.py` without arguments, the GUI now includes a `Calibrate Note Mapping...` button so playback and mapping setup live under one entry point.

## Available actions

### 1. Sweep the configured channels

Fires each configured channel once so you can see the physical order on the piano.

### 2. Save a contiguous octave map

Use this when the currently installed solenoids cover one continuous span of notes.

The tool will:

1. sweep the channels
2. ask for the bottom note, such as `C4`
3. assign the channels upward from there
4. save the mapping

### 3. Save a manual channel-to-note map

Use this when the installed keys are not contiguous.
This is the right mode for layouts like white keys in one octave plus full
chromatic notes in others.

The tool will:

1. fire one channel
2. ask which piano note moved
3. repeat for each configured channel
4. save the mapping

### 4. Tune one channel

Lets you try a custom strike/hold pulse on one channel without editing code.

## Saved outputs

The calibration tools write:

- [config/calibrated_mapping.json](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/config/calibrated_mapping.json)
- [songs/metadata/calibration_report.json](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/songs/metadata/calibration_report.json)
- [songs/metadata/calibration_report.txt](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/songs/metadata/calibration_report.txt)

When `calibrated_mapping.json` exists, the playback tool automatically uses it.

If calibration reports an I2C warning, stop and fix the PCA9685 board
addresses first. Multiple boards must use unique addresses such as `0x40`,
`0x41`, `0x42`, and `0x43`.
