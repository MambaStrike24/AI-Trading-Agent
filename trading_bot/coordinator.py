from __future__ import annotations

"""Simple coordinator for aggregating structured agent responses.

Each agent returns a structured JSON object containing a ``summary``, ``reasoning``,
and one or more role-specific fields. This coordinator orchestrates a run for a
given symbol and date by executing each agent and collecting their outputs.

The coordinator builds a ``strategy_summary`` that maps each agent's name to
its JSON response, and returns a full conversation history for downstream
analysis or strategy generation.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence
import yfinance as yf
import pandas as pd


@dataclass
class Coordinator:
    """Coordinate execution of role-specific agents."""

    agents: Sequence[Any]

    def run(self, symbol: str, date: str) -> Dict[str, Any]:
        """Execute each agent for the given symbol and date.

        Each agent is passed the symbol, date (as of which it should reason),
        and the running conversation history.

        Returns
        -------
        Dict[str, Any]
            {
                "symbol": ...,
                "date": ...,
                "conversation": [...],
                "strategy_summary": {agent_name: {...}, ...}
            }
        """
        history: List[Dict[str, Any]] = []
        summary_obj: Dict[str, Any] = {}

        # First loop: run all agents except StrategyTypeAgent and StrategyExecutorAgent
        # First loop: run all agents except the planning chain
        skip_names = {
            "StrategyTypeAgent",
            "IndicatorSelectionAgent",
            "StrategyPlannerAgent",
        }
        for agent in self.agents:
            if agent.name in skip_names:
                continue
            
            response = agent.respond(symbol=symbol, date=date)
            agent_name = getattr(agent, "name", agent.__class__.__name__)
            entry = {"agent": agent_name, **response}
            history.append(entry)
            summary_obj[agent_name] = response

        # Inject OHLCV data from yfinance as "DataFeed"
        end = pd.to_datetime(date)
        start = end - pd.Timedelta(days=7)
        df = yf.download(
            symbol,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval="1h",
            auto_adjust=True,
            progress=False,
        )
        if df.empty:
            ohlcv_data = {"error": "no data"}
        else:
            df = df.tail(48)  # last 2 days of hourly candles
            df = df[["Open", "High", "Low", "Close", "Volume"]].round(2)
            ohlcv_data = df.reset_index().to_dict(orient="records")

        datafeed_entry = {
            "agent": "DataFeed",
            "symbol": symbol,
            "date": date,
            "ohlcv": ohlcv_data,
        }
        history.append(datafeed_entry)

        # Run StrategyTypeAgent
        strategy_type_agent = next((a for a in self.agents if a.name == "StrategyTypeAgent"), None)
        if strategy_type_agent:
            response = strategy_type_agent.respond(symbol=symbol, date=date, history=history)
            history.append(response)
            summary_obj[response["agent"]] = response

        # Run IndicatorSelectionAgent
        indicator_selector = next((a for a in self.agents if a.name == "IndicatorSelectionAgent"), None)
        if indicator_selector:
            response = indicator_selector.respond(symbol=symbol, date=date, history=history)
            history.append(response)
            summary_obj[response["agent"]] = response

            # ---- Force-include ATR so it is always available ----
            from trading_bot.indicators.registry import INDICATOR_REGISTRY
            indicators_used = list(response.get("indicators_used", []))  # copy

            def ensure_indicator(name: str, fallback_params: dict | None = None):
                if any(i.get("name") == name for i in indicators_used):
                    return
                if name in INDICATOR_REGISTRY:
                    params = INDICATOR_REGISTRY[name].get("params", {}) or {}
                    if fallback_params:
                        params = {**params, **fallback_params}
                    indicators_used.append({"name": name, "params": params})

            # Always include ATR (for stops/trailing stops/derivations)
            ensure_indicator("ATR")
            
            # Compute actual indicator values immediately after selection
            try:
                from trading_bot.indicators.compute import compute_selected_indicators
                indicators_used = response.get("indicators_used", [])
                indicator_values = compute_selected_indicators(symbol, date, indicators_used)
            except Exception as e:
                indicator_values = {"error": str(e)}

            indicator_data_entry = {
                "agent": "IndicatorValues",
                "symbol": symbol,
                "date": date,
                "indicators": indicators_used,
                "values": indicator_values
            }
            history.append(indicator_data_entry)
            summary_obj[indicator_data_entry["agent"]] = indicator_data_entry

        strategy_planner = next((a for a in self.agents if a.name == "StrategyPlannerAgent"), None)
        if strategy_planner:
            response = strategy_planner.respond(symbol=symbol, date=date, history=history)
            history.append(response)
            summary_obj[response["agent"]] = response

        return {
            "symbol": symbol,
            "date": date.isoformat(),
            "conversation": history,
            "strategy_summary": summary_obj,
        }
