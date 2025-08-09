# trading_bot/strategies/reversal.py
from typing import Dict, Any
import numpy as np
import pandas as pd
import ta

DEFAULTS: Dict[str, Any] = {
    "rsi_window": 14,
    "bb_window": 20,
    "bb_dev": 2.0,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "body_pct_min": 0.50,  # 50%
}

def _ensure_columns(out: pd.DataFrame, p: Dict[str, Any]) -> pd.DataFrame:
    # Compute if missing; if your pipeline precomputes these, we won't double-calc.
    if "rsi" not in out:
        out["rsi"] = ta.momentum.RSIIndicator(out["close"], window=p["rsi_window"]).rsi()
    if "bb_lower" not in out or "bb_upper" not in out:
        bb = ta.volatility.BollingerBands(
            out["close"], window=p["bb_window"], window_dev=p["bb_dev"]
        )
        out["bb_lower"] = bb.bollinger_lband()
        out["bb_upper"] = bb.bollinger_hband()
    return out

# AFTER
def detect_reversal_entry(df: pd.DataFrame, params: Dict[str, Any] = None, **kwargs) -> pd.Series:
    # Merge DEFAULTS + explicit params dict + free kwargs
    p = DEFAULTS.copy()
    if params:
        p.update(params)
    if kwargs:
        p.update(kwargs)

    out = _ensure_columns(df.copy(), p)
    rng = (out["high"] - out["low"]).replace(0, np.nan)
    out["body_pct"] = (out["close"] - out["open"]).abs() / rng

    long_entry = (
        (out["rsi"] < p["rsi_oversold"]) &
        (out["close"] <= out["bb_lower"]) &
        (out["body_pct"] >= p["body_pct_min"])
    )
    short_entry = (
        (out["rsi"] > p["rsi_overbought"]) &
        (out["close"] >= out["bb_upper"]) &
        (out["body_pct"] >= p["body_pct_min"])
    )

    long_entry = long_entry.fillna(False)
    short_entry = short_entry.fillna(False)

    reversal_entry = (long_entry | short_entry)
    reversal_entry.name = "reversal_entry"
    return reversal_entry


# Optional: if you want direction elsewhere (not required by StrategySpec)
def reversal_direction(df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.Series:
    p = DEFAULTS.copy()
    if params:
        p.update(params)
    out = _ensure_columns(df.copy(), p)
    rng = (out["high"] - out["low"]).replace(0, np.nan)
    out["body_pct"] = (out["close"] - out["open"]).abs() / rng
    long_entry = (
        (out["rsi"] < p["rsi_oversold"]) &
        (out["close"] <= out["bb_lower"]) &
        (out["body_pct"] >= p["body_pct_min"])
    )
    short_entry = (
        (out["rsi"] > p["rsi_overbought"]) &
        (out["close"] >= out["bb_upper"]) &
        (out["body_pct"] >= p["body_pct_min"])
    )
    sig = np.select(
        [long_entry & ~short_entry, short_entry & ~long_entry],
        [1, -1],
        default=0
    )
    return pd.Series(sig, index=df.index, name="reversal_signal")
