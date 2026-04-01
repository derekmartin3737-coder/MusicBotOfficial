# TODO: Option B Serial Runtime Plan

## Target user workflow

The intended final workflow is:

1. Find a MIDI file online
2. Download it normally into Windows Downloads
3. Run one Python command
4. Python automatically finds the newest downloaded MIDI
5. Python asks simple user questions such as tempo or playback options
6. Python converts the MIDI
7. Python sends the song to the Arduino over USB
8. The piano plays without reflashing firmware for every song

## Non-negotiable final requirement

The finished system must not require the user to edit code for normal operation.

That means:

- the user must not edit `.ino` files
- the user must not edit `.py` files
- the user must not edit generated `.h` files
- the user must not manually move generated files
- the user must not manually change include paths or active song names in Arduino code

Normal interaction must happen only through inputs such as:

- downloading a MIDI file normally
- selecting a song by filename or newest-file behavior
- answering simple prompts
- optional command-line arguments
- optional user-safe configuration inputs

Developer code changes are allowed while we build the system, but the final workflow must not depend on them.

## Current routing and source of truth

### Desired end-user input source

- `C:\Users\derek\Downloads`
  - final user workflow should default to the newest `.mid` or `.midi` file here

### Current project staging/input folder

- `songs/midi/`
  - current converter input folder during development

### Python conversion source

- `scripts/convert_midi.py`
  - current converter
  - currently generates Arduino-ready `.h` data and `.json` metadata

### Arduino IDE deployment target

- `C:\Users\derek\OneDrive - Oregon State University\Documents\Arduino\Capstone_python_arduino_led_code\Capstone_python_arduino_led_code.ino`
  - configured Arduino IDE sketch target

### Active generated header target

- `C:\Users\derek\OneDrive - Oregon State University\Documents\Arduino\Capstone_python_arduino_led_code\generated\current_song.h`
  - current mirrored active header for the Arduino IDE sketch

### Repo copy

- `arduino/MusicBotOfficial/MusicBotOfficial.ino`
  - repo source sketch
- `arduino/MusicBotOfficial/generated/current_song.h`
  - repo copy of the active generated song

The repo remains the authoring source, but the converter syncs the active sketch and header to the Arduino IDE sketchbook path above.

## What is already done

- MIDI conversion works
- Active generated song is written as `current_song.h`
- Active metadata is written as `current_song.json`
- Note mapping is configured for:
  - `C3 -> channel 0`
  - `D3 -> channel 1`
  - `E3 -> channel 2`
- Notes outside that mapping are skipped
- Mixed 25N / 5N channel tuning exists
- Same-time events are grouped for better chord timing
- The converter is configured to sync the active sketch and header to the Arduino IDE sketchbook folder

## What is still missing for the real user logistics

- Python does not yet default to the newest MIDI in Windows Downloads
- Python does not yet import or track the newest downloaded MIDI automatically
- Python does not yet ask beginner-friendly prompts for tempo and playback options
- Python does not yet stream event data over USB to the Arduino
- Python does not yet auto-detect and verify the correct COM port
- Python does not yet gracefully handle:
  - no MIDI found in Downloads
  - invalid MIDI files
  - `.zip` downloads instead of MIDI files
  - unsupported notes
  - multiple serial devices connected
- The current flow still assumes a technical operator during development

## Why Option B is the right target

Option B means:

- the Arduino runs a fixed playback firmware
- Python converts a MIDI into runtime event data
- Python sends the song over serial
- the Arduino plays it immediately

This best matches the desired user experience:

1. download MIDI
2. run Python
3. answer simple prompts
4. piano plays

It also removes the need to re-upload the Arduino sketch every time a new song is chosen.

## What still exists from the current Option A-style workflow

Right now the system still compiles songs into `current_song.h`.

That is still useful because:

- it keeps the project playable during development
- it gives a reliable fallback if serial streaming is not ready
- it provides a good event format to evolve into a serial protocol

## Main tasks to complete Option B

### Phase 0: Separate one-time setup from daily use

- [ ] Define the one-time engineering setup steps:
  - install Python dependencies
  - install USB serial dependencies
  - flash the fixed Arduino runtime once
  - verify the PCA9685 and solenoid hardware once
- [ ] Define the daily user workflow separately from setup
- [ ] Make sure the daily workflow never requires reopening setup instructions
- [ ] Consider packaging the Python workflow as:
  - a double-click script
  - or a simple executable

### Phase 1: Lock down the fixed Arduino runtime

- [ ] Keep one stable Arduino sketch in:
  - `C:\Users\derek\OneDrive - Oregon State University\Documents\Arduino\Capstone_python_arduino_led_code\Capstone_python_arduino_led_code.ino`
- [ ] Make the fixed runtime stable enough that the user never needs to edit or swap Arduino sketch code during normal playback
- [ ] Stop treating songs as compile-time-only firmware content
- [ ] Define the Arduino runtime responsibilities:
  - initialize PCA9685
  - receive song packets over serial
  - buffer events
  - start playback
  - stop playback
  - report errors/status back to Python

### Phase 2: Define the serial song protocol

- [ ] Decide whether the protocol is:
  - line-based text
  - compact CSV-like messages
  - binary packets
- [ ] Define required message types:
  - handshake
  - clear song buffer
  - song metadata
  - event packet
  - playback begin
  - playback stop
  - runtime status
- [ ] Include enough data per event for:
  - delta time
  - channel
  - PWM value
- [ ] Support chunked transfer so large songs do not require full in-RAM storage

### Phase 3: Build the Python sender

- [ ] Add `pyserial` to the Python dependencies
- [ ] Create a Python serial sender that:
  - opens the COM port
  - resets or handshakes with the Arduino
  - sends the converted events
  - tells the Arduino to begin playback
- [ ] Auto-detect the connected Arduino over USB by default
- [ ] Provide a friendly fallback prompt if multiple COM ports are present
- [ ] Add clear terminal output for:
  - chosen MIDI
  - mapped notes
  - skipped notes
  - port used
  - successful transfer
- [ ] Make Python the only normal operator entry point for playback

### Phase 4: Keep the current converter as the event engine

- [ ] Reuse the current converter scheduling logic
- [ ] Split output modes into:
  - header export mode
  - serial streaming mode
- [ ] Keep `.json` metadata generation for debugging
- [ ] Add a manifest of the most recent streamed song

### Phase 5: Reduce the user flow to one command

- [ ] Support default behavior:
  - choose newest MIDI in `C:\Users\derek\Downloads`
  - accept both `.mid` and `.midi`
  - validate that it is a readable MIDI file
  - import or track it inside the project if needed
  - convert it
  - send it to Arduino
  - start playback
- [ ] Keep optional overrides for:
  - explicit MIDI filename
  - explicit filepath
  - tempo override
  - dry run
  - export-only mode
- [ ] Prompt the user in plain language instead of technical terms where possible
- [ ] Ensure these remain user inputs rather than code edits

### Phase 6: Handle beginner-proof edge cases

- [ ] Handle "no MIDI found in Downloads" with a simple recovery message
- [ ] Handle invalid or corrupted MIDI files gracefully
- [ ] Handle songs with unsupported notes by warning clearly and offering to continue
- [ ] Handle accidental ZIP downloads clearly
- [ ] Show the user exactly which file was chosen and why
- [ ] Confirm the Arduino is connected before attempting playback

### Phase 7: Preserve a fallback path

- [ ] Keep `current_song.h` generation working while serial runtime is under development
- [ ] Keep the Arduino IDE sync path working
- [ ] Keep manual upload available as a fallback during development
- [ ] Remove the need for the user to touch fallback internals once the final serial workflow is complete

### Phase 8: Externalize all routine user choices

- [ ] Move all routine song-selection behavior into Python inputs
- [ ] Move all routine playback options into command-line arguments or a user-safe config file
- [ ] Separate developer tuning values from user-facing controls
- [ ] Document which settings are safe for the user to change
- [ ] Ensure the final workflow does not require opening source files at all
- [ ] Keep the default mode beginner-safe:
  - newest MIDI in Downloads
  - simple tempo prompt
  - automatic USB transfer

## Things to watch out for

- The Arduino has limited RAM, so large songs may need chunked streaming instead of full buffering
- Serial playback must be robust enough not to corrupt timing or partially load songs
- Downloaded MIDI files may use notes outside `C3/D3/E3`
- Songs with dense chords or very fast repeated notes may need more scheduling or queue tuning
- The Python-to-Arduino serial path needs a stable COM port selection strategy
- The fixed runtime and the repo source must stay in sync
- The "most recently downloaded file" rule needs to be precise:
  - newest `.mid` or `.midi` by modification time
- The current hardware setup is one Arduino controlling the PCA9685 and solenoids, not multiple independent Arduinos

## Near-term implementation order

1. Build the fixed serial playback Arduino runtime
2. Add Python serial transport using the existing converted event format
3. Add newest-file detection from Windows Downloads
4. Add simple prompts and COM auto-detection
5. Keep header export as a fallback
6. Switch the default workflow to serial playback once stable

## Are we ready to begin?

Not yet for the final non-technical user workflow.

Macroscopically, the plan is close in spirit but not complete in execution.

What already matches the logistics well:

- conversion logic exists
- note mapping exists
- active routing to the Arduino sketchbook path exists
- a single Python entry point is a realistic target

What is still missing before the workflow truly fits a non-technical user:

- a one-time setup process that is distinct from normal use
- newest-MIDI-from-Downloads automation
- beginner-friendly prompts
- USB serial transfer to the Arduino
- COM-port auto-detection
- robust error handling for bad downloads and unsupported files

## Definition of done for Option B

Option B is complete when the user can:

1. download a MIDI into Windows Downloads
2. run one Python command
3. let Python automatically find the newest MIDI
4. answer simple prompts such as tempo
5. watch Python convert and send the song over USB
6. hear the piano play

without reopening Arduino IDE or re-uploading firmware for each song

And also when:

- one-time setup has been reduced to a clearly documented install-and-flash step
- the user does not need to edit any source code
- the user does not need to manually copy generated files
- the user does not need to rename or relink Arduino includes
- the user does not need to understand Arduino IDE internals
