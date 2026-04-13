"""Utilities to open generated reports."""

import webbrowser
from pathlib import Path


class ReportOpener:
    """Single responsibility: open a report file with the default OS handler."""

    def open_file(self, path: str) -> None:
        target = Path(path).resolve()
        webbrowser.open(target.as_uri())
