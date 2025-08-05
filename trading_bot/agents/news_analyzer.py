"""News analysis agent.

For this kata the agent works with a tiny built-in set of headlines per symbol
and performs a naive sentiment calculation.  Real implementations would query a
news API or RSS feed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


POSITIVE_WORDS = {"beat", "growth", "up", "surge", "gain"}
NEGATIVE_WORDS = {"miss", "down", "fall", "loss", "drop"}


@dataclass
class NewsAnalyzerAgent:
    """Analyse headline sentiment using a simple keyword approach."""

    data_source: str = "sample"
    headlines: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "TSLA": [
                "TSLA reports record delivery numbers",
                "Analysts debate if TSLA rally can continue",
            ]
        }
    )

    def analyze(self, symbol: str) -> Dict[str, Any]:
        headlines = self.headlines.get(symbol, [])
        if not headlines:
            sentiment = 0
            summary = "No headlines"
        else:
            pos = sum(sum(w.lower() in POSITIVE_WORDS for w in h.split()) for h in headlines)
            neg = sum(sum(w.lower() in NEGATIVE_WORDS for w in h.split()) for h in headlines)
            sentiment = pos - neg
            summary = "Positive" if sentiment > 0 else "Negative" if sentiment < 0 else "Neutral"

        return {
            "agent": "NewsAnalyzerAgent",
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "methods_used": ["keyword_sentiment"],
            "results": {"headlines": headlines, "sentiment": sentiment},
            "summary": summary,
            "sentiment": sentiment,
            "data_source": self.data_source,
        }


__all__: List[str] = ["NewsAnalyzerAgent"]

