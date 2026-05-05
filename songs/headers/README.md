# Generated Song Headers

This folder stores versioned Arduino header files created by the MIDI converter.

The headers live here instead of under `arduino/MusicBotOfficial` because the
Arduino IDE scans sketch folders and can ask to rename files whose names contain
characters it dislikes. New generated header names are sanitized to
letters/numbers/underscores only.

`arduino/MusicBotOfficial/generated/current_song.h` remains the local active
export used for debugging the last conversion.
