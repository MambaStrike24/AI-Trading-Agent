# 🚀 Agent-Based Trading Bot Framework

## 🏗️ Overview

This project is a **collaborative agent-based trading framework** designed to generate **daily trading strategies** using data from technical indicators, market activity, social sentiment, and financial news. Each day, before market open, the system runs a full pipeline that:

1. Gathers insights using intelligent agents  
2. Composes a dynamic, multi-line strategy  
3. Backtests the strategy  
4. Logs results and updates portfolio tracking  

---

## ✨ Strategy Components

Each generated strategy must include the following sections:

- **ENTRY CRITERIA**
- **POSITION SIZING**
- **RISK MANAGEMENT**
- **EXIT STRATEGY**
- **TRADE MANAGEMENT**

The system supports:

- ✅ Scheduled daily runs  
- ✅ Multi-symbol support  
- ✅ Portfolio tracking  
- ✅ Historical review and logging  
- ✅ Free and public data sources  

---

## 🧠 Agent Autonomy + Explainability

Each agent operates independently, selecting which methods and indicators to use based on context. All outputs must include:

- Structured JSON results  
- Indicators or methods used  
- Natural-language summary  
- Timestamp and data source label  

### Example Output (TechnicalAnalysisAgent)

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
Agent Expectations
TechnicalAnalysisAgent: Trend detection using selected indicators

MarketScannerAgent: Price, volume, VWAP, ATR, and volatility

SocialMediaAgent: Sentiment from StockTwits, Reddit, or samples

NewsAnalyzerAgent: Sentiment and key headlines from news APIs or static sets

🧠 Strategy Composer
The strategy composer aggregates agent insights and generates a structured, creative trading plan.

Strategy Output Format
json
Copy
Edit
{
  "symbol": "TSLA",
  "date": "2025-01-01",
  "entry_criteria": "...",
  "position_sizing": "...",
  "risk_management": "...",
  "exit_strategy": "...",
  "trade_management": "...",
  "rationale": {
    "technical": { "summary": "...", "details": {...} },
    "news": { "summary": "...", "headlines": [...] },
    "social": { "summary": "...", "score": 1 },
    "macro": { "summary": "..." }
  }
}
Strategies must be executable and explainable using only the provided agent data.

📉 Backtester Module
Simulates historical performance of each strategy over a user-defined date range.

Example Call
python
Copy
Edit
backtest(symbol="TSLA", start_date="2025-01-01", end_date="2025-01-04", strategy_dict=strategy)
Output Format
json
Copy
Edit
{
  "symbol": "TSLA",
  "date_range": ["2025-01-01", "2025-01-04"],
  "net_return": 0.087,
  "max_drawdown": 0.041,
  "trade_log": [
    {
      "entry_time": "2025-01-01T09:33:00",
      "entry_price": 245.50,
      "exit_time": "2025-01-03T15:40:00",
      "exit_price": 265.60,
      "pnl": 20.10
    }
  ],
  "equity_curve": [...],
  "strategy_applied": "<full strategy>",
  "agent_inputs": {
    "technical": { ... },
    "social": { ... },
    "news": { ... }
  }
}
Use Backtrader or bt as the simulation engine.

🕒 Daily Scheduler
Use APScheduler or cron to trigger daily runs before market open (e.g., 8:00 AM ET).

For each symbol (e.g., ["TSLA", "AAPL", "NVDA"]), the pipeline should:

Run all agents

Compose a strategy

Backtest the strategy

Save all results

🗂️ Historical Logging
Use JSON, SQLite, Firestore, or PostgreSQL to persist:

Strategy objects

Agent outputs

Backtest results

Timestamps and symbol

Example Query
python
Copy
Edit
load_strategy(symbol="TSLA", date="2025-01-02")
📊 Portfolio Tracking
Track simulated or real trades over time:

Entry/exit time and price

Position size

Strategy reference

Open/closed status

Live PnL

🆓 Free Data Sources
Use only free and public data services:

📈 yfinance: price, volume, indicators

📰 newsapi, Google News RSS: headlines

💬 StockTwits, Reddit, or sample data: sentiment

🖥️ Phase 2 Extensions (Optional)
Dashboard: Streamlit or Flask UI

Notifications: Slack or email daily strategy delivery

Live Trading: Alpaca or Interactive Brokers integration

✅ Final Checklist
 Agents return structured, autonomous JSON with reasoning

 Strategy composer generates all required sections

 Backtester evaluates strategy with traceable results

 Scheduler runs daily per symbol

 All outputs are logged and reviewable

 Portfolio can track open/closed positions

 Only free APIs and data sources are used

🧼 Codex Cleanup Instructions
After fully reviewing this README and project specification:

🧠 Codex, now scan the current codebase.
🧹 Remove or refactor any unused, outdated, or misaligned files.
🔄 Rebuild the system from scratch if necessary using modular, testable components.
✅ Ensure everything aligns with the specs in this README.
