import os

import pytest

import meeting_notes_summarizer.cli as cli
from meeting_notes_summarizer.cli import main


TRANSCRIPT = """\
Dana: We decided to go with the three-step flow.
Marcus: I will wire the progress bar by Friday.
Priya: What about abandoned carts?
"""


@pytest.fixture(autouse=True)
def _clean_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield


def _stdin(monkeypatch, text):
    import io

    fake = io.StringIO(text)
    monkeypatch.setattr("sys.stdin", fake)
    return fake


def test_stdin_paste_and_transcript_saved_to_disk(capsys, monkeypatch):
    _stdin(monkeypatch, TRANSCRIPT)
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "Action Items" in out or "Action items" in out
    saved = list(os.scandir("transcripts"))
    assert len(saved) == 1
    assert open(saved[0].path).read().strip() == TRANSCRIPT.strip()


def test_no_save_skips_transcript_disk_writes(capsys, monkeypatch):
    _stdin(monkeypatch, TRANSCRIPT)
    main(["--no-save"])
    assert not os.path.exists("transcripts")


def test_prefix_transcript_file_flag(capsys):
    path = "meeting.txt"
    with open(path, "w") as fh:
        fh.write(TRANSCRIPT)
    assert main([path]) == 0
    assert "Dana" in capsys.readouterr().out
    assert not os.path.exists("transcripts")


def test_missing_file_is_clean_error(capsys):
    with pytest.raises(SystemExit):
        main(["nope-missing.txt"])


def test_out_writes_markdown_file(capsys, monkeypatch):
    _stdin(monkeypatch, TRANSCRIPT)
    main(["-o", "report.md"])
    body = open("report.md").read()
    assert body.startswith("# ")
    err = capsys.readouterr().err
    assert "Wrote report" in err


def test_text_format(capsys, monkeypatch):
    _stdin(monkeypatch, TRANSCRIPT)
    main(["-f", "text"])
    out = capsys.readouterr().out
    assert "===" in out
    assert "##" not in out


def test_polish_flag_uses_mocked_endpoint(capsys, monkeypatch):
    _stdin(monkeypatch, TRANSCRIPT)

    def fake_polish(report, transcript_text, base_url, model, temperature, timeout,
                    send_transcript=False):
        assert base_url == "http://localhost:9999/v1"
        assert model == "tiny-model"
        report.summary = "Polished summary."
        report.polished = True
        return report

    monkeypatch.setattr("meeting_notes_summarizer.cli.polish_report", fake_polish)
    main(["--polish", "--base-url", "http://localhost:9999/v1", "--model", "tiny-model"])
    out = capsys.readouterr().out
    assert "Polished summary." in out


def test_polish_error_surfaced_from_bad_endpoint(monkeypatch):
    _stdin(monkeypatch, TRANSCRIPT)

    def exploding_polish(*args, **kwargs):
        raise ConnectionError("endpoint down")

    monkeypatch.setattr("meeting_notes_summarizer.cli.polish_report", exploding_polish)
    with pytest.raises(ConnectionError):
        main(["--polish"])


def test_out_refuses_to_clobber_unrelated_file(capsys, monkeypatch):
    with open("photo.png", "w") as fh:
        fh.write("pretend binary")
    _stdin(monkeypatch, TRANSCRIPT)
    with pytest.raises(Exception):
        main(["-o", "photo.png"])
    # transcript still saved, file untouched
    assert open("photo.png").read() == "pretend binary"


def test_version_flag(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
