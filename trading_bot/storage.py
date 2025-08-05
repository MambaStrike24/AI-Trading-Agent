from __future__ import annotations

"""Simple JSON storage helpers for persisting bot outputs.

The real project might use a database, but for unit tests and lightweight
usage we write each record to a ``data/`` directory organised by symbol.  This
module provides minimal ``save`` and ``load`` helpers.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import json


@dataclass
class JSONStorage:
    """Persist dictionaries as JSON files on disk."""

    base_dir: Path | str = Path("data")

    def __post_init__(self) -> None:
        self.base_dir = Path(self.base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, category: str, symbol: str, date_str: str) -> Path:
        symbol_dir = self.base_dir / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        return symbol_dir / f"{date_str}_{category}.json"

    def save(self, category: str, symbol: str, date_str: str, data: Dict[str, Any]) -> Path:
        """Write ``data`` to disk and return the file path."""
        path = self._path(category, symbol, date_str)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        return path

    def load(self, category: str, symbol: str, date_str: str) -> Dict[str, Any]:
        """Load and return data previously saved with :meth:`save`."""
        path = self._path(category, symbol, date_str)
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)


__all__ = ["JSONStorage"]
