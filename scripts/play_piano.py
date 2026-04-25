"""Command-line entry point for normal song playback.

This file intentionally stays small. The actual MIDI analysis, note mapping,
file generation, and USB streaming logic lives in convert_midi.py. By default it
launches a Tkinter GUI so classmates can run one obvious file from an IDE. Pass
CLI arguments, or `--cli`, to use the original terminal workflow. Calibration
flags are also routed through this entry point so users can keep launching one
script for both playback and mapping setup.
"""

import sys

import convert_midi as engine

CALIBRATION_FLAGS = {
    "--calibrate",
    "--sweep",
    "--calibrate-octave",
    "--calibrate-manual",
    "--patch-mapping",
    "--tune-channel",
}


if __name__ == "__main__":
    try:
        if "--calibrate" in sys.argv[1:]:
            sys.argv = [sys.argv[0]] + [arg for arg in sys.argv[1:] if arg != "--calibrate"]
            import piano_tools

            piano_tools.main()
            raise SystemExit(0)

        if any(flag in sys.argv[1:] for flag in CALIBRATION_FLAGS - {"--calibrate"}):
            import piano_tools

            piano_tools.main()
            raise SystemExit(0)

        use_cli = len(sys.argv) > 1
        if "--cli" in sys.argv[1:]:
            use_cli = True
            sys.argv = [sys.argv[0]] + [arg for arg in sys.argv[1:] if arg != "--cli"]

        if use_cli:
            engine.main()
        else:
            try:
                import play_piano_gui
            except ImportError:
                print("Tkinter GUI is unavailable, so falling back to the terminal workflow.")
                engine.main()
            else:
                play_piano_gui.main()
    except (EOFError, FileNotFoundError, RuntimeError, TimeoutError, ValueError, OSError) as error:
        print(f"\nUnable to continue: {error}")
        raise SystemExit(1)
