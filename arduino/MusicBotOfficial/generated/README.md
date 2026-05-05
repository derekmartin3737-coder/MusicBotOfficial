# Active Song Header

This folder is inside the Arduino sketch folder, so keep it boring for the
Arduino IDE.

Only `current_song.h` belongs here during normal playback. It is overwritten by
the Python converter and is ignored by Git.

Versioned song headers are archived outside the Arduino sketch folder in
`songs/headers` so downloaded song names cannot make the Arduino IDE ask to
rename sketch tabs.
