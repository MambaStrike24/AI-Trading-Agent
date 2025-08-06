from __future__ import annotations

"""Very small portfolio tracking utility.

The :class:`Portfolio` class stores opened and closed positions allowing the
system to track PnL over time.  It is deliberately lightweight but mirrors the
fields described in the project specification.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Position:
    symbol: str
    size: float
    entry_price: float
    entry_time: datetime
    strategy_ref: str
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None

    def is_open(self) -> bool:  # pragma: no cover - trivial
        return self.exit_price is None

    def pnl(self) -> Optional[float]:
        if self.exit_price is None:
            return None
        return (self.exit_price - self.entry_price) * self.size


class Portfolio:
    """Track open and closed positions."""

    def __init__(self) -> None:
        self.positions: List[Position] = []

    # Opening and closing -------------------------------------------------
    def open_position(
        self,
        symbol: str,
        size: float,
        entry_price: float,
        entry_time: datetime,
        strategy_ref: str,
    ) -> Position:
        pos = Position(symbol, size, entry_price, entry_time, strategy_ref)
        self.positions.append(pos)
        return pos

    def close_position(self, position: Position, exit_price: float, exit_time: datetime) -> Position:
        position.exit_price = exit_price
        position.exit_time = exit_time
        return position

    # Query helpers -------------------------------------------------------
    def open_positions(self) -> List[Position]:
        return [p for p in self.positions if p.is_open()]

    def closed_positions(self) -> List[Position]:
        return [p for p in self.positions if not p.is_open()]

    def total_pnl(self) -> float:
        """Return the realised profit and loss of all closed positions."""
        return sum(p.pnl() or 0.0 for p in self.closed_positions())


__all__ = ["Portfolio", "Position"]
