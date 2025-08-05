# AI Trading Agent

This repository implements a minimal **agent‑based trading framework**.  Each
agent gathers a different type of information about a stock symbol and returns a
structured JSON report.  The reports are combined into a trading strategy,
backtested, and optionally saved to disk with any portfolio updates.

## Project Modules

| Module / File | Purpose |
| --- | --- |
| `trading_bot/agents/technical_analysis.py` | Downloads price data from Yahoo Finance and computes EMA, RSI and MACD indicators. |
| `trading_bot/agents/market_scanner.py` | Collects price, volume, VWAP, ATR and volatility metrics. |
| `trading_bot/agents/social_media.py` | Performs keyword‑based sentiment analysis on sample posts. |
| `trading_bot/agents/news_analyzer.py` | Analyses sample headlines for sentiment and returns key headlines. |
| `trading_bot/strategy.py` | Combines agent outputs into entry, sizing, risk and exit sections. |
| `trading_bot/backtest.py` | Runs a simple buy‑and‑hold simulation to evaluate a strategy. |
| `trading_bot/storage.py` | Persists agent outputs and strategies as JSON under a symbol/date tree. |
| `trading_bot/portfolio.py` | Tracks open and closed positions and computes PnL. |
| `trading_bot/scheduler.py` | Queues daily runs with APScheduler. |
| `trading_bot/pipeline.py` | Orchestrates agents, strategy composition, backtesting and persistence. |

## Agent Output

Every agent returns a JSON serialisable dictionary containing:

- `agent`: name of the agent
- `symbol`: the instrument analysed
- `timestamp`: UTC time when the analysis was produced
- method specific fields (e.g. `indicators_used`, `results`, `summary`,
  `trend_signal`, `data_source`)

Example response from the `TechnicalAnalysisAgent`:

```json
{
  "agent": "TechnicalAnalysisAgent",
  "symbol": "TSLA",
  "timestamp": "2025-01-01T08:00:00Z",
  "indicators_used": ["ema_9", "rsi_14", "macd"],
  "results": {
    "ema_9": 250.3,
    "rsi_14": 57.2,
    "macd_hist": 1.24
  },
  "summary": "Trend is bullish with price above EMA and positive MACD crossover.",
  "trend_signal": "bullish",
  "data_source": "Yahoo Finance"
}
```

## Daily Workflow

For each configured symbol the pipeline performs:

1. **Run agents** – gather technical, market, social and news data.
2. **Compose strategy** – aggregate agent reports into a full trading plan
   (entry, position sizing, risk management, exit and trade management).
3. **Backtest** – simulate a simple buy‑and‑hold over the recent period.
4. **Persist and update portfolio** – save agent outputs, strategy and backtest
   results while recording any open or closed positions.

## Step‑by‑Step Usage

1. **Install dependencies and run tests**
   ```bash
   pip install -r requirements.txt
   pytest -q
   ```
2. **Construct and run the pipeline**
   ```python
   from trading_bot.agents import (
       TechnicalAnalysisAgent, MarketScannerAgent,
       SocialMediaAgent, NewsAnalyzerAgent,
   )
   from trading_bot.pipeline import Pipeline
   from trading_bot.storage import JSONStorage
   from trading_bot.portfolio import Portfolio

   agents = [
       TechnicalAnalysisAgent(),
       MarketScannerAgent(),
       SocialMediaAgent(),
       NewsAnalyzerAgent(),
   ]

   pipeline = Pipeline(agents=agents,
                       storage=JSONStorage("data"),
                       portfolio=Portfolio())

   result = pipeline.run_for_symbol("TSLA")
   print(result["strategy"])  # composed strategy dictionary
   ```
3. **Schedule a daily run**
   ```python
   from trading_bot.scheduler import schedule_daily_run

   schedule_daily_run(pipeline, symbols=["TSLA", "AAPL"], hour=8, minute=0)
   ```
4. **Load historical strategies**
   ```python
   stored = pipeline.storage.load_strategy("TSLA", result["strategy"]["date"])
   ```

These steps demonstrate the full workflow from data collection to persistence.

## Running tests

To verify the environment at any time, re‑run the tests:

```bash
pytest -q
```

External API calls are mocked; no network access is required.