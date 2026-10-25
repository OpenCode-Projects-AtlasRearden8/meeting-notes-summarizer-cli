import json


def save_report(path: str, rendered: str) -> None:
    """Write a report, refusing to clobber anything that is not a report file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            existing = fh.read()
        if existing and "# " not in existing and "Summary" not in existing:
            raise FileExistsError(
                f"refusing to overwrite non-report file: {path} (use --out with a new name)"
            )
    except FileNotFoundError:
        pass
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(rendered + "\n")


def read_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)
