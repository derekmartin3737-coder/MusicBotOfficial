# Serial Protocol

The current Arduino runtime uses a line-based text protocol over USB serial.

Protocol version:

- `2`

Runtime sketch:

- [MusicBotOfficial.ino](/C:/Users/derek/Downloads/Capstone/Music%20bot%20official%20directory/arduino/MusicBotOfficial/MusicBotOfficial.ino)

## Handshake

Python sends:

```text
HELLO
```

Arduino replies:

```text
READY 2 BUFFER 48
```

That reports the protocol version and event buffer capacity.

## Song streaming

1. Python sends:

```text
CLEAR
BEGIN <total_event_count>
```

2. Arduino replies:

```text
OK BEGIN capacity=<buffer_capacity> total=<total_event_count>
```

3. Python sends a chunk of events:

```text
EVENT <dt_ms> <channel> <pwm>
EVENT <dt_ms> <channel> <pwm>
...
```

4. Python sends:

```text
COMMIT
```

5. Arduino replies:

```text
OK ACCEPTED recv=<received_count> free=<free_slots> total=<total_event_count>
```

6. Python sends:

```text
PLAY
```

7. Arduino replies:

```text
OK PLAYING
```

8. Python keeps polling:

```text
STATUS
```

Arduino replies with:

```text
STATUS <state> recv=<received_count> played=<played_count> buffered=<buffered_count> free=<free_slots> total=<total_event_count>
```

9. Python keeps sending chunks as space opens up.

10. When playback finishes, Arduino sends:

```text
OK PLAYBACK_DONE
```

## Debug commands

Turn everything off:

```text
ALL_OFF
```

Fire one calibration pulse:

```text
FIRE <channel> <strike_pwm> <hold_pwm> <strike_ms> <hold_ms> <release_ms>
```

## Why chunking exists

The Arduino Uno does not have enough RAM to preload arbitrarily large songs. The runtime therefore keeps only a ring buffer of upcoming events and lets Python continue feeding the rest of the song while playback is running.
