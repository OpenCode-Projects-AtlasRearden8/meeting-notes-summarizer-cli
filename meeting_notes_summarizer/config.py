import os
from dataclasses import dataclass
from typing import Optional

try:  # Python 3.11+
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.1"
DEFAULT_TIMEOUT = 60.0
DEFAULT_TEMPERATURE = 0.3

CONFIG_NAME = "meetingsummarizer.toml"


def user_config_path() -> str:
    config_home = os.environ.get(
        "XDG_CONFIG_HOME",
        os.path.expanduser(os.path.join("~", ".config")),
    )
    return os.path.join(config_home, "meetingsummarizer", CONFIG_NAME)


@dataclass
class Config:
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    timeout: float = DEFAULT_TIMEOUT


def load_config(path: Optional[str] = None) -> Config:
    cfg = Config()
    candidates = []
    if path:
        candidates.append(path)
    candidates.append(os.path.join(".", CONFIG_NAME))
    candidates.append(user_config_path())
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            data = _read_toml(candidate)
            for key in ("base_url", "model", "temperature", "timeout"):
                if key in data:
                    setattr(cfg, key, data[key])
            break
    return _validate(cfg)


def _read_toml(path: str) -> dict:
    if tomllib is None:  # pragma: no cover
        raise RuntimeError("Python 3.11+ required to read TOML config files")
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    return data.get("polish", data)


def _validate(cfg: Config) -> Config:
    if not str(cfg.base_url).startswith(("http://", "https://")):
        raise SystemExit(f"Config error: base_url must start with http:// or https:// (got {cfg.base_url!r})")
    if not cfg.model:
        raise SystemExit("Config error: model must not be empty")
    try:
        cfg.temperature = float(cfg.temperature)
        cfg.timeout = float(cfg.timeout)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"Config error: temperature/timeout must be numbers ({exc})")
    return cfg
