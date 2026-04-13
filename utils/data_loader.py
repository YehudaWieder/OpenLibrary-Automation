import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".json", ".yaml", ".yml", ".csv"}


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


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        logger.error("PyYAML is required to load YAML files: %s", exc)
        raise

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_csv(path: Path) -> Any:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.reader(handle) if row]

    if not rows:
        return {}

    if len(rows) == 1:
        return {}

    if all(len(row) == 2 for row in rows):
        return {
            row[0].strip(): _parse_scalar(row[1])
            for row in rows
        }

    header, *data_rows = rows
    output: List[Dict[str, Any]] = []

    for row in data_rows:
        output.append({header[i].strip(): _parse_scalar(row[i]) if i < len(row) else None for i in range(len(header))})

    return output if len(output) > 1 else output[0]


def load_data(file_path: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    path = Path(file_path).expanduser()
    if not path.exists():
        logger.error("Data file not found at: %s", path)
        raise FileNotFoundError(f"Missing data file: {path}")

    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported data file extension: {extension}")

    if extension == ".json":
        raw_data = _load_json(path)
    elif extension in {".yaml", ".yml"}:
        raw_data = _load_yaml(path)
    else:
        raw_data = _load_csv(path)

    logger.info("Data loaded from %s", path)
    return raw_data


def load_test_data(file_path: str, record_index: int = 0) -> Dict[str, Any]:
    raw_data = load_data(file_path)

    if isinstance(raw_data, dict):
        return raw_data

    if isinstance(raw_data, list):
        if not raw_data:
            raise ValueError(f"No records found in test data file: {file_path}")
        if record_index < 0 or record_index >= len(raw_data):
            raise IndexError(
                f"Test data index {record_index} is out of range for file: {file_path}"
            )
        return raw_data[record_index]

    raise TypeError("Test data must be a JSON/YAML dict or a CSV/JSON list of dicts")
