"""Allow `python -m meeting_notes_summarizer ...`."""
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
