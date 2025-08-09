# trading_bot/strategies/__init__.py
from .registry import StrategySpec, register, select_indicators_for
from . import breakout, reversal  # import so their functions exist

register(StrategySpec(
    name="breakout",
    indicators=select_indicators_for("breakout"),
    detector=breakout.detect_breakout_entry,   # <- your function
    params={"volume_multiplier": 2.0, "min_body_pct": 0.5},  # defaults
))

register(StrategySpec(
    name="reversal",
    indicators=select_indicators_for("reversal"),
    detector=reversal.detect_reversal_entry,   # <- your function
    params=reversal.DEFAULTS,                  # reuse module defaults
))
