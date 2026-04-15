"""Command-line entry point for normal song playback.

This file intentionally stays small. The actual MIDI analysis, note mapping,
file generation, and USB streaming logic lives in convert_midi.py. Keeping this
as a wrapper lets classmates run one obvious command without needing to know the
internal module name.
"""

import convert_midi as engine


if __name__ == "__main__":
    try:
        engine.main()
    except (EOFError, FileNotFoundError, RuntimeError, TimeoutError, ValueError, OSError) as error:
        print(f"\nUnable to continue: {error}")
        raise SystemExit(1)
