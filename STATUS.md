# STATUS.md — meeting-notes-summarizer

Last updated: 2026-10-25

## What was built

`meeting-notes-summarizer` — a local-first Python 3.11+ CLI that turns meeting
transcripts into a structured report:

- **Summary** (extractive, scored)
- **Decisions**
- **Action items** with owner (`@Name`) and due date when detectable
- **Open questions**
- **Plain-English recap**

Features:

- Input: transcript file argument / `-i`, piped stdin, or interactive paste
  (pasted transcripts are saved to `./transcripts/` so they stay on disk;
  `--no-save` skips that).
- Output: Markdown (default) or plain text (`-f text`), on stdout or written
  via `-o` (refuses to overwrite files that don't look like reports).
- Optional **polish** step: rewrites the two prose sections via any
  OpenAI-compatible chat endpoint. Flags (`--base-url`, `--model`) override a
  TOML config (`./meetingsummarizer.toml` or
  `$XDG_CONFIG_HOME/meetingsummarizer/meetingsummarizer.toml`), which overrides
  defaults (Ollama `http://localhost:11434/v1`, model `llama3.1`).
- **Privacy boundaries:** no API key is ever requested or sent; no
  `Authorization` header is set; by default the polish request contains only
  the two prose sections, not the raw transcript — `--send-transcript` opts in.
- Unicode-safe output; timestamps like `[00:12:34]` are stripped from lines.

## How to run it

```bash
python -m meeting_notes_summarizer examples/sample_transcript.txt
# or, after `pip install .`:
meetingsummarizer transcript.txt -f text -o report.txt

# with polish (Ollama running locally, or any OpenAI-compatible base_url):
python -m meeting_notes_summarizer transcript.txt --polish --model llama3.1
```

Tests:

```bash
python -m pytest
```

## Verification results

- `python -m pytest` — **36 passed** (system Python 3.13 and a clean venv).
- `pip install .` into a fresh venv: `meetingsummarizer --version` works;
  file input, text/markdown rendering, and `-o` export verified.
- Paste (stdin) mode verified, transcript saved to `./transcripts/`
  timestamped, `--no-save` verified.
- `--polish` verified end-to-end against a fake OpenAI-compatible HTTP server
  (real `urllib` POST, not just a monkeypatch): request hit
  `/v1/chat/completions`, carried the model + prose payload, and the polished
  summary/recap replaced the draft in the output. Request log confirmed
  **empty auth headers** and **no raw transcript** without
  `--send-transcript`; with the flag, context lines were present.
- `-o photo.png`-style overwrite into an unrelated file is refused.
- Missing file exits with a clean `error:` message (exit code 2).

## Known gaps / limitations

- Extraction is purely heuristic on the host machine — it will miss
  implicitly delegated tasks and may pull odd snippet sentences into the
  summary for very short transcripts. The LLM polish only rewrites prose; it
  never adds items, so stray speaker labels ("Dana: ") can still appear in
  short summaries.
- Date parsing covers common phrases (weekdays, "by Friday", `10/28`,
  "Oct 28", "end of week"), not arbitrary date grammar.
- Polish parses a fixed `NEW SUMMARY:` / `NEW RECAP:` reply format; a
  non-conforming model reply leaves the draft prose in place rather than
  failing the run.
- `--polish` assumes the endpoint requires no auth (by design). Endpoints
  behind API keys need an auth-injecting proxy in front.
- Only Ollama-style `/v1/chat/completions` (non-streaming) is implemented.
- Windows interactive-paste termination key differs (Ctrl+Z then Enter);
  untested on Windows/CI.

## Project layout

```
meeting_notes_summarizer/   package (cli, parser, summarizer, polish, config, exporter, models)
tests/                      pytest suite (36 tests, endpoint fully mocked)
examples/                   sample transcript
LICENSE                     MIT, "Copyright (c) 2026 Asdale Dynamics, LLC"
README.md                   usage, config, credits
pyproject.toml              package metadata + pytest config
```

Built by Asdale Dynamics, LLC. MIT licensed. No secrets, keys, or personal
data in any file.
