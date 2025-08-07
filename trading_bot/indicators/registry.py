import backtrader as bt
from trading_bot.indicators.vwap import VWAP


INDICATOR_REGISTRY = {
    "VWAP": {
        "class": VWAP,
        "params": {"period": 20},
        "description": "Custom VWAP indicator (Volume Weighted Average Price)",
        "strategy_tags": ["breakout", "reversal"]
    },
    "RSI": {
        "class": bt.indicators.RSI,
        "params": {"period": 14},
        "description": "Relative Strength Index (momentum & reversal detection)",
        "strategy_tags": ["pullback", "reversal"]
    },
    "EMA": {
        "class": bt.indicators.EMA,
        "params": {"period": 8},
        "description": "Exponential Moving Average (trend-following and crossover)",
        "strategy_tags": ["pullback", "breakout"]
    },
    "MACD": {
        "class": bt.indicators.MACD,
        "params": {"fast": 12, "slow": 26, "signal": 9},
        "description": "MACD for trend and momentum crossovers",
        "strategy_tags": ["reversal", "pullback"]
    },
    "ATR": {
        "class": bt.indicators.ATR,
        "params": {"period": 14},
        "description": "Average True Range (volatility-based stop sizing)",
        "strategy_tags": ["breakout", "risk", "pullback", "reversal"]
    },
    "BollingerBands": {
        "class": bt.indicators.BollingerBands,
        "params": {"period": 20, "devfactor": 2.0},
        "description": "Volatility bands for mean reversion and breakouts",
        "strategy_tags": ["pullback", "reversal"]
    },
    "Volume": {
        "class": None,  # Comes from data feed directly
        "params": {},
        "description": "Raw volume series for spike and confirmation",
        "required": "data.volume",
        "strategy_tags": ["breakout", "reversal", "pullback"]
    },
}
