import convert_midi as engine


if __name__ == "__main__":
    try:
        engine.main()
    except (EOFError, FileNotFoundError, RuntimeError, TimeoutError, ValueError, OSError) as error:
        print(f"\nUnable to continue: {error}")
        raise SystemExit(1)
