import pytest

from meeting_notes_summarizer.summarizer import summarize
from meeting_notes_summarizer.parser import read_lines, strip_timestamps_and_blanks


TRANSCRIPT = """\
Dana: The launch is next week. We decided to go with the three-step flow.

Marcus: Will do. I will finish the progress bar by Friday.

Dana: Who owns the email announcement?

Priya: What about users who abandon step 2?
"""


def test_strip_timestamps_and_blanks_removes_noise():
    text = "[00:01] Dana: hello\n\n[00:02] Marcus: hi\n"
    lines = strip_timestamps_and_blanks(text)
    assert lines == ["Dana: hello", "Marcus: hi"]


def test_strip_timestamps_and_blanks_handles_seconds():
    text = "[00:01:23] Dana: hello there\n"
    assert strip_timestamps_and_blanks(text) == ["Dana: hello there"]


def test_summarize_extracts_decisions():
    report = summarize(TRANSCRIPT)
    assert any("three-step" in d.text for d in report.decisions)


def test_summarize_extracts_action_item_with_owner_and_date():
    report = summarize(TRANSCRIPT)
    owners = {(a.owner, a.date) for a in report.action_items}
    assert ("Marcus", "by Friday") in owners
    assert any("progress bar" in a.text for a in report.action_items)


def test_summarize_extracts_questions():
    report = summarize(TRANSCRIPT)
    texts = " ".join(q.text for q in report.open_questions)
    assert "abandon step 2" in texts


def test_summarize_produces_summary_and_recap():
    report = summarize(TRANSCRIPT)
    assert report.summary
    assert "action item" in report.recap.lower()


def test_report_markdown_contains_all_sections():
    out = summarize(TRANSCRIPT).to_markdown()
    for heading in ("Summary", "Decisions", "Action Items", "Open Questions", "Plain-English Recap"):
        assert heading in out


def test_report_text_render_has_checkboxes_only_in_md():
    text = summarize(TRANSCRIPT).to_text()
    assert "- [ ]" not in text


def test_empty_transcript_does_not_crash():
    report = summarize("   \n\n  ")
    assert report.summary == ""
    assert report.to_markdown()
