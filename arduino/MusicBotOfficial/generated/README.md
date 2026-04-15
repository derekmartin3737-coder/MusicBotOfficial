# Generated Song Headers

This folder stores Arduino header files created by the MIDI converter.

## Tracked Files

Curated example headers are committed so teammates can inspect generated output or use `HeaderPlaybackFallback.ino` without running Python first.

## Ignored Files

`current_song.h` is intentionally ignored. It is the local "last conversion" output and changes every time someone tests a different song.

Repeated downloaded imports such as `*_imported_v*.h` are also ignored. If the team wants to keep a generated header permanently, give the source song a stable project name and commit the curated output intentionally.
