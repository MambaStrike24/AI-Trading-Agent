# AI Trading Agent

This repository contains the beginnings of an agent-based trading framework.  It
is intentionally lightweight and serves as a foundation for future work.  The
project structure includes:

- **TechnicalAnalysisAgent** – downloads price data from Yahoo Finance and
  computes a few common indicators (EMA, RSI and MACD).
- **MarketScannerAgent** – collects price, volume, VWAP, ATR and volatility
  metrics.
- **SocialMediaAgent** – performs keyword based sentiment analysis on a small
  sample of posts.
- **NewsAnalyzerAgent** – analyses sample headlines for sentiment.
- **Strategy Composer** – combines the outputs of agents into a single trading
  strategy dictionary containing entry, sizing and risk guidelines.
- **Backtester** – runs a minimal buy-and-hold simulation to evaluate a
  composed strategy.

The implementation is heavily simplified but follows the JSON schemas described
in the project specification.

## Running tests

The repository uses `pytest` for the tiny test-suite.  To execute the tests run:

```bash
pytest
```

Network access is not required for the tests as external data calls are
mocked.