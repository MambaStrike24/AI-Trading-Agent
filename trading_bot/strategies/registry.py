from dataclasses import dataclass
from typing import Callable, Dict, Any, Optional
from trading_bot.indicators.registry import INDICATOR_REGISTRY

@dataclass
class StrategySpec:
    name: str
    indicators: Dict[str, Dict[str, Any]]   # {"RSI": {"period": 14}, ...}
    detector: Callable[..., Any]            # returns pd.Series[bool]
    params: Dict[str, Any]                  # default detector params

REGISTRY: Dict[str, StrategySpec] = {}

def select_indicators_for(strategy_type: str) -> Dict[str, Dict[str, Any]]:
    """
    Pull default indicator params from INDICATOR_REGISTRY using strategy_tags.
    """
    out: Dict[str, Dict[str, Any]] = {}
    st = strategy_type.lower()
    for name, meta in INDICATOR_REGISTRY.items():
        tags = set(meta.get("strategy_tags", []))
        if st in tags:
            out[name] = dict(meta.get("params", {}))  # copy
    return out

def register(spec: StrategySpec) -> None:
    REGISTRY[spec.name.lower()] = spec

def get_strategy_spec(name: str) -> Optional[StrategySpec]:
    return REGISTRY.get(name.lower())
