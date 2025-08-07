import yfinance as yf
import pandas as pd
import backtrader as bt
from trading_bot.indicators.registry import INDICATOR_REGISTRY


def compute_selected_indicators(symbol, date, indicators_used, window_days=60):
    end = pd.to_datetime(date) + pd.Timedelta(days=1)
    start = end - pd.Timedelta(days=window_days)

    df = yf.download(
        symbol,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),  # exclusive, so this includes 'date'
        interval="1h",
        auto_adjust=True,
        progress=False,
    )

    if df.empty:
        raise ValueError(f"No price data for {symbol} from {start.date()} to {end.date()}.")

    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    result = {}

    class IndicatorStrategy(bt.Strategy):
        def __init__(self):
            self.ind_map = {}
            for item in indicators_used:
                name = item["name"]
                params = item.get("params", {})
                if name in INDICATOR_REGISTRY:
                    ind_class = INDICATOR_REGISTRY[name]["class"]
                    if ind_class:
                        self.ind_map[name] = ind_class(self.data, **params)

        def next(self):
            for name, ind in self.ind_map.items():
                try:
                    result[name] = float(ind[0])
                except Exception:
                    result[name] = None
            self.env.runstop()

    cerebro.addstrategy(IndicatorStrategy)
    cerebro.run()

    return result
