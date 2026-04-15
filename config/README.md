# Config Files

JSON does not support real comments, so this folder uses a README instead of putting `//` comments inside the config files.

## `piano_config.json`

Main hardware configuration for the autonomous piano player.

- `project_mode` names the current hardware setup.
- `pca9685` stores the PWM board I2C address and frequency.
- `mapping` tells Python which MIDI notes route to which PCA9685 channels.
- `actuation` controls strike PWM, hold PWM, release timing, and retrigger timing.
- `notes` stores human-readable engineering notes about the current setup.

## `calibrated_mapping.json`

Machine-specific calibration output created by `scripts\piano_tools.py`.

If this file exists, Python uses it instead of the default mapping in `piano_config.json`. This lets each physical piano build have its own wiring map without changing the repo default.

This file is local hardware state, so only commit it if the team intentionally wants to share that exact wiring layout.

## `deployment_paths.json`

Optional local deployment settings.

This can point Python at an Arduino IDE sketch folder for syncing generated files, and it stores serial settings such as baud rate and preferred COM port behavior.

## `user_preferences.json`

User workflow defaults.

This controls convenience behavior such as whether Python should auto-select the newest downloaded MIDI, whether it should prompt for fit mode, and whether playback should wait for the Arduino to finish.
