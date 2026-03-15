# TODO

## Implemented in software

- Project reorganized into `arduino/`, `config/`, `scripts/`, and `songs/`
- Active Arduino playback sketch uses the PCA9685 instead of direct GPIO switching
- Active exporter generates PCA9685 `channel + pwm` events instead of LED-style `pin + on/off`
- Mixed-solenoid support is enabled with per-channel actuation overrides
- Simultaneous note events now play as grouped chord updates in the Arduino sketch
- Active mapping mode is explicit `C3/D3/E3 -> channels 0/1/2`
- Channel `0` is configured as the stronger 25N solenoid
- Channels `1` and `2` are configured as 5N solenoids
- Notes outside the mapped keys are skipped
- MIDI velocity affects strike strength
- Strike, hold, and release behavior are generated for each scheduled note
- Bench sketches exist for both one-solenoid and three-solenoid testing
- Custom showcase MIDI files exist for 3-note sync and dynamic testing
- Metadata records the config snapshot, channel mapping, and scheduled note information for each export

## Current hardware assumptions

- Arduino board: Arduino Uno
- PWM controller: PCA9685 over I2C on Uno pins `A4/A5`
- Driver stage: 4-channel MOSFET driver board
- Solenoid power: external 12V high-current supply through the MOSFET board
- Flyback protection: manual diode per solenoid
- Common ground: shared across Arduino, PCA9685, MOSFET driver, and supply
- Active three-key layout:
  - Channel `0` -> `C3` -> 25N solenoid
  - Channel `1` -> `D3` -> 5N solenoid
  - Channel `2` -> `E3` -> 5N solenoid

## Bench tuning still needed

- Verify safe PWM frequency on the real 25N and 5N solenoids
- Tune channel `0` strike and hold values for the 25N actuator
- Tune channels `1` and `2` separately if the two 5N solenoids do not behave identically
- Tune release timing for clean repeated strikes
- Test short staccato notes versus sustained notes
- Confirm chord timing feels synchronized enough on the real mechanism

## Hardware validation still needed

- Confirm flyback diode polarity on every solenoid
- Confirm the PCA9685 output is only driving the MOSFET control side, not the solenoid power directly
- Check whether the MOSFET board input side behaves cleanly at the chosen PWM frequency
- Verify the supply can handle simultaneous channel hits without noticeable sag

## Future software expansion

- Add more mapped keys in `config/piano_config.json`
- Add more per-channel tuning fields if different key weights need them
- Add export profile names to generated filenames
- Add a calibration workflow once more than three solenoids are installed
