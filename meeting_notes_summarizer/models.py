from dataclasses import dataclass, field
from typing import List


@dataclass
class Decision:
    text: str


@dataclass
class ActionItem:
    text: str
    owner: str = ""
    date: str = ""

    def display(self) -> str:
        bits = []
        if self.owner:
            bits.append(f"@{self.owner}")
        if self.date:
            bits.append(f"(due: {self.date})")
        return " ".join([bits[0], self.text] + bits[1:]).strip() if bits else self.text


@dataclass
class OpenQuestion:
    text: str


@dataclass
class MeetingReport:
    summary: str = ""
    decisions: List[Decision] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    open_questions: List[OpenQuestion] = field(default_factory=list)
    recap: str = ""
    title: str = "Meeting Notes"
    polished: bool = False

    def to_text(self) -> str:
        lines = [self.title, "=" * max(len(self.title), 12), ""]
        lines.append("Summary")
        lines.append("-" * 8)
        lines.append(self.summary or "(no summary)")
        lines.append("")
        lines.append("Decisions")
        lines.append("-" * 8)
        if self.decisions:
            lines.extend(f"* {d.text}" for d in self.decisions)
        else:
            lines.append("(none detected)")
        lines.append("")
        lines.append("Action Items")
        lines.append("-" * 8)
        if self.action_items:
            lines.extend(f"* {a.display()}" for a in self.action_items)
        else:
            lines.append("(none detected)")
        lines.append("")
        lines.append("Open Questions")
        lines.append("-" * 8)
        if self.open_questions:
            lines.extend(f"* {q.text}" for q in self.open_questions)
        else:
            lines.append("(none detected)")
        lines.append("")
        lines.append("Plain-English Recap")
        lines.append("-" * 8)
        lines.append(self.recap or "(no recap)")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", ""]
        lines.append("## Summary")
        lines.append("")
        lines.append(self.summary or "(no summary)")
        lines.append("")
        lines.append("## Decisions")
        lines.append("")
        if self.decisions:
            lines.extend(f"- {d.text}" for d in self.decisions)
        else:
            lines.append("_None detected._")
        lines.append("")
        lines.append("## Action Items")
        lines.append("")
        if self.action_items:
            lines.extend(f"- [ ] {a.display()}" for a in self.action_items)
        else:
            lines.append("_None detected._")
        lines.append("")
        lines.append("## Open Questions")
        lines.append("")
        if self.open_questions:
            lines.extend(f"- {q.text}" for q in self.open_questions)
        else:
            lines.append("_None detected._")
        lines.append("")
        lines.append("## Plain-English Recap")
        lines.append("")
        lines.append(self.recap or "(no recap)")
        lines.append("")
        lines.append("---")
        lines.append("_Generated locally by meeting-notes-summarizer "
                     "(Asdale Dynamics, LLC)._")
        return "\n".join(lines)
