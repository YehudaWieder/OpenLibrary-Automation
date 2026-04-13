from __future__ import annotations

import csv
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

logger = logging.getLogger(__name__)

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

DEFAULTS: Dict[str, Any] = {
    "BASE_URL": "https://openlibrary.org",
    "HEADLESS": False,
    "BROWSER": "chromium",
    "TIMEOUT": 30000,
    "TEST_DATA_PATH": "data/test_data.json",
    "EMAIL_INPUT": None,
    "USERNAME_INPUT": None,
    "PASSWORD_INPUT": None,
}

SENSITIVE_KEYS = {"EMAIL_INPUT", "USERNAME_INPUT", "PASSWORD_INPUT"}

CONFIG_CANDIDATE_PRIORITY: List[str] = [
    ".json",
    ".csv",
    ".yaml",
    ".yml",
]

CONFIG_CANDIDATES: List[Path] = [Path(f"config/config{ext}") for ext in CONFIG_CANDIDATE_PRIORITY]


def _parse_scalar(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value

    if isinstance(value, (int, float)):
        return value

    text = str(value).strip()
    lowered = text.lower()

    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False

    if text.isdigit():
        return int(text)

    try:
        if "." in text:
            return float(text)
    except ValueError:
        pass

    return text


def _load_json(file_path: Path) -> Any:
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_yaml(file_path: Path) -> Any:
    if yaml is None:
        raise ImportError(
            "PyYAML is required to load YAML config files. Install it with 'pip install PyYAML'."
        )

    with file_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_csv(file_path: Path) -> Any:
    with file_path.open("r", encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.reader(handle) if row]

    if not rows:
        return {}

    if len(rows) == 1:
        # A single row can be interpreted as headers with no data.
        return {}

    # If every row is two columns, treat as key/value pairs.
    if all(len(row) == 2 for row in rows):
        parsed: Dict[str, Any] = {}
        for key, value in rows:
            parsed[key.strip()] = _parse_scalar(value)
        return parsed

    # Fall back to header-based row parsing.
    header, *data_rows = rows
    output: List[Dict[str, Any]] = []
    for row in data_rows:
        row_data: Dict[str, Any] = {}
        for index, key in enumerate(header):
            value = row[index] if index < len(row) else ""
            row_data[key.strip()] = _parse_scalar(value)
        output.append(row_data)

    if len(output) == 1:
        return output[0]

    return output


def load_config_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    path = Path(file_path).expanduser()
    if not path.exists():
        logger.warning("Config file not found at %s", path)
        return {}

    extension = path.suffix.lower()
    raw: Any

    if extension == ".json":
        raw = _load_json(path)
    elif extension in {".yaml", ".yml"}:
        raw = _load_yaml(path)
    elif extension == ".csv":
        raw = _load_csv(path)
    else:
        raise ValueError(f"Unsupported config file extension: {extension}")

    if isinstance(raw, list):
        # If file contains a list of dictionaries, use the first item as config.
        return raw[0] if raw else {}
    if isinstance(raw, dict):
        return {key: _parse_scalar(value) for key, value in raw.items()}

    logger.warning("Unexpected config file type for %s: %s", path, type(raw))
    return {}


def _discover_config_file() -> Optional[Path]:
    env_config = os.getenv("CONFIG_PATH")
    if env_config:
        candidate = Path(env_config).expanduser()
        if candidate.exists():
            return candidate
        logger.warning("CONFIG_PATH points to a missing file: %s", candidate)

    for candidate in CONFIG_CANDIDATES:
        extension = candidate.suffix.lower()
        if extension in {".yaml", ".yml"} and yaml is None:
            continue
        if candidate.exists():
            return candidate

    logger.info("No configuration file found in config directory. Falling back to defaults and environment variables.")
    return None


def _merge_values(config_values: Dict[str, Any], env_values: Dict[str, Optional[str]]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for key, default in DEFAULTS.items():
        if key in SENSITIVE_KEYS:
            env_value = env_values.get(key)
            merged[key] = _parse_scalar(env_value) if env_value is not None else default
            continue

        if key in config_values and config_values[key] is not None:
            merged[key] = config_values[key]
            continue

        env_value = env_values.get(key)
        if env_value is not None:
            merged[key] = _parse_scalar(env_value)
            continue

        merged[key] = default

    return merged


@dataclass(frozen=True)
class Config:
    BASE_URL: str = DEFAULTS["BASE_URL"]
    HEADLESS: bool = DEFAULTS["HEADLESS"]
    BROWSER: str = DEFAULTS["BROWSER"]
    TIMEOUT: int = DEFAULTS["TIMEOUT"]
    TEST_DATA_PATH: str = DEFAULTS["TEST_DATA_PATH"]
    EMAIL_INPUT: Optional[str] = DEFAULTS["EMAIL_INPUT"]
    USERNAME_INPUT: Optional[str] = DEFAULTS["USERNAME_INPUT"]
    PASSWORD_INPUT: Optional[str] = DEFAULTS["PASSWORD_INPUT"]

    @classmethod
    def load(cls) -> "Config":
        config_file = _discover_config_file()
        config_data = load_config_file(config_file) if config_file else {}
        env_data = {key: os.getenv(key) for key in DEFAULTS}
        merged = _merge_values(config_data, env_data)
        return cls(
            BASE_URL=merged["BASE_URL"],
            HEADLESS=merged["HEADLESS"],
            BROWSER=merged["BROWSER"],
            TIMEOUT=int(merged["TIMEOUT"]),
            TEST_DATA_PATH=str(merged["TEST_DATA_PATH"]),
            EMAIL_INPUT=merged["EMAIL_INPUT"],
            USERNAME_INPUT=merged["USERNAME_INPUT"],
            PASSWORD_INPUT=merged["PASSWORD_INPUT"],
        )


CONFIG = Config.load()
