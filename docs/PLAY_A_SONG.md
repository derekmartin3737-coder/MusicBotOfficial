# Play A Song

This is the normal daily workflow after setup is already done.

## Fastest path

1. Plug the Arduino into USB
2. Turn on the solenoid power supply
3. Download a MIDI file into Windows Downloads
4. Run:

```bash
python scripts/play_piano.py
```

Or double-click:

- [play_piano.bat](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/play_piano.bat)

The same launcher also includes `Calibrate Note Mapping...` in the GUI if you need to update the saved key mapping before playing.

## What happens next

The tool will:

1. automatically pick the newest `.mid` or `.midi` in Downloads
2. scan the note range
3. show how much of the song is playable
4. ask whether to:
   - keep the original pitches (`strict`)
   - transpose by octave (`transpose`) so out-of-range notes are folded into the playable octave(s) when possible, while folded notes that would smear timing are skipped
   - stop (`cancel`)
5. optionally ask for a tempo override
6. convert the MIDI into timed PWM events
7. send the event stream to the Arduino over USB

## Useful optional command examples

Use a specific project MIDI:

```bash
python scripts/play_piano.py --project-song "Hot Cross Buns.mid"
```

Use a specific file path:

```bash
python scripts/play_piano.py --song "C:\path\to\song.mid"
```

Analyze only, without writing files or sending to hardware:

```bash
python scripts/play_piano.py --project-song "Hot Cross Buns.mid" --dry-run
```

Force a specific fit mode:

```bash
python scripts/play_piano.py --project-song "Hot Cross Buns.mid" --fit-mode strict
```
