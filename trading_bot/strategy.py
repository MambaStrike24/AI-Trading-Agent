# trading_bot/strategy.py
from __future__ import annotations
from typing import Any, Dict, Optional

# Ensure strategy specs (e.g., breakout) auto-register
import trading_bot.strategies as _  # triggers __init__ -> breakout import/registration

from trading_bot.strategies.registry import get_strategy_spec

# ---------------------------
# helpers
# ---------------------------

def _coerce_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)

def _clean_direction(setup: Dict[str, Any]) -> str:
    d = str(setup.get("direction", "long")).lower().strip()
    return "short" if d == "short" else "long"

def _infer_strategy_block(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    if "StrategyPlannerAgent" in agent_data:
        return agent_data["StrategyPlannerAgent"]
    if "strategy" in agent_data and isinstance(agent_data["strategy"], dict):
        return agent_data["strategy"]
    if "setup" in agent_data or "strategy_type" in agent_data:
        return agent_data
    return {}

def _targets_from_setup(setup: Dict[str, Any]) -> list[Dict[str, float]]:
    out = []
    for t in setup.get("targets", []) or []:
        out.append({
            "price": _coerce_float(t.get("price")),
            "size_pct": _coerce_float(t.get("size_pct"), 50.0),
        })
    return out

# ---------------------------
# public API
# ---------------------------

def compose_strategy(symbol: str,
                     agent_data: Dict[str, Any],
                     strategy_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Build a normalized plan dict for the backtester.
    Accepts {"strategy": {...}}, {"StrategyPlannerAgent": {...}}, or a planner-like dict.
    """
    planner = _infer_strategy_block(agent_data)
    if not planner:
        return {"plan": None}

    setup = planner.get("setup") or {}
    strategy_type = str(planner.get("strategy_type", "reversal")).lower()

    # --- risk / exits ---
    stop_price   = _coerce_float((setup.get("stop_loss") or {}).get("price"))
    risk_pct     = _coerce_float(setup.get("capital_risk_pct"), 1.0) / 100.0
    trail_cfg    = setup.get("trailing_stop") or {}
    trail_method = str(trail_cfg.get("method", "ATR")).upper()
    trail_period = int(trail_cfg.get("period", 14) or 14)
    trail_mult   = _coerce_float(trail_cfg.get("mult", 2.0 if trail_method == "ATR" else 0.0), 2.0)

    # --- strategy spec ---
    spec = get_strategy_spec(strategy_type)
    if not spec:
        return {"plan": None}

    # Merge default detector params with any user overrides
    detector_params = {**spec.params}
    detector_params.update(setup.get("detector_params") or {})

    plan: Dict[str, Any] = {
        "strategy_type": spec.name,
        "indicators": spec.indicators,    # computed by backtester before detector
        "entry": {
            # string ref is optional; backtester can directly use spec.detector
            "detector": f"{spec.name}.detect_{spec.name}_entry",
            "params": detector_params,
        },
        "exit": {"rule": "stop_or_trail", "params": {}},
        "sizing": {"risk_pct": risk_pct if risk_pct > 0 else 0.01},
        "risk": {
            "stop_type": "fixed_price",
            "fixed_stop": stop_price,
            "tp_buckets": _targets_from_setup(setup),
            "trail": {"method": trail_method, "period": trail_period, "mult": trail_mult},
        },
        "meta": {
            "agent": planner.get("agent"),
            "symbol": planner.get("symbol", symbol),
            "date": planner.get("date", strategy_date),
            "summary": planner.get("summary"),
            "rationale": planner.get("rationale"),
        },
    }
    return {"plan": plan}
