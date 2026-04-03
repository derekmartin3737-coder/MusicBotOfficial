# Setup

Use this once on a new machine.

## 1. Clone the repo

Clone the GitHub repository and open the project root.

## 2. Install Python dependencies

From the repo root:

```bash
pip install -r requirements.txt
```

## 3. Install the Arduino library

In Arduino IDE, install:

- `Adafruit PWM Servo Driver Library`

## 4. Upload the Arduino runtime once

Open:

- [MusicBotOfficial.ino](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/arduino/MusicBotOfficial/MusicBotOfficial.ino)

Then:

1. Plug in the Arduino Uno by USB
2. Select the board and COM port
3. Upload the sketch

After that, normal song playback happens from Python over USB. You do not need to re-upload for each new MIDI.

## 5. Verify the hardware

Confirm:

- Arduino `A4` -> PCA9685 `SDA`
- Arduino `A5` -> PCA9685 `SCL`
- common ground between Arduino, PCA9685, MOSFET stage, and power supply
- each solenoid has flyback protection
- the solenoid supply is separate from the Arduino 5V rail

## 6. Optional double-click entry points

The repo includes:

- [play_piano.bat](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/play_piano.bat)
- [calibrate_piano.bat](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/calibrate_piano.bat)

These use `.venv\Scripts\python.exe` if it exists, otherwise they fall back to `python` on the system path.
