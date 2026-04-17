# Coworker Run Commands

This guide is for teammates who clone the GitHub repo and want to run or test the autonomous piano player from a Windows computer.

## 1. Clone The Repo

```powershell
git clone https://github.com/derekmartin3737-coder/MusicBotOfficial.git
```

## 2. Change Into The Project Folder

```powershell
cd MusicBotOfficial
```

## 3. Install Python Requirements

```powershell
python -m pip install -r requirements.txt
```

Optional but recommended if you want an isolated Python environment:

```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
python -m pip install -r requirements.txt
```

## 4. Upload The Arduino Runtime

Open this exact file in the Arduino IDE:

```text
arduino\MusicBotOfficial\MusicBotOfficial.ino
```

Then upload it to the Arduino Uno from the Arduino IDE.

After upload finishes, close the Arduino IDE before running Python. The Arduino IDE can keep the COM port locked, which prevents Python from connecting.

## 5. Find The Arduino COM Port

Run:

```powershell
python scripts\play_piano.py --list-ports
```

Look for the Arduino Uno port, usually something like `COM3`, `COM7`, or similar. Use that value anywhere this guide says `<COM_PORT>`.

If the port command throws an access error, close the Arduino tools with:

```powershell
Get-Process "Arduino IDE","arduino-cli","arduino-language-server" -ErrorAction SilentlyContinue | Stop-Process -Force
```

Then run the port command again.

## 6. Play The Newest Downloaded MIDI

Use this when you downloaded a new `.mid` file into the normal Windows Downloads folder.

Normal speed:

```powershell
python -u scripts\play_piano.py --play-latest --fit-mode transpose --tempo 1x --port <COM_PORT>
```

Half speed:

```powershell
python -u scripts\play_piano.py --play-latest --fit-mode transpose --tempo .5 --port <COM_PORT>
```

Original pitches only, skipping out-of-range notes:

```powershell
python -u scripts\play_piano.py --play-latest --fit-mode strict --tempo 1x --port <COM_PORT>
```

## 7. Choose An Existing Project Song

Use this when you want to pick from the repo's `songs\midi` folder.

```powershell
python -u scripts\play_piano.py --choose-library --fit-mode transpose --tempo 1x --port <COM_PORT>
```

Dry-run the chooser without sending anything to the Arduino:

```powershell
python -u scripts\play_piano.py --choose-library --fit-mode transpose --tempo 1x --dry-run
```

## 8. Play A Specific Project Song

Use this when you know the exact filename inside `songs\midi`.

```powershell
python -u scripts\play_piano.py --project-song "<SONG_NAME.mid>" --fit-mode transpose --tempo 1x --port <COM_PORT>
```

Example:

```powershell
python -u scripts\play_piano.py --project-song "hes_a_pirate_isolated_melody.mid" --fit-mode transpose --tempo .5 --port <COM_PORT>
```

## 9. Play A Specific Downloaded MIDI Path

Use this when the MIDI file is somewhere outside the project folder.

```powershell
python -u scripts\play_piano.py --song "<FULL_MIDI_PATH>" --fit-mode transpose --tempo 1x --port <COM_PORT>
```

Example:

```powershell
python -u scripts\play_piano.py --song "C:\Users\name\Downloads\my_song.mid" --fit-mode transpose --tempo 1x --port <COM_PORT>
```

## 10. If You Built A New Octave

If channels are physically wired in exact chromatic order, run octave calibration:

```powershell
python -u scripts\piano_tools.py --port <COM_PORT> --calibrate-octave
```

If wiring order is unknown, use manual calibration:

```powershell
python -u scripts\piano_tools.py --port <COM_PORT> --calibrate-manual
```

After calibration, verify with a sweep:

```powershell
python -u scripts\piano_tools.py --port <COM_PORT> --sweep
```

Test one raw PCA9685 channel:

```powershell
python -u scripts\piano_tools.py --port <COM_PORT> --tune-channel <CHANNEL_NUMBER>
```

Example:

```powershell
python -u scripts\piano_tools.py --port COM3 --tune-channel 4
```

## 11. If You Only Want To Analyze A Song

No Arduino required:

```powershell
python -u scripts\play_piano.py --song "<FULL_MIDI_PATH>" --fit-mode transpose --tempo 1x --dry-run
```

Generate output files but do not send over USB:

```powershell
python -u scripts\play_piano.py --song "<FULL_MIDI_PATH>" --fit-mode transpose --tempo 1x --export-only
```

## 12. Pedal Servo Test

Upload this sketch first:

```text
arduino\PedalServoBenchTest\PedalServoBenchTest.ino
```

Then close the Arduino IDE and run:

```powershell
python -u scripts\pedal_servo_reaction_test.py --port <COM_PORT>
```

Quick short test:

```powershell
python -u scripts\pedal_servo_reaction_test.py --port <COM_PORT> --measured-moves 2
```

## 13. Pedal Actuation Sweep

Use this when you want to watch the pedal servo press and release with a few built-in motion profiles.

Upload this sketch:

```text
arduino\PedalServoActuationSweep\PedalServoActuationSweep.ino
```

It auto-cycles through:

- direct full-speed motion
- the measured median timing profile
- a firmer faster ramp
- a softer slower ramp

Optional: open the Arduino Serial Monitor at `115200` baud to see which profile is running or to send:

- `n` for the next profile
- `r` to repeat the current profile
- `p` to pause or resume auto-cycle
- `h` to home the servo
- `?` for help

## Notes

- Do not upload `.json` or `.h` files to the Arduino. The runtime sketch is `arduino\MusicBotOfficial\MusicBotOfficial.ino`.
- Use `--fit-mode transpose` when you want the song shifted by octaves to fit the available solenoids.
- Use `--fit-mode strict` when you want original pitches only, with out-of-range notes skipped.
- Close Arduino IDE before Python playback so the serial port is available.
- If something starts buzzing or holding unexpectedly, unplug power first, then debug the command or wiring.
