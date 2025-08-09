"""Specialised agents powered by a lightweight local language model.

Each agent issues a structured prompt instructing the model to return JSON with
the fields ``summary`` and ``reasoning`` plus a role specific field.  The JSON is
parsed and surfaced to the caller as a normal dictionary which makes downstream
processing straightforward.
"""

from __future__ import annotations

import json
from typing import Any, Dict
import re 
import yfinance as yf
from datetime import timedelta
import pandas as pd 
from typing import Any, Dict
from trading_bot.indicators.registry import INDICATOR_REGISTRY
import re 
from ..storage import JSONStorage

_PLANNER_STORAGE = JSONStorage(base_dir="data")

def _stringify_dates(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _stringify_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_stringify_dates(v) for v in obj]
    elif hasattr(obj, "isoformat"):  # Catches datetime.date and datetime.datetime
        return obj.isoformat()
    else:
        return obj
    
def _safe_json(obj):
    if isinstance(obj, dict):
        return {str(k): _safe_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_safe_json(v) for v in obj]
    elif hasattr(obj, "isoformat"):
        return obj.isoformat()
    elif isinstance(obj, (set, tuple)):
        return [_safe_json(v) for v in obj]
    else:
        return obj
    
class _BaseAgent:
    """Common helper to query the LLM and parse JSON responses."""

    name: str
    prompt_template: str

    def _query(self, symbol: str, date: str) -> Dict[str, Any]:
        try:
            from trading_bot import openai_client
        except Exception as exc:
            raise ImportError("openai_client must be available to use agents") from exc

        prompt = self.prompt_template.format(symbol=symbol, date=date)
        prompt += " Respond ONLY in JSON using the structure described above."
        raw = openai_client.call_llm(prompt)
        # print(f"\n\n--- RAW LLM RESPONSE for {symbol} ({self.name}) ---\n{raw}\n")

        # Parse JSON
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            data = json.loads(match.group(0)) if match else None

        if not isinstance(data, dict):
            return {
                "agent": self.name,
                "symbol": symbol,
                # "date": date,
                "date": str(date),
                "summary": "",
                "reasoning": "",
                "details": {"error": "invalid json"},
            }

        # Wrap role-specific fields in "details"
        reserved_keys = {"summary", "reasoning"}
        details = {k: v for k, v in data.items() if k not in reserved_keys}

        return _stringify_dates({
            "agent": self.name,
            "symbol": symbol,
            "date": str(date),
            "summary": data.get("summary", ""),
            "reasoning": data.get("reasoning", ""),
            "details": details,
        })

class MarketAnalystAgent(_BaseAgent):
    """Generate market analysis for a ticker symbol."""

    name = "MarketAnalystAgent"

    def __init__(self, prompt_template: str | None = None) -> None:
        self.prompt_template = (
            prompt_template or 
            "You are a financial market analyst. Today's date is {date}. "
            "Assess how macroeconomic trends and company-level valuation factors available strictly before {date} influence investor sentiment and the investment outlook for the stock {symbol}. "
            "Do NOT reference or speculate on any data from {date} or later. "
            "Focus your analysis on factors like interest rates, inflation, GDP growth, unemployment, bond yields, currency trends, sector strength, and valuation metrics (e.g., P/E, earnings growth). "
            "Do NOT use technical indicators — another analyst will handle that.\n"
            "Respond ONLY in JSON with the following keys:\n"
            "- summary: A one-line macro/fundamental outlook (e.g., 'Improving macro backdrop supports bullish sentiment').\n"
            "- reasoning: A 2–4 sentence explanation referencing macroeconomic and valuation signals.\n"
            "- macro_factors: A list of key macro or valuation drivers affecting the stock (e.g., [{{'factor': 'Interest rates', 'effect': 'Falling yields support growth stocks'}}])."
        )

    def analyze(self, symbol: str, date: str) -> Dict[str, Any]:
        """Return a structured market analysis."""
        # return self._query(symbol, "macro_factors", date)
        return self._query(symbol, date)

    def respond(self, symbol: str, date: str, history: Any | None = None) -> Dict[str, Any]:
        return self.analyze(symbol, date)


# class RiskAdvisorAgent(_BaseAgent):
#     """Assess investment risks for a ticker symbol."""

#     name = "RiskAdvisorAgent"

#     def __init__(self, prompt_template: str | None = None) -> None:
#         self.prompt_template = (
#             prompt_template or 
#             "You are a risk advisor evaluating the investment risk of the stock symbol {symbol} as of {date}. "
#             "Use only data available strictly before {date}, including price volatility, macroeconomic trends, sector conditions, and company-specific developments. "
#             "Do NOT reference or speculate on any events occurring on {date} or later. "
#             "Your assessment should focus solely on known risks up to that point in time.\n"
#             "Respond ONLY in JSON with the following keys:\n"
#             "- summary: A one-line summary of the risk assessment.\n"
#             "- reasoning: A few sentences explaining the main risk factors.\n"
#             "- risk_level: One of 'Low', 'Medium', or 'High'."
#         )

#     def assess(self, symbol: str, date: str) -> Dict[str, Any]:
#         """Return a structured risk assessment."""
#         # return self._query(symbol, "risk_level", date)
#         return self._query(symbol, date)

#     def respond(self, symbol: str, date: str, history: Any | None = None) -> Dict[str, Any]:
#         return self.assess(symbol, date)

class NewsSummarizerAgent(_BaseAgent):
    """Summarise recent news for a ticker symbol."""

    name = "NewsSummarizerAgent"

    def __init__(self, prompt_template: str | None = None) -> None:
        self.prompt_template = (
            prompt_template or 
            "You are a financial news summarizer for the stock symbol {symbol}. "
            "Today's date is {date}. Summarize only news published strictly before {date}. "
            "Exclude any headlines or information from {date} or later. "
            "Focus on key developments such as earnings, leadership changes, product launches, regulatory issues, and market commentary.\n"
            "For each key story, assign a sentiment label: 'Positive', 'Negative', or 'Neutral'.\n"
            "Respond ONLY in JSON with the following keys:\n"
            "- summary: A one-line overview of recent news sentiment.\n"
            "- reasoning: A few sentences explaining how the news affects investor perception.\n"
            "- headlines: A list of major headlines, each with a sentiment label."
        )

    def summarize(self, symbol: str, date: str) -> Dict[str, Any]:
        """Return a structured news summary."""
        # return self._query(symbol, "headlines", date)
        return self._query(symbol, date)

    def respond(self, symbol: str, date: str, history: Any | None = None) -> Dict[str, Any]:
        return self.summarize(symbol, date)
    
class StrategyTypeAgent(_BaseAgent):
    """Decide strategy type (breakout, pullback, reversal) based on macro, news, OHLCV data."""

    name = "StrategyTypeAgent"

    def __init__(self, prompt_template: str | None = None) -> None:
        self.prompt_template = (
            prompt_template or """
            You are a professional trading strategist. 
            Today's date is {date}. You are given recent market information and price data for the stock symbol {symbol}.

            Your task is to determine the most appropriate trading strategy type for today. 
            You may choose ONLY ONE of the following:

            - breakout
            - pullback
            - reversal

            Consider:
            - Macroeconomic and valuation insights
            - Recent news sentiment
            - Historical price and volume data (Open, High, Low, Close, Volume)

            Respond ONLY in the following JSON format:
            {
            "strategy_type": "breakout | pullback | reversal",
            "summary": "One-line summary of why this strategy fits today",
            "reasoning": "2–4 sentences combining macro, news, and price action"
            }
            """
        )

    def respond(self, symbol: str, date: str, history: list | None = None) -> dict:
        if history is None:
            raise ValueError("StrategyTypeAgent requires `history` including macro, news, and OHLCV")

        try:
            from trading_bot import openai_client
        except Exception as exc:
            raise ImportError("openai_client must be available") from exc

        # Extract last agent outputs for macro/news
        prior_outputs = [h for h in history if h["agent"] in {"MarketAnalystAgent", "NewsSummarizerAgent"}]
        datafeed = next((h for h in history if h["agent"] == "DataFeed"), None)

        prompt = self.prompt_template.replace("{symbol}", symbol).replace("{date}", str(date))
        prompt += "\n\nHere is relevant macro and sentiment analysis:\n"
        prompt += json.dumps(_safe_json(_stringify_dates(prior_outputs)), indent=2)

        if datafeed:
            prompt += "\n\nHere is the recent price/volume data:\n"

            # Sanitize datetimes and keys
            safe_ohlcv = [
                {str(k): (str(v) if isinstance(v, (pd.Timestamp, pd.Timedelta)) else v)
                for k, v in row.items()}
                for row in datafeed.get("ohlcv", [])
            ]

            prompt += json.dumps(safe_ohlcv, indent=2)


        prompt += "\n\nRespond ONLY in the required JSON format."

        raw = openai_client.call_llm(prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            data = json.loads(match.group(0)) if match else {}

        return {
            "agent": self.name,
            "symbol": symbol,
            "date": date,
            **data,
        }
    
class IndicatorSelectionAgent(_BaseAgent):
    """Select 3–5 indicators from the registry based on strategy type and market context."""

    name = "IndicatorSelectionAgent"

    def __init__(self, prompt_template: str | None = None) -> None:

        indicator_list = [
            f"- {name}: {meta['description']} (Tags: {', '.join(meta['strategy_tags'])})"
            for name, meta in INDICATOR_REGISTRY.items()
        ]
        indicator_doc = "\n".join(indicator_list)

        self.prompt_template = (
            prompt_template or f"""
            You are a trading assistant. Today's date is {{date}}.
            You are given a trading strategy type, recent market sentiment, and recent price data.

            Your job is to choose 3 to 5 technical indicators that are appropriate for the given strategy.

            ---

            **Available Strategy Types:**
            - breakout
            - pullback
            - reversal

            Choose ONLY indicators where the `strategy_tags` match the chosen strategy type.

            **Available Indicators:**
            {indicator_doc}

            ---

            Respond ONLY in this JSON format:

            {{
            "strategy_type": "reversal | breakout | pullback",
            "indicators_used": [
                {{"name": "RSI", "params": {{"period": 14}}}},
                {{"name": "MACD", "params": {{"fast": 12, "slow": 26, "signal": 9}}}},
                ...
            ]
            }}
            """
        )

    def respond(self, symbol: str, date: str, history: list | None = None) -> dict:
        if history is None:
            raise ValueError("IndicatorSelectionAgent requires `history` including strategy_type and OHLCV")

        try:
            from trading_bot import openai_client
        except Exception as exc:
            raise ImportError("openai_client must be available") from exc

        # Extract required agent outputs
        prior_outputs = [h for h in history if h["agent"] in {
            "MarketAnalystAgent", "NewsSummarizerAgent", "StrategyTypeAgent", "DataFeed"
        }]

        prompt = self.prompt_template.replace("{symbol}", symbol).replace("{date}", str(date))
        prompt += "\n\nHere is the current market and strategy context:\n"
        prompt += json.dumps(_safe_json(_stringify_dates(prior_outputs)), indent=2)
        prompt += "\n\nRespond ONLY in the required JSON format."

        raw = openai_client.call_llm(prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            data = json.loads(match.group(0)) if match else {}

        return {
            "agent": self.name,
            "symbol": symbol,
            "date": date,
            **data,
        }
    
class StrategyPlannerAgent(_BaseAgent):
    """Plan entry/exit/stop strategy based on strategy_type, indicators, and actual market data."""

    name = "StrategyPlannerAgent"

    def __init__(self, prompt_template: str | None = None) -> None:
        self.prompt_template = (prompt_template or """
        You are a professional trading strategy planner.
        Today's date is {date}.
        You are given the full market context, trading strategy type, technical indicators, and their computed values for {symbol}.

        Your job is to write an actionable daily trading strategy.

        Respond ONLY in this EXACT JSON schema (no commentary, no extra fields):
        {
        "strategy_type": "reversal | breakout | pullback",
        "summary": "One-line summary of strategy idea",
        "rationale": "2–4 sentences combining indicator values and market reasoning",
        "setup": {
            "direction": "long | short",
            "entry_price": <number>,
            "entry_reason": "text",
            "stop_loss": { "price": <number>, "reason": "text" },
            "capital_risk_pct": <number>,
            "targets": [
            { "price": <number>, "size_pct": <number>, "reason": "text" },
            { "price": <number>, "size_pct": <number>, "reason": "text" }
            ],
            "trailing_stop": {
            "method": "EMA | VWAP | ATR | None",
            "period": <number>,
            "description": "text",
            "reason": "text"
            }
        },
        "derivations": {
            "session_range": { "high": <number>, "low": <number> },
            "last_close": <number>,
            "vwap": <number>,
            "atr": <number>,
            "rsi": <number>,
            "macd": { "line": <number>, "signal": <number>, "hist": <number> },
            "rr_calc": { "entry": <number>, "stop": <number>, "target1": <number>, "rr1": <number> }
        }
        }

        OUTPUT RULES (must comply):
        - Replace ALL <number> placeholders with actual numeric literals (e.g., 412.35). Do NOT leave placeholders.
        - Output valid JSON (double quotes, no comments, no trailing commas).
        - Entry/stop/targets must be derived from the provided OHLCV and computed indicators.
        - Entry must lie within the most recent session's [low, high].
        - Stop must be below entry for long, above entry for short.
        - R:R ≥ 2.0 across at least one target (compute from stop).
        - The 'derivations' object must show the exact numeric values used for decisions.
        """)

    def respond(self, symbol: str, date: str, history: list | None = None) -> dict:
        if history is None:
            raise ValueError("StrategyPlannerAgent requires full context including actual indicator values.")

        try:
            from trading_bot import openai_client
        except Exception as exc:
            raise ImportError("openai_client must be available") from exc

        prompt = self.prompt_template.replace("{symbol}", symbol).replace("{date}", str(date))
        prompt += "\n\nHere is the full market and technical context:\n"
        prompt += json.dumps(_safe_json(_stringify_dates(history)), indent=2)
        prompt += "\n\nRespond ONLY in the required JSON format."

        raw = openai_client.call_llm(prompt)

        # --- sanitize common LLM artifacts before parsing ---
        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)            # drop code fences
        text = re.sub(r"<[^>]+>", "null", text)                         # replace leftover <placeholder>
        text = re.sub(r"\bNaN\b|\binf\b|-inf", "null", text, flags=re.I)# JSON-safe
        # normalize smart quotes and strip trailing commas
        text = (text.replace("“", '"').replace("”", '"')
                    .replace("’", "'").replace("‘", "'"))
        text = re.sub(r",\s*(?=[}\]])", "", text)
        # ----------------------------------------------------

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # save raw for debugging when the JSON is malformed
            try:
                _PLANNER_STORAGE.save("strategy_raw", symbol, str(date), {"raw_text": text})
                print(f"[Planner] Malformed JSON for {symbol} {date}, saved strategy_raw.")
            except Exception:
                pass  # never let debug IO break the run

            data = {}
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                candidate = match.group(0)
                candidate = (candidate.replace("“", '"').replace("”", '"')
                                      .replace("’", "'").replace("‘", "'"))
                candidate = re.sub(r",\s*(?=[}\]])", "", candidate)
                try:
                    data = json.loads(candidate)
                except json.JSONDecodeError:
                    data = {"plan": {}, "parse_warning": "planner JSON malformed"}

        if not isinstance(data, dict):
            data = {}
        data.setdefault("plan", {})

        return {
            "agent": self.name,
            "symbol": symbol,
            "date": date,
            **data,
        }
    
__all__ = [
  "MarketAnalystAgent", 
  "NewsSummarizerAgent", 
  "StrategyTypeAgent",
  "IndicatorSelectionAgent",
  "StrategyPlannerAgent",
  "_stringify_dates"
]