import json
from typing import Any, Dict, List, Optional

from .models import MeetingReport

SYSTEM_PROMPT = (
    "You are a careful editor for meeting summaries. "
    "Keep things plain-English, warm, and brief. "
    "Never invent facts that are not in the input. "
    "Do not add medical, legal, or financial advice."
)

POLISH_PROMPT_TEMPLATE = """Rewrite the two prose sections of this meeting report so they are clearer \
and friendlier, like explaining to a smart friend. Do not change any facts, do not add \
new facts, and do not touch the decisions, action items, or questions.

Title: {title}

Current summary:
{summary}

Current recap:
{recap}

Recent sentences from the transcript you may use for wording (never invent beyond these):
{context}

Reply with exactly:
NEW SUMMARY: <one short paragraph>
NEW RECAP: <one short paragraph>
"""


def build_polish_payload(report: MeetingReport, context: str) -> List[Dict[str, str]]:
    prompt = POLISH_PROMPT_TEMPLATE.format(
        title=report.title,
        summary=report.summary or "(blank)",
        recap=report.recap or "(blank)",
        context=context[:2000],
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]


def parse_polish_reply(text: str) -> Optional[Dict[str, str]]:
    summary = None
    recap = None
    for key, out in (("NEW SUMMARY:", "summary"), ("NEW RECAP:", "recap")):
        m = text.find(key)
        if m == -1:
            continue
        starts = [k for k in ("NEW SUMMARY:", "NEW RECAP:") if text.find(k, m + 1) != -1]
        if starts:
            end = min(text.find(k, m + 1) for k in starts)
        else:
            end = len(text)
        value = text[m + len(key):end].strip().strip("`")
        value = "\n".join(l.strip() for l in value.splitlines() if l.strip())
        if out == "summary":
            summary = value or summary
        else:
            recap = value or recap
    if summary is None and recap is None:
        return None
    return {"summary": summary, "recap": recap}


def chat_completions(base_url: str, model: str, messages: List[Dict[str, str]],
                     temperature: float, timeout: float) -> str:
    """POST to an OpenAI-compatible /chat/completions endpoint.

    No API key, no auth headers: these endpoints are expected to be local
    (e.g. Ollama, llama.cpp server, LM Studio).
    """
    import urllib.request

    url = base_url.rstrip("/")
    if not url.endswith("/chat/completions"):
        url = url + "/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8", errors="replace"))
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Unexpected response shape from endpoint: {body!r}") from exc


def polish_report(report: MeetingReport, transcript_text: str, base_url: str,
                  model: str, temperature: float = 0.3, timeout: float = 60.0,
                  send_transcript: bool = False) -> MeetingReport:
    context = ""
    if send_transcript and transcript_text.strip():
        context = " ".join(
            line for line in transcript_text.strip().splitlines() if line.strip()
        )
        # strip timestamps to keep the payload small
        context = "\n".join(
            line for line in context.splitlines()
            if line.strip() and not line.strip().startswith(("[", "("))
        )
    messages = build_polish_payload(report, context)
    reply = chat_completions(base_url, model, messages, temperature, timeout)
    parsed = parse_polish_reply(reply)
    if parsed:
        if parsed.get("summary"):
            report.summary = parsed["summary"]
        if parsed.get("recap"):
            report.recap = parsed["recap"]
    report.polished = True
    return report
