# AI Trading Agent

This repository implements a minimal **role‑based trading framework** powered by OpenAI.
Specialised agents (market analyst, risk advisor, news summariser, etc.) query
the OpenAI API for insights about a stock symbol. A small `Coordinator`
orchestrates their conversation and returns a structured report for downstream
tools. The agents require an `OPENAI_API_KEY` to be present in the environment.

## Project Modules

| Module / File | Purpose |
| --- | --- |
| `trading_bot/agents/llm_roles.py` | Role‑specific OpenAI agents (analyst, risk advisor, news summariser). |
| `trading_bot/coordinator.py` | Orchestrates conversations between role agents. |
| `trading_bot/openai_client.py` | Thin wrapper around the OpenAI API. |
| `trading_bot/strategy.py` | Combines agent outputs into entry, sizing, risk and exit sections. |
| `trading_bot/backtest.py` | Runs a simple buy‑and‑hold simulation to evaluate a strategy. |
| `trading_bot/storage.py` | Persists agent outputs and strategies as JSON under a symbol/date tree. |
| `trading_bot/portfolio.py` | Tracks open and closed positions and computes PnL. |
| `trading_bot/scheduler.py` | Queues daily runs with APScheduler. |
| `trading_bot/pipeline.py` | Delegates execution to the coordinator. |

## Agent Output

Every role agent returns a JSON serialisable dictionary containing:

- `agent`: name of the agent
- `symbol`: the instrument analysed
- a role‑specific field such as `analysis`, `assessment` or `summary`

Example response from the `MarketAnalystAgent`:

```json
{
  "agent": "MarketAnalystAgent",
  "symbol": "TSLA",
  "analysis": "Tesla shows growth potential this quarter."
}
```

## Daily Workflow

For each configured symbol the pipeline performs:

1. **Run agents** – gather specialised LLM-based commentary.
2. Optionally feed the combined reports into separate strategy or backtesting
   utilities.

## Step‑by‑Step Usage

1. **Set your OpenAI API key**

   The LLM agents use the OpenAI API. Export your key before running any code:

   ```bash
   export OPENAI_API_KEY="sk-..."  # Linux / macOS
   # For Windows PowerShell use: setx OPENAI_API_KEY "sk-..."
   ```
2. **Install dependencies and run tests**

   This project requires the `yfinance` and `apscheduler` packages for data
   retrieval and scheduling. They are included in `requirements.txt`.

   ```bash
   pip install -r requirements.txt
   pytest -q
   ```
3. **Construct and run the coordinator**
   ```python
   from trading_bot.coordinator import Coordinator
   from trading_bot.pipeline import Pipeline
   from trading_bot.agents.llm_roles import (
       MarketAnalystAgent,
       RiskAdvisorAgent,
       NewsSummarizerAgent,
   )

   class Analyst:
       def respond(self, symbol, history):
           return {"message": MarketAnalystAgent().analyze(symbol)["analysis"]}

   class Risk:
       def respond(self, symbol, history):
           return {"message": RiskAdvisorAgent().assess(symbol)["assessment"]}

   class News:
       def respond(self, symbol, history):
           return {"message": NewsSummarizerAgent().summarize(symbol)["summary"]}

   from trading_bot.storage import JSONStorage

   coordinator = Coordinator([Analyst(), Risk(), News()])
   pipeline = Pipeline(coordinator, storage=JSONStorage())

   result = pipeline.run("TSLA")
   print(result["conversation"])  # exchange between agents
   ```
   A notebook version is available at `notebooks/role_coordinator_demo.ipynb`.
4. **Schedule a daily run**
   ```python
   from trading_bot.scheduler import schedule_daily_run

   schedule_daily_run(pipeline.run, symbols=["TSLA", "AAPL"], run_time="08:00")
   ```

These steps demonstrate the core workflow.

## Running tests

To verify the environment at any time, re‑run the tests:

```bash
pytest -q
```

External API calls are mocked; no network access is required.
