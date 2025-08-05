"""Minimal pipeline orchestrating role agents via the Coordinator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .coordinator import Coordinator


@dataclass
class Pipeline:
    """Pipeline delegating orchestration to :class:`Coordinator`."""

    coordinator: Coordinator

    def run(self, symbol: str) -> Dict[str, Any]:
        """Execute the coordinator for ``symbol`` and return its output."""
        return self.coordinator.run(symbol)


__all__ = ["Pipeline"]
