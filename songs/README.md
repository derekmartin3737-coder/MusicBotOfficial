# Songs Folder

The song library has two jobs:

- `songs\midi` contains curated MIDI examples that are safe for the whole team to share.
- `songs\metadata` contains generated analysis/output data from the converter.

Repeated local imports from Downloads, such as `*_imported_v*.mid`, are ignored so the library does not fill up with duplicates during testing.

If you want to test a private or temporary MIDI without adding it to GitHub, place it in `songs\midi\local` or leave it in your normal Windows Downloads folder and run `scripts\play_piano.py --play-latest`.

If you want a MIDI to become a shared project song, give it a clear filename in `songs\midi`, run the converter, review the output, and commit the curated MIDI plus any generated metadata/header that the team intentionally wants to keep.
