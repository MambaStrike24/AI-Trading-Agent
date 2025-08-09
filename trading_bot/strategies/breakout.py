import pandas as pd
from .registry import StrategySpec, register, select_indicators_for

def detect_breakout_entry(
    df: pd.DataFrame,
    previous_day_high: float,
    volume_multiplier: float = 1.2,
    window: int = 14,
    min_body_pct: float = 0.5,
) -> pd.Series:
    """
    Boolean Series 'breakout_entry' aligned to df.index.
    Expects lowercase columns: open, high, low, close, volume (hourly).
    """
    avgv = df["volume"].rolling(window=window, min_periods=1).mean()
    rng = (df["high"] - df["low"]).replace(0, 1e-4)
    body_pct = (df["close"] - df["open"]).abs() / rng

    s = (
        (df["high"] > previous_day_high) &
        (df["close"] > previous_day_high) &
        (df["volume"] > avgv * volume_multiplier) &
        (body_pct > min_body_pct)
    )
    # Ensure boolean Series and set a proper name (compatible across pandas versions)
    s = s.astype(bool)
    s.name = "breakout_entry"
    return s

BREAKOUT_SPEC = StrategySpec(
    name="breakout",
    indicators=select_indicators_for("breakout"),  # pulls VWAP/EMA/ATR from your INDICATOR_REGISTRY by tag
    detector=detect_breakout_entry,
    params={
        "volume_multiplier": 1.2,
        "window": 14,
        "min_body_pct": 0.5,
        # NOTE: 'previous_day_high' must be provided at runtime from your data context
    },
)

register(BREAKOUT_SPEC)
