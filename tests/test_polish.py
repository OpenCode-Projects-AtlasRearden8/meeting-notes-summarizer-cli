import json
from unittest import mock

import pytest

from meeting_notes_summarizer.polish import (
    chat_completions,
    parse_polish_reply,
    polish_report,
    build_polish_payload,
)
from meeting_notes_summarizer.summarizer import summarize


TRANSCRIPT = (
    "Dana: Welcome everyone, this is our weekly sync.\n"
    "Marcus: First up, the site redesign status.\n"
    "Dana: We decided to go with the simple flow.\n"
    "Marcus: I will ship it by Monday.\n"
    "Priya: Support data came back and it looks promising.\n"
    "Dana: Great, thanks for checking on that report.\n"
    "Marcus: The bug backlog is shrinking week over week.\n"
    "Priya: The office coffee machine repair is scheduled for Tuesday afternoon.\n"
    "Dana: Okay, parking lot items noted for next time.\n"
)
REPLY = (
    "NEW SUMMARY: The team picked the simple flow, honestly a smart small step.\n"
    "NEW RECAP: One lock-in choice, one task, nothing dangling.\n"
)


class FakeResponse:
    def __init__(self, body: dict):
        self._body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


def test_polish_report_updates_prose_and_flags_polished(monkeypatch):
    report = summarize(TRANSCRIPT)
    calls = {}

    def fake_chat(base_url, model, messages, temperature, timeout):
        calls["base_url"] = base_url
        calls["model"] = model
        return REPLY

    monkeypatch.setattr("meeting_notes_summarizer.polish.chat_completions", fake_chat)
    polished = polish_report(report, TRANSCRIPT, base_url="http://localhost:11434/v1", model="llama3.1")
    assert polished.summary.startswith("The team picked")
    assert polished.recap.startswith("One lock-in choice")
    assert polished.polished is True
    assert calls["base_url"] == "http://localhost:11434/v1"
    assert calls["model"] == "llama3.1"


def test_polish_never_sends_full_transcript_by_default(monkeypatch):
    report = summarize(TRANSCRIPT)
    seen = {}

    def fake_chat(base_url, model, messages, temperature, timeout):
        seen["user_msg"] = messages[-1]["content"]
        return REPLY

    monkeypatch.setattr("meeting_notes_summarizer.polish.chat_completions", fake_chat)
    polish_report(report, TRANSCRIPT, base_url="http://localhost:11434/v1", model="m")
    # derived prose is fine, but the full flattened transcript must not be shipped along
    assert "sync. Marcus: First up" not in seen["user_msg"]
    assert "Current summary:" in seen["user_msg"]


def test_polish_includes_transcript_only_when_requested(monkeypatch):
    report = summarize(TRANSCRIPT)
    seen = {}

    def fake_chat(base_url, model, messages, temperature, timeout):
        seen["user_msg"] = messages[-1]["content"]
        return REPLY

    monkeypatch.setattr("meeting_notes_summarizer.polish.chat_completions", fake_chat)
    polish_report(report, TRANSCRIPT, base_url="http://localhost:11434/v1", model="m",
                  send_transcript=True)
    assert "sync. Marcus: First up" in seen["user_msg"]


def test_polish_prompt_includes_transcript_only_when_requested():
    report = summarize(TRANSCRIPT)
    from meeting_notes_summarizer.polish import POLISH_PROMPT_TEMPLATE
    with_transcript = POLISH_PROMPT_TEMPLATE.format(
        title=report.title, summary=report.summary, recap=report.recap,
        context=TRANSCRIPT,
    )
    assert "I will ship it by Monday" in with_transcript


def test_chat_completions_posts_to_chat_completions_url_without_auth(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.headers)
        captured["body"] = json.loads(req.data.decode())
        return FakeResponse({"choices": [{"message": {"content": "hi"}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    out = chat_completions(
        base_url="http://localhost:11434/v1",
        model="llama3.1",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.3,
        timeout=5,
    )
    assert out == "hi"
    assert captured["url"] == "http://localhost:11434/v1/chat/completions"
    assert captured["body"]["model"] == "llama3.1"
    assert captured["body"]["messages"] == [{"role": "user", "content": "hello"}]
    headers = {k.lower(): v for k, v in captured["headers"].items()}
    assert "authorization" not in headers
    assert "api-key" not in headers


def test_chat_completions_rejects_unexpected_shape(monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda req, timeout: FakeResponse({"nope": True})
    )
    with pytest.raises(ValueError):
        chat_completions("http://localhost:11434/v1", "m", [{"role": "user", "content": "x"}], 0.3, 5)


def test_parse_polish_reply_or_semantics():
    assert parse_polish_reply("banana") is None
    parsed = parse_polish_reply(REPLY)
    assert parsed["summary"].startswith("The team picked")
    assert parsed["recap"].startswith("One lock-in choice")
    assert parsed is not None


def test_build_polish_payload_has_system_and_user():
    report = summarize(TRANSCRIPT)
    messages = build_polish_payload(report, "some context")
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert "polish" in messages[-1]["content"].lower() or "rewrite" in messages[-1]["content"].lower()
