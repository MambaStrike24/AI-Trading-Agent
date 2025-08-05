from __future__ import annotations

"""Simple conversation coordinator for multiple role agents.

The :class:`Coordinator` orchestrates a sequential conversation between a list
of agents.  Each agent receives the conversation history so far and may return
both a message and an optional follow-up question.  The coordinator aggregates
these exchanges and exposes the full conversation along with any questions and
the final decision.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence


@dataclass
class Coordinator:
    """Coordinate dialogue between role specific agents."""

    agents: Sequence[Any]

    def run(self, symbol: str) -> Dict[str, Any]:
        """Run a conversation between all agents.

        Parameters
        ----------
        symbol:
            The market symbol the agents should discuss.
        Returns
        -------
        dict
            Dictionary containing the conversation history, any follow-up
            questions raised by agents and the final decision produced by the
            last agent.
        """
        history: List[Dict[str, str]] = []
        follow_ups: List[Dict[str, str]] = []

        for agent in self.agents:
            response: Dict[str, str] = agent.respond(symbol, history)
            agent_name = getattr(agent, "name", agent.__class__.__name__)
            message = response.get("message", "")
            history.append({"agent": agent_name, "message": message})
            question = response.get("question")
            if question:
                follow_ups.append({"agent": agent_name, "question": question})

        final_decision = history[-1]["message"] if history else ""
        return {
            "symbol": symbol,
            "conversation": history,
            "follow_ups": follow_ups,
            "final_decision": final_decision,
        }


__all__ = ["Coordinator"]
