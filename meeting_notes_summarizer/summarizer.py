import re
from typing import List, Optional, Tuple

from .models import ActionItem, Decision, MeetingReport, OpenQuestion
from .parser import (
    extract_date,
    extract_decision,
    extract_owner,
    find_action,
    find_decision,
    is_question,
    read_lines,
    sentences,
    strip_action_prefix,
    suggest_title,
)

STOPWORDS = set(
    "the a an and or but so if then we i you he she they it our your their is are "
    "was were be been am do does did will would can could should shall may might "
    "to of in on at for with by from as that this these those there here not no "
    "just really very okay ok um uh yeah yes yep nope going gonna get got have has had".split()
)

ACKNOWLEDGEMENTS = {
    "will do", "ok", "okay", "done", "got it", "sure", "yes", "sounds good", "on it",
}

QUESTION_STARTERS = re.compile(
    r"(?:what|why|how|when|where|who|which|should|can|could|do|does|did|are|is|will|would)\b",
    re.IGNORECASE,
)

QUESTION_LABEL = re.compile(r"^\s*question\s*[:\-]\s*", re.IGNORECASE)
SPEAKER_PREFIX = re.compile(r"^([A-Z][\w'-]{1,20})\s*:\s*(.*)$", re.S)
REQUEST = re.compile(r"^([A-Z][\w'-]+)\s*,?\s*can (?:you|we|someone)\b", re.IGNORECASE)


def _score(sentence: str) -> int:
    score = 0
    lower = sentence.lower()
    if find_decision(lower):
        score += 3
    if find_action(lower):
        score += 2
    if re.search(r"\b(important|key|priority|goal|launch|release|budget|deadline|next steps)\b", lower):
        score += 2
    if re.search(r"\d+", sentence):
        score += 1
    words = [w for w in re.findall(r"[a-z']+", lower) if w not in STOPWORDS]
    score += len(words)
    return score


def build_summary(text: str, max_sentences: int = 5) -> str:
    lines = read_lines(text)
    candidates: List[Tuple[int, int, str]] = []
    paras = [l for l in lines if l.strip()]
    idx = 0
    for i, line in enumerate(paras):
        for j, sent in enumerate(sentences(line)):
            score = _score(sent)
            # opening sentences of the meeting get a small bump
            if j == 0 and i < 4:
                score += 1
            candidates.append((score, idx, sent))
            idx += 1
    if not candidates:
        return ""
    top = sorted(candidates, key=lambda t: (-t[0], t[1]))[:max_sentences]
    top.sort(key=lambda t: t[1])
    return " ".join(s for _, _, s in top)


def clean_question(sent: str) -> str:
    q = sent.strip()
    m = QUESTION_LABEL.match(q)
    if m:
        q = q[m.end():].strip()
    m = SPEAKER_PREFIX.match(q)
    if m and QUESTION_STARTERS.match(m.group(2)):
        q = m.group(2).strip()
    return q.rstrip("?").strip() + "?"


def match_request(sent: str) -> Optional[Tuple[str, str]]:
    """Detect 'Priya, can you draft the email?' as a delegated action item."""
    text_in = sent.strip()
    m = SPEAKER_PREFIX.match(text_in)
    owner_part = m.group(2).strip() if m else text_in
    m = REQUEST.match(owner_part)
    if not m or not text_in.endswith("?"):
        return None
    owner = m.group(1)
    text = re.sub(r"^([A-Z][\w'-]+)\s*,?\s*", "", owner_part, count=1)
    text = text.rstrip("?.!").strip()
    return owner, text


def summarize(text: str) -> MeetingReport:
    report = MeetingReport()
    report.title = suggest_title(text)
    lines = read_lines(text)

    for line in lines:
        if not line:
            continue
        speaker = ""
        m = re.match(r"^([A-Z][\w'-]+(?:\s[A-Z]?[\w'-]+)?)\s*:\s", line)
        if m:
            speaker = m.group(1)
        for sent in sentences(line):
            if sent.strip().lower().rstrip(".!") in ACKNOWLEDGEMENTS:
                continue
            if find_decision(sent) and not is_question(sent):
                report.decisions.append(Decision(extract_decision(sent)))
            elif find_action(sent):
                item = strip_action_prefix(sent)
                owner = extract_owner(item) or extract_owner(sent) or speaker
                # "Dana: Marcus will do X" — keep the dotter as owner only if
                # the person after the colon isn't the one taking the action.
                sm = SPEAKER_PREFIX.match(item)
                if sm:
                    rest_owner = extract_owner(sm.group(2))
                    if rest_owner:
                        item = sm.group(2)
                        owner = rest_owner
                if owner and item.startswith(f"{owner} will "):
                    rest = item[len(owner) + len(" will "):]
                    item = rest[:1].upper() + rest[1:]
                report.action_items.append(
                    ActionItem(text=item.rstrip(";,.!"), owner=owner, date=extract_date(sent))
                )
            elif match_request(sent):
                owner, req_text = match_request(sent)
                report.action_items.append(
                    ActionItem(text=req_text, owner=owner, date=extract_date(sent))
                )
            elif is_question(sent):
                report.open_questions.append(OpenQuestion(clean_question(sent)))

    report.summary = build_summary(text)
    report.recap = build_recap(report)
    return report


def build_recap(report: MeetingReport) -> str:
    bits = []
    n_dec = len(report.decisions)
    n_act = len(report.action_items)
    n_q = len(report.open_questions)
    first = report.summary.split(". ")[0].rstrip(".") if report.summary else "The team met"
    bits.append(f"{first}.")
    if n_dec:
        first_dec = report.decisions[0].text
        bits.append(f"The group locked in {n_dec} decision{'s' if n_dec != 1 else ''} — for example: {first_dec}.")
    else:
        bits.append("No clear decisions were called out in this transcript.")
    if n_act:
        owners = sorted({a.owner for a in report.action_items if a.owner})
        who = " and ".join(owners) if owners else "someone still worth pinning down"
        bits.append(f"There {'is 1 action item' if n_act == 1 else f'are {n_act} action items'}, mostly for {who}.")
    else:
        bits.append("No action items were spotted, so either it was informational or follow-ups need to be written down.")
    if n_q:
        bits.append(f"{n_q} open question{'s' if n_q != 1 else ''} still need{'s' if n_q == 1 else ''} answers before things can move.")
    else:
        bits.append("Nothing was left hanging as an open question.")
    return " ".join(bits)
