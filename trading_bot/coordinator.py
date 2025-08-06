from __future__ import annotations

"""Simple coordinator for aggregating structured agent responses.

The previous version of the project implemented a conversation style interface
where each agent returned a free-form message.  For the new iteration agents
return structured JSON objects containing a ``summary`` and ``reasoning``.  The
coordinator simply gathers these results and builds a high level
``strategy_summary`` by concatenating the individual summaries.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence


@dataclass
class Coordinator:
    """Coordinate dialogue between role specific agents."""

    agents: Sequence[Any]

    def run(self, symbol: str) -> Dict[str, Any]:
        """Execute each agent and collate their structured outputs."""

        history: List[Dict[str, Any]] = []

        for agent in self.agents:
            response: Dict[str, Any] = agent.respond(symbol, history)
            agent_name = getattr(agent, "name", agent.__class__.__name__)
            entry = {"agent": agent_name, **response}
            history.append(entry)

        summary = " ".join(item.get("summary", "") for item in history).strip()
        return {"symbol": symbol, "conversation": history, "strategy_summary": summary}


__all__ = ["Coordinator"]
