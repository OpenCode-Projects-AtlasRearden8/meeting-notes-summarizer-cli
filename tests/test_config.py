import os

import pytest

from meeting_notes_summarizer.config import load_config


def _write(tmp_path, name="meetingsummarizer.toml", body=""):
    p = tmp_path / name
    p.write_text(body)
    return str(p)


def test_config_defaults_when_no_file(tmp_path):
    cfg = load_config(_write(tmp_path, body="[polish]\ntemperature = 0.9\n"))
    # file exists but only has temperature: other defaults stay
    assert cfg.temperature == 0.9
    assert cfg.base_url


def test_config_reads_polish_table(tmp_path):
    path = _write(
        tmp_path,
        body=(
            '[polish]\nbase_url = "http://localhost:1234/v1"\nmodel = "mistral"\n'
            'temperature = 0.1\ntimeout = 12.5\n'
        ),
    )
    cfg = load_config(path)
    assert cfg.base_url == "http://localhost:1234/v1"
    assert cfg.model == "mistral"
    assert cfg.temperature == 0.1
    assert cfg.timeout == 12.5


def test_config_rejects_bad_scheme(tmp_path):
    path = _write(tmp_path, body='[polish]\nbase_url = "ftp://example"\n')
    with pytest.raises(SystemExit):
        load_config(path)


def test_config_rejects_empty_model(tmp_path):
    path = _write(tmp_path, body='[polish]\nmodel = ""\n')
    with pytest.raises(SystemExit):
        load_config(path)


def test_local_file_wins_over_user_config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    os.makedirs(tmp_path / "xdg" / "meetingsummarizer", exist_ok=True)
    (tmp_path / "xdg" / "meetingsummarizer" / "meetingsummarizer.toml").write_text(
        '[polish]\nmodel = "user-model"\n'
    )
    user_cfg = load_config(None)
    assert user_cfg.model == "user-model"

    explicit = _write(tmp_path, body='[polish]\nmodel = "local-model"\n')
    assert load_config(explicit).model == "local-model"
