"""Test data loader for data-driven testing."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .data_loader import load_data


class TestDataLoader:
    """
    Loader for test data from JSON, YAML, or CSV files.
    """

    def __init__(self, data_file_path: str) -> None:
        self.data_file_path: str = data_file_path
        self.test_data: List[Dict[str, Any]] = []

    def load_test_data(self) -> List[Dict[str, Any]]:
        """Load test data from a supported external file format."""
        raw = load_data(self.data_file_path)
        if isinstance(raw, dict):
            self.test_data = [raw]
        elif isinstance(raw, list):
            self.test_data = raw
        else:
            raise TypeError("Test data must be a JSON/YAML dict or CSV/JSON list of dicts")

        return self.test_data

    def get_test_case(self, test_case_id: str) -> Optional[Dict[str, Any]]:
        """Return a single test case by its unique identifier."""
        return next(
            (item for item in self.test_data if item.get("test_id") == test_case_id),
            None,
        )

    def get_all_test_cases(self) -> List[Dict[str, Any]]:
        """Return all loaded test cases."""
        return self.test_data

    def validate_test_data_schema(self, required_fields: List[str]) -> bool:
        """Validate that each loaded test case contains all required fields."""
        return all(
            all(field in item for field in required_fields) for item in self.test_data
        )

    def get_parameter_combinations(self) -> List[Dict[str, Any]]:
        """Return a list of parameter dictionaries for parametrized tests."""
        return self.test_data
