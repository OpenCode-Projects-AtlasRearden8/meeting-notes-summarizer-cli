import datetime
import re
from typing import List, Optional, Tuple

DECISION_PATTERNS = [
    r"\b(?:we|i)\s+(?:decided|agreed)\b",
    r"\bdecision\s*[:\-]",
    r"\bwe(?:'ll| will) go with\b",
    r"\bapproved\b",
    r"\blet'?s (?:use|go|ditch|keep|drop)\b",
    r"(?<!\bwon't )\bwe will (?:use|keep|drop|move|ship)\b",
]

ACTION_PATTERNS = [
    r"\baction\s*(?:item)?\s*[:\-]\s*",
    r"\btodo\s*[:\-]\s*",
]

MONTHS = ("jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec")

DATE_PATTERNS = [
    r"(?:by|before|due|on)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|next week|this week|next month|tomorrow|eod|eow|end of (?:day|week|month))\b",
    r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b",
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sept?|oct|nov|dec)[a-z]*\.?\s+\d{1,2}\b",
    r"\bnext week\b|\bthis week\b|\btomorrow\b|\bnext (?:monday|tuesday|wednesday|thursday|friday)\b|\bend of (?:day|week|month)\b|\beod\b|\beow\b",
]

QUESTION_STARTERS = r"(?:what|why|how|when|where|who|which|should|can|could|do|does|did|are|is|will|would)\b"


def _load_text(source: Optional[str], file_path: Optional[str]) -> str:
    if file_path:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    if source:
        return source
    return ""


def read_lines(text: str) -> List[str]:
    return [line for line in _clean_lines(text) if line]


def _clean_lines(text: str) -> List[str]:
    cleaned = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            cleaned.append("")
            continue
        # strip common transcript timestamps like "[00:12:34]" or "(00:12)"
        line = re.sub(r"^[\[(]\d{1,2}:\d{2}(?::\d{2})?[\])]\s*", "", line)
        cleaned.append(line)
    return cleaned


strip_timestamps_and_blanks = read_lines


def sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def find_decision(s: str) -> bool:
    for pat in DECISION_PATTERNS:
        if re.search(pat, s, flags=re.IGNORECASE):
            return True
    return False


def extract_decision(s: str) -> str:
    m = re.match(r"^\s*(?:decision\s*[:\-]\s*)?(.*)$", s, flags=re.IGNORECASE)
    return m.group(1).strip().rstrip(";,.!") if m else s


def find_action(s: str) -> bool:
    if any(re.search(p, s, flags=re.IGNORECASE) for p in ACTION_PATTERNS):
        return True
    # "Name will ..." or "Name needs to ..."
    if re.match(r"^[A-Z][\w .':-]{0,30}\b(?:will|'ll|needs? to|to-do|todo)\b", s):
        return True
    if re.search(r"^(?:I|We)\s+(?:will|'ll)\b", s):
        return True
    return False


def strip_action_prefix(s: str) -> str:
    for pat in ACTION_PATTERNS:
        if re.search(pat, s, flags=re.IGNORECASE):
            return re.sub(pat, "", s, count=1, flags=re.IGNORECASE).strip()
    return s


NON_OWNER_LABELS = {
    "todo", "to-do", "action", "question", "decision", "note", "issue",
    "topic", "summary", "meeting", "agenda", "next", "follow", "follow-up",
}


def extract_owner(s: str) -> str:
    # speaker-prefixed line, e.g. "Marcus: I will finish the docs"
    m = re.match(r"^([A-Z][\w'-]+(?:\s[A-Z]?[\w'-]+)?)\s*:\s", s)
    if m and m.group(1).lower() not in NON_OWNER_LABELS:
        return m.group(1)
    m = re.match(r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b(?:\s+will|\s+'ll|\s+needs? to|\s+is going to|\s+owns)\b", s)
    if m:
        return m.group(1)
    # allow lowercase names like "sam will"
    m = re.match(r"^([a-z][a-z]+(?:\s[a-z][a-z]+)?)\s+(?:will|'ll)\b", s)
    if m:
        return m.group(1).capitalize()
    return ""


def extract_date(s: str) -> str:
    for pat in DATE_PATTERNS:
        m = re.search(pat, s, flags=re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return ""


def is_question(s: str) -> bool:
    if s.endswith("?"):
        return True
    if re.search(r"\?\s*$", s):
        return True
    return False


def starts_question(s: str) -> bool:
    return bool(re.match(r"^\s*" + QUESTION_STARTERS, s, flags=re.IGNORECASE))


def slugify(value: str) -> str:
    value = re.sub(r"[^\w\- ]+", "", value).strip().lower()
    return re.sub(r"[\s_]+", "-", value)[:60] or "meeting"


def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def suggest_title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line and (line.isupper() or line.startswith("#")):
            return line.lstrip("#").strip()[:80]
        if line:
            break
    return "Meeting Notes"
