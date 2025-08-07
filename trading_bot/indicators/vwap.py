# trading_bot/indicators/vwap.py

import backtrader as bt


class VWAP(bt.Indicator):
    """Custom VWAP (Volume Weighted Average Price) indicator"""
    lines = ('vwap',)
    params = dict(period=20)

    def __init__(self):
        # Cumulative volume * price over the period
        cum_price_vol = bt.ind.SumN(self.data.close * self.data.volume, period=self.p.period)
        cum_vol = bt.ind.SumN(self.data.volume, period=self.p.period)
        self.lines.vwap = cum_price_vol / (cum_vol + 1e-8)  # avoid division by zero
