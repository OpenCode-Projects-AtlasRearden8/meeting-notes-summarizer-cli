import argparse
import os
import sys

from . import __version__
from .config import DEFAULT_BASE_URL, DEFAULT_MODEL, load_config
from .exporter import save_report
from .parser import _load_text, slugify, suggest_title, timestamp
from .polish import polish_report
from .summarizer import summarize


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="meetingsummarizer",
        description=(
            "Local-first meeting transcript summarizer. Reads a transcript "
            "from a file or pasted stdin text, builds a heuristic report "
            "(summary, decisions, action items, open questions, plain-English "
            "recap), and optionally polishes the prose via an OpenAI-compatible "
            "endpoint you point it at. Built by Asdale Dynamics, LLC."
        ),
        epilog=(
            "Privacy: the transcript stays on disk. The polish step only sends "
            "the two prose sections and never an API key."
        ),
    )
    parser.add_argument("file", nargs="?", default=None,
                        help="Path to a transcript file (.txt/.md). Omit to read pasted text from stdin.")
    parser.add_argument("-i", "--input", default=None, help="Alternate way to pass the transcript file.")
    parser.add_argument("-f", "--format", choices=("md", "text"), default="md",
                        help="Output format (default: md).")
    parser.add_argument("-o", "--out", default=None,
                        help="Write the report to this file instead of stdout.")
    parser.add_argument("--polish", action="store_true",
                        help="Polish summary/recap via the configured OpenAI-compatible endpoint.")
    parser.add_argument("--base-url", default=None,
                        help=f"Endpoint base URL (default: {DEFAULT_BASE_URL}; config file also works).")
    parser.add_argument("--model", default=None,
                        help=f"Model name to request (default: {DEFAULT_MODEL}; config file also works).")
    parser.add_argument("--config", default=None,
                        help="Path to a TOML config file (default: ./meetingsummarizer.toml or "
                             "$XDG_CONFIG_HOME/meetingsummarizer/meetingsummarizer.toml).")
    parser.add_argument("--send-transcript", action="store_true",
                        help="Include recent transcript lines in the polish request "
                             "(off by default: only the two prose sections are sent).")
    parser.add_argument("--no-save", action="store_true",
                        help="Do not save a copy of pasted transcripts to ./transcripts/.")
    parser.add_argument("--title", default=None, help="Override the report title.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    path = args.input or args.file
    if path and not os.path.isfile(path):
        print(f"error: file not found: {path}", file=sys.stderr)
        raise SystemExit(2)

    if path:
        text = _load_text(None, path)
        saved_as = None
    else:
        if sys.stdin.isatty() and path is None:
            print("Paste your transcript, then press Ctrl+D (Ctrl+Z then Enter on Windows):",
                  file=sys.stderr)
        text = sys.stdin.read()
        saved_as = None
        if not args.no_save and text.strip():
            slug = slugify(suggest_title(text))
            folder = os.path.join(".", "transcripts")
            os.makedirs(folder, exist_ok=True)
            name = f"{timestamp()}-{slug}.txt"
            # never let a transcript write clobber an existing file
            counter = 1
            while os.path.exists(os.path.join(folder, name)):
                counter += 1
                name = f"{timestamp()}-{slug}-{counter}.txt"
            with open(os.path.join(folder, name), "w", encoding="utf-8") as fh:
                fh.write(text)
            saved_as = os.path.join(folder, name)

    if not text.strip():
        print("error: no transcript text was provided", file=sys.stderr)
        return 2

    report = summarize(text)
    if args.title:
        report.title = args.title

    if args.polish:
        cfg = load_config(args.config)
        base_url = args.base_url or cfg.base_url
        model = args.model or cfg.model
        report = polish_report(report, text, base_url=base_url, model=model,
                               temperature=cfg.temperature, timeout=cfg.timeout,
                               send_transcript=args.send_transcript)

    rendered = report.to_markdown() if args.format == "md" else report.to_text()

    if args.out:
        save_report(args.out, rendered)
        print(f"Wrote report to {args.out}", file=sys.stderr)
    else:
        print(rendered)

    if saved_as:
        print(f"Transcript saved on disk: {saved_as}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
