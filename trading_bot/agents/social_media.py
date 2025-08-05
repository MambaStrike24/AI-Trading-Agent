"""Simple social media sentiment agent.

The real project would connect to services such as StockTwits or Reddit to
gauge retail sentiment.  For the purposes of this kata the agent operates on a
very small, built-in sample dataset and performs rudimentary sentiment scoring
based on positive/negative word counts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


POSITIVE_WORDS = {"buy", "bull", "long", "moon", "gain", "up"}
NEGATIVE_WORDS = {"sell", "bear", "short", "down", "loss"}


@dataclass
class SocialMediaAgent:
    """Analyse a very small sample of social media posts for sentiment."""

    data_source: str = "sample"
    samples: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "TSLA": [
                "TSLA to the moon!",
                "Thinking of going long TSLA",
                "TSLA might be overvalued",
            ]
        }
    )

    def analyze(self, symbol: str) -> Dict[str, Any]:
        posts = self.samples.get(symbol, [])
        if not posts:
            summary = "No social data"
            score = 0
        else:
            pos = sum(sum(w.lower() in POSITIVE_WORDS for w in p.split()) for p in posts)
            neg = sum(sum(w.lower() in NEGATIVE_WORDS for w in p.split()) for p in posts)
            score = pos - neg
            summary = "Bullish" if score > 0 else "Bearish" if score < 0 else "Neutral"

        return {
            "agent": "SocialMediaAgent",
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "methods_used": ["keyword_sentiment"],
            "results": {"posts": posts, "score": score},
            "summary": summary,
            "score": score,
            "data_source": self.data_source,
        }


__all__: List[str] = ["SocialMediaAgent"]

