"""meeting_notes_summarizer: local-first meeting transcript summarizer.

Everything runs on your machine. The only point of contact with another
process is the optional "polish" step, which talks to an OpenAI-compatible
endpoint you configure (usually Ollama on localhost). Nothing is sent
anywhere unless you ask for it.
"""

__version__ = "0.1.0"

from .models import ActionItem, Decision, MeetingReport, OpenQuestion  # noqa: F401
from .summarizer import summarize  # noqa: F401
