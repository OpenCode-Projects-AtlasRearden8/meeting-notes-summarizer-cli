# meeting-notes-summarizer

A local-first command-line tool that turns meeting transcripts into a clean
report: short **summary**, **decisions**, **action items with owners and
dates**, **open questions**, and a **plain-English recap**.

Built by **Asdale Dynamics, LLC** — AI explained like a friend would:
plain English, step by step, never condescending.

## Why local-first

- Your transcript stays **on disk**. Pasted transcripts are saved to
  `./transcripts/` so you always have a copy (use `--no-save` to skip).
- Everything else — parsing, scoring, summarizing — runs **on your machine**
  using only the Python standard library. No cloud, no accounts.
- The optional "polish" step talks to an **OpenAI-compatible endpoint that you
  point at** (by default Ollama on `http://localhost:11434/v1`). It never
  requires or sends an API key, and by default it sends **only the two prose
  sections** (summary + recap), not your raw transcript. Use
  `--send-transcript` if you deliberately want context lines included.

## Install

Python 3.11+ required. No third-party runtime dependencies.

```bash
python -m meeting_notes_summarizer --help
```

Or install as a command (`meetingsummarizer`):

```bash
pip install .
```

## Run

```bash
# from a transcript file, Markdown report on screen
python -m meeting_notes_summarizer examples/sample_transcript.txt

# paste a transcript interactively (finish with Ctrl+D; Windows: Ctrl+Z then Enter)
python -m meeting_notes_summarizer

# pipe a transcript in
cat transcript.txt | python -m meeting_notes_summarizer -i

# plain text instead of Markdown, saved to a file
python -m meeting_notes_summarizer transcript.txt -f text -o report.txt

# copy a custom title into the report
python -m meeting_notes_summarizer transcript.txt --title "Weekly Sync"
```

### Optional: LLM polish

Polish rewrites the summary and recap so they read a little friendlier. It is
**opt-in** and works with any OpenAI-compatible chat endpoint:

```bash
# default: Ollama on localhost:11434/v1 with model llama3.1
ollama run llama3.1 --help  # make sure Ollama is running locally first
python -m meeting_notes_summarizer transcript.txt --polish

# any base_url/model via flags
python -m meeting_notes_summarizer transcript.txt --polish \
  --base-url http://localhost:1234/v1 --model mistral
```

Notes:

- No API key is ever requested or transmitted. If your endpoint needs a key,
  put auth in front of it yourself; this tool only speaks plain HTTP.
- The polish request contains the two prose sections plus a prompt. It does
  not contain the raw transcript unless you pass `--send-transcript`.

### Configuration file

Flags win over config; config wins over defaults. Create a
`meetingsummarizer.toml` in the current directory, or at
`$XDG_CONFIG_HOME/meetingsummarizer/meetingsummarizer.toml`:

```toml
[polish]
base_url = "http://localhost:11434/v1"   # default
model = "llama3.1"                       # default
temperature = 0.3
timeout = 60.0
```

## Output example

```markdown
# Weekly Sync

## Summary
...

## Decisions
- We decided to ship the three-step version instead of the wizard.

## Action Items
- [ ] @Marcus (due: by Friday) wire up the progress bar

## Open Questions
- What should we do about users who abandon step 2?

## Plain-English Recap
...
```

## Development

```bash
python -m pytest          # run the test suite
python -m venv .venv && source .venv/bin/activate && pip install . pytest
```

## Who makes this

**Asdale Dynamics, LLC** (Dylan Asdale). Beginner-friendly AI manuals,
local-first tools, and small-business helpers at
[dylanasdale.github.io](https://dylanasdale.github.io) and in
*The Massive AI Manual*.

## License

MIT — see [LICENSE](LICENSE). `Copyright (c) 2026 Asdale Dynamics, LLC`
