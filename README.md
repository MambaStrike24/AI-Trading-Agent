# AI Trading Agent

This repository implements a minimal **LLM‑powered trading framework**.
Agents query a language model for insights about a stock symbol and return a
structured JSON report that can be consumed by downstream tools.

## Project Modules

| Module / File | Purpose |
| --- | --- |
| `trading_bot/agents/llm_agent.py` | Queries a language model for market commentary. |
| `trading_bot/strategy.py` | Combines agent outputs into entry, sizing, risk and exit sections. |
| `trading_bot/backtest.py` | Runs a simple buy‑and‑hold simulation to evaluate a strategy. |
| `trading_bot/storage.py` | Persists agent outputs and strategies as JSON under a symbol/date tree. |
| `trading_bot/portfolio.py` | Tracks open and closed positions and computes PnL. |
| `trading_bot/scheduler.py` | Queues daily runs with APScheduler. |
| `trading_bot/pipeline.py` | Runs LLM agents and aggregates their outputs. |

## Agent Output

Every agent returns a JSON serialisable dictionary containing:

- `agent`: name of the agent
- `symbol`: the instrument analysed
- `summary`: brief conclusion from the model
- `raw_response`: full text returned by the LLM

Example response from the `LLMAgent`:

```json
{
  "agent": "LLMAgent",
  "symbol": "TSLA",
  "summary": "Tesla shows growth potential this quarter.",
  "raw_response": "Tesla's recent earnings beat expectations..."
}
```

## Daily Workflow

For each configured symbol the pipeline performs:

1. **Run agents** – gather LLM-based commentary.
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
3. **Construct and run the pipeline**
   ```python
   from trading_bot.agents import LLMAgent
   from trading_bot.pipeline import Pipeline

   agents = [LLMAgent()]
   pipeline = Pipeline(agents=agents)

   result = pipeline.run("TSLA")
   print(result["reports"])  # list of agent outputs
   ```
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
