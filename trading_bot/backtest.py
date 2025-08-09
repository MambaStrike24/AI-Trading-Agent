# trading_bot/backtest.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from datetime import timedelta
import pandas as pd
import ast, math

from trading_bot.strategy import compose_strategy
from trading_bot.data.utils import get_previous_day_high
from trading_bot.strategies.registry import get_strategy_spec

# ---------- helpers ----------

def _normalize_ohlcv(df_in: pd.DataFrame) -> pd.DataFrame:
    """Make yfinance output compatible with Backtrader PandasData."""
    df = df_in.copy()

    # Flatten MultiIndex (intraday or multi-symbol cases)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join([str(x) for x in tup if x is not None and str(x) != ""]).strip()
            for tup in df.columns.values
        ]

    # Lowercase columns
    df.columns = [str(c).lower() for c in df.columns]

    # Find columns even if prefixed like 'tsla_open'
    def find(key: str) -> str:
        if key in df.columns:
            return key
        cands = [c for c in df.columns if c.endswith(key)]
        if not cands:
            raise ValueError(f"Required column '{key}' not found. Got: {df.columns.tolist()[:10]} ...")
        return cands[0]

    o = find("open"); h = find("high"); l = find("low"); c = find("close"); v = find("volume")
    out = df[[o, h, l, c, v]].rename(columns={o: "open", h: "high", l: "low", c: "close", v: "volume"})
    out.index.name = "datetime"
    return out


# ---------- backtester ----------

@dataclass
class Backtester:
    data_source: str = "Yahoo Finance"
    starting_cash: float = 100_000.0

    # ------- core (single plan) -------
    def _run_single_backtest(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        plan: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        import yfinance as yf
        import backtrader as bt

        # top of _run_single_backtest (after you have `plan`)
        inds = (plan or {}).get("indicators", {})
        atr_p  = int((inds.get("ATR")  or {}).get("period", 14))
        rsi_p  = int((inds.get("RSI")  or {}).get("period", 14))
        mac    = (inds.get("MACD") or {})
        mac_fast = int(mac.get("fast", 12))
        mac_slow = int(mac.get("slow", 26))
        mac_sig  = int(mac.get("signal", 9))
        bb_p   = int((inds.get("BB")   or {}).get("period", 20))

        trail  = ((plan or {}).get("risk") or {}).get("trail", {}) or {}
        ema_p  = int(trail.get("period", 20)) if str(trail.get("method", "ATR")).upper() == "EMA" else 0

        max_need = max(atr_p, rsi_p, mac_slow + mac_sig, bb_p, ema_p)

        # Be VERY generous for intraday. Market only has ~6–7 hourly bars per day,
        # so you need many calendar days to get N "bars".
        min_days_warmup = 20          # ~1 month of trading hours
        min_hours_warmup = min_days_warmup * 24

        # Ensure we have at least (max_need + cushion) *trading* bars worth of time
        # Use 3x multiplier to account for weekends/holidays / partial sessions.
        computed_hours = int((max_need + 100) * 3)

        warmup_hours = max(min_hours_warmup, computed_hours)
        start_dt = pd.to_datetime(start_date) - pd.Timedelta(hours=warmup_hours)
        end_dt_incl  = pd.to_datetime(end_date) + pd.Timedelta(days=1)


        df = yf.download(
            symbol,
            start=start_dt.strftime("%Y-%m-%d"),
            end=end_dt_incl.strftime("%Y-%m-%d"),
            interval="1h",
            progress=False,
            auto_adjust=True,
            multi_level_index=False,
        )
        print("Bars:", len(df), df.index.min(), "->", df.index.max())

        if df.empty:
            return {"status": "no_data", "symbol": symbol, "date_range": [start_date, end_date]}

        if not plan:
            return {
                "engine": "backtrader",
                "status": "no_plan",
                "symbol": symbol,
                "date_range": [start_date, end_date],
                "starting_cash": self.starting_cash,
                "final_value": self.starting_cash,
                "net_return": 0.0,
                "max_drawdown": 0.0,
                "trade_analysis": {"total": {"total": 0}},
                "strategy_applied": None,
                "data_source": self.data_source,
            }

        # ---- inline strategy following the plan ----
        class PlannedStrategy(bt.Strategy):
            params = dict(plan=None, commission=0.0005, trade_date=None, strict_rules=False)

            # --- indicator setup ---
            def __init__(self):
                self.strict_rules = bool(self.p.strict_rules)
                self.plan = self.p.plan
                self.broker.setcommission(commission=self.p.commission)

                inds = (self.plan.get("indicators") or {})
                # Core indicators (defaults)
                self.atr = bt.ind.ATR(self.data, period=int((inds.get("ATR") or {}).get("period", 14)))
                self.rsi = bt.ind.RSI(self.data.close, period=int((inds.get("RSI") or {}).get("period", 14)))

                macd_cfg = inds.get("MACD") or {}
                self.macd = bt.ind.MACD(
                    self.data.close,
                    period_me1=int(macd_cfg.get("fast", 12)),
                    period_me2=int(macd_cfg.get("slow", 26)),
                    period_signal=int(macd_cfg.get("signal", 9)),
                )
                self.macd_hist = self.macd.macd - self.macd.signal

                # Optional Bollinger Bands if plan asks for it
                self.bb = None
                bb_cfg = inds.get("BB")
                if bb_cfg:
                    self.bb = bt.ind.BollingerBands(
                        self.data.close,
                        period=int(bb_cfg.get("period", 20)),
                        devfactor=float(bb_cfg.get("dev", 2)),
                    )

                # Trailing configuration
                risk = self.plan.get("risk") or {}
                trail = (risk.get("trail") or {})
                self.trail_method = str(trail.get("method", "ATR")).upper()
                self.trail_mult = float(trail.get("mult", 2.0))
                self.ema_trail = None
                if self.trail_method == "EMA":
                    ema_period = int(trail.get("period", 20))
                    self.ema_trail = bt.ind.EMA(self.data.close, period=ema_period)

                # Sizing / risk
                sizing = self.plan.get("sizing") or {}
                self.risk_pct = float(sizing.get("risk_pct", 0.01))

                # Plan fields (legacy)
                self.entry_rule = ((self.plan.get("entry") or {}).get("rule") or "").strip()
                self.entry_price = float((self.plan.get("entry") or {}).get("params", {}).get("entry", 0.0))
                self.fixed_stop = float(risk.get("fixed_stop", 0.0))
                self.tp_buckets = list((risk.get("tp_buckets") or []))
                self.target_filled = [False] * len(self.tp_buckets)

                self.strategy_type = str(self.plan.get("strategy_type", "")).lower()
                self.order = None
                self.trail_stop = None
                self._hwm = None  # for ATR trailing

                # ===== Bind predefined detector if available =====
                try:
                    self._spec = get_strategy_spec(self.strategy_type)
                except Exception:
                    self._spec = None
                # Copy detector params from plan (they may be mutated at runtime)
                self._detector_params = dict(((self.plan.get("entry") or {}).get("params") or {}))
                # ==================================================
                print("[ENTRY PARAMS AT INIT]", self.strategy_type, self._detector_params)
                
            # --- helpers for rule evaluation ---
            def _build_ctx(self) -> dict:
                ctx = {
                    "price": float(self.data.close[0]),
                    "entry": float(self.entry_price),
                    "rsi": float(self.rsi[0]),
                    "macd": float(self.macd.macd[0]),
                    "macd_signal": float(self.macd.signal[0]),
                    "macd_hist": float(self.macd_hist[0]),
                    "atr": float(self.atr[0]),
                }
                # previous values for "rising/cross"
                try:
                    ctx["macd_hist_prev"] = float(self.macd_hist[-1])
                except Exception:
                    ctx["macd_hist_prev"] = float("nan")
                ctx["macd_hist_rising"] = (
                    ctx["macd_hist"] > ctx["macd_hist_prev"]
                    if not math.isnan(ctx["macd_hist_prev"]) else False
                )
                # optional BB/EMA
                if self.bb is not None:
                    ctx["bb_top"] = float(self.bb.top[0])
                    ctx["bb_mid"] = float(self.bb.mid[0])
                    ctx["bb_bot"] = float(self.bb.bot[0])
                if self.ema_trail is not None:
                    ctx["ema"] = float(self.ema_trail[0])
                return ctx

            def _safe_eval_rule(self, rule: str, ctx: dict) -> bool:
                # normalize boolean ops
                expr = (
                    rule.replace("&&", " and ")
                        .replace("&", " and ")
                        .replace("||", " or ")
                        .replace("|", " or ")
                )
                allowed_names = set(ctx.keys())

                def _validate(node):
                    if isinstance(node, ast.Expression):
                        return _validate(node.body)
                    if isinstance(node, ast.BoolOp):
                        return isinstance(node.op, (ast.And, ast.Or)) and all(_validate(v) for v in node.values)
                    if isinstance(node, ast.Compare):
                        if not _validate(node.left):
                            return False
                        return all(_validate(comp) for comp in node.comparators)
                    if isinstance(node, ast.Name):
                        return node.id in allowed_names
                    if isinstance(node, ast.Constant):
                        return isinstance(node.value, (int, float, bool))
                    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                        return _validate(node.operand)
                    return False

                tree = ast.parse(expr, mode="eval")
                if not _validate(tree):
                    return False

                try:
                    return bool(eval(compile(tree, "<rule>", "eval"), {"__builtins__": {}}, ctx))
                except Exception:
                    return False

            # --- sizing / signal / trail ---
            def _risk_size(self) -> int:
                eq = self.broker.getvalue()
                px = float(self.data.close[0])
                entry = max(px, self.entry_price) if self.entry_price > 0 else px
                stop_dist = max(1e-9, entry - self.fixed_stop)
                return max(int((eq * self.risk_pct) / stop_dist), 0)
            
            def _df_window(self, lookback: int = 200) -> pd.DataFrame:
                import backtrader as bt  # ensure local scope
                n = min(len(self.data), max(10, lookback))
                idx = [bt.num2date(self.data.datetime[-i], tz=None) for i in range(n, 0, -1)]
                dfw = pd.DataFrame({
                    "open":   [float(self.data.open[-i])   for i in range(n, 0, -1)],
                    "high":   [float(self.data.high[-i])   for i in range(n, 0, -1)],
                    "low":    [float(self.data.low[-i])    for i in range(n, 0, -1)],
                    "close":  [float(self.data.close[-i])  for i in range(n, 0, -1)],
                    "volume": [float(self.data.volume[-i]) for i in range(n, 0, -1)],
                }, index=pd.to_datetime(idx))
                dfw.index.name = "datetime"
                return dfw

            def _entry_signal(self) -> bool:
                # Preferred path: use predefined detector if spec exists
                if self._spec and callable(getattr(self._spec, "detector", None)):
                    dfw = self._df_window(lookback=300)
                    try:
                        sig = self._spec.detector(dfw, **self._detector_params)

                        # Trace the most recent 3 bars of the detector:
                        try:
                            last3 = sig.iloc[-3:]
                            print("[DETECTOR last3]",
                                [(str(ts), bool(val)) for ts, val in zip(last3.index, last3.astype(bool))])
                        except Exception:
                            pass

                        ok_now = bool(sig.iloc[-1])
                        if ok_now:
                            # Log *when* the signal is true at runtime
                            try:
                                import backtrader as bt  # local import
                                cur_dt = bt.num2date(self.data.datetime[0], tz=None)
                            except Exception:
                                cur_dt = None
                            print("[ENTRY SIGNAL TRUE]", self.strategy_type, cur_dt)
                            return True
                        return False

                    except Exception as e:
                        print(f"[DetectorError] {self.strategy_type}: {e}")
                        # fall through to legacy logic below

                # Legacy path: If plan provides a rule string, evaluate it
                if self.entry_rule:
                    return self._safe_eval_rule(self.entry_rule, self._build_ctx())

                if self.strict_rules:
                    return False

                # Sensible default for pullbacks (if no explicit rule)
                if self.strategy_type == "pullback" and self.bb is not None:
                    implicit = "price <= bb_bot and rsi <= 35 and macd_hist_rising"
                    return self._safe_eval_rule(implicit, self._build_ctx())

                # Fallback: legacy reversal gate
                price = float(self.data.close[0])
                return (price >= self.entry_price
                        and float(self.rsi[0]) <= 30
                        and float(self.macd_hist[0]) > 0)


            def _update_trail(self):
                if not self.position:
                    self.trail_stop, self._hwm = None, None
                    return
                price = float(self.data.close[0])

                if self.trail_method == "EMA" and self.ema_trail is not None:
                    # trail at EMA(period)
                    self.trail_stop = float(self.ema_trail[0])
                    return

                # ATR method (use HWM - mult*ATR)
                atrv = float(self.atr[0])
                self._hwm = price if self._hwm is None else max(self._hwm, price)
                self.trail_stop = self._hwm - self.trail_mult * atrv

            def _cancel_pending_stops(self):
                # Best-effort: cancel any open orders to avoid next-day artifacts
                try:
                    for o in list(self.broker.get_orders_open()):
                        self.cancel(o)
                except Exception:
                    pass
                
            # --- main ---
            def next(self):
                if self.p.trade_date is not None:
                    cur_date = self.data.datetime.date(0)
                    if cur_date != self.p.trade_date:
                        return

                if not self.position:
                    if self._entry_signal():
                        size = self._risk_size()
                        if size > 0:
                            print("[BUY]", "size=", size, "at bar",
                                bt.num2date(self.data.datetime[0], tz=None))
                            self.buy(size=size)
                            # protective stop
                            self.sell(exectype=bt.Order.Stop, price=self.fixed_stop, size=size)
                            self._hwm = float(self.data.close[0])
                else:
                    self._update_trail()
                    price = float(self.data.close[0])

                    # take-profit buckets
                    for i, tp in enumerate(self.tp_buckets):
                        if not self.target_filled[i] and price >= float(tp["price"]):
                            sz = int(self.position.size * (float(tp["size_pct"]) / 100.0))
                            if sz > 0:
                                self.sell(size=sz)
                            self.target_filled[i] = True

                    # trail exit
                    if self.trail_stop and price <= self.trail_stop:
                        self.close()
                        self._cancel_pending_stops()
                        return

                    # --- EOD: force flat on last bar of trade date ---
                    if self._is_last_bar_of_trade_date() and self.position:
                        self.close()
                        self._cancel_pending_stops()
                        return


            def _is_last_bar_of_trade_date(self) -> bool:
                """Return True on the final bar of self.p.trade_date."""
                try:
                    next_date = self.data.datetime.date(1)  # peek one bar ahead
                except IndexError:
                    # No next bar at all -> treat as last
                    return True
                return next_date != self.p.trade_date

        # ---- run cerebro ----
        df2 = _normalize_ohlcv(df)

        # Inject runtime detector context for predefined strategies (e.g., breakout)
        try:
            spec = get_strategy_spec((plan or {}).get("strategy_type", ""))
        except Exception:
            spec = None

        if spec and spec.name.lower() == "breakout":
            entry = (plan or {}).get("entry") or {}
            params = entry.get("params") or {}

            # 1) Ensure previous_day_high is set for the trade date
            if "previous_day_high" not in params or pd.isna(params.get("previous_day_high")):
                params["previous_day_high"] = get_previous_day_high(df2, ref_date=start_date)

            # 2) Ensure detector params exist / have defaults
            params.setdefault("volume_multiplier", 1.2)
            params.setdefault("min_body_pct", 0.5)
            params.setdefault("window", 14)

            entry["params"] = params
            plan["entry"] = entry  # write back so PlannedStrategy sees it

            # ---- Detector-matching debug (now uses injected params) ----
            pvh = float(params["previous_day_high"])
            vol_mult = float(params["volume_multiplier"])
            min_body = float(params["min_body_pct"])
            window_n = int(params["window"])

            _d = pd.to_datetime(start_date).date()
            day_bars = df2[df2.index.date == _d]
            if not day_bars.empty:
                # same rolling logic as detector: rolling over history up to this day
                hist = df2[df2.index <= day_bars.index.max()].tail(300)
                avgv = hist["volume"].rolling(window=window_n, min_periods=1).mean().reindex(df2.index)
                avgv = avgv.loc[day_bars.index]

                rng = (day_bars["high"] - day_bars["low"]).replace(0, 1e-4)
                body_pct = (day_bars["close"] - day_bars["open"]).abs() / rng

                cond_hi   = day_bars["high"]  > pvh
                cond_cls  = day_bars["close"] > pvh
                cond_vol  = day_bars["volume"] > (avgv * vol_mult)
                cond_body = body_pct > min_body
                fired = (cond_hi & cond_cls & cond_vol & cond_body)

                if not fired.any():
                    print("[DEBUG] Breakout not triggered on", start_date)
                    print(" pvh:", pvh,
                        "| any high>pvh:", bool(cond_hi.any()),
                        " any close>pvh:", bool(cond_cls.any()),
                        " any vol spike:", bool(cond_vol.any()),
                        " any body>th:", bool(cond_body.any()),
                        "| vol_mult:", vol_mult, "min_body:", min_body, "win:", window_n)
                else:
                    print("[DEBUG] Breakout WOULD trigger on", start_date,
                        "first:", fired[fired].index[0])


                    
        import backtrader as bt  # noqa
        data = bt.feeds.PandasData(
            dataname=df2,
            timeframe=bt.TimeFrame.Minutes,
            compression=60,
        )

        cerebro = bt.Cerebro(stdstats=False)
        cerebro.adddata(data)
        cerebro.broker.setcash(self.starting_cash)

        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="dd")

        trade_dt = pd.to_datetime(start_date).date()
        cerebro.addstrategy(PlannedStrategy, plan=plan, trade_date=trade_dt)
        strat = cerebro.run(preload=True, runonce=False)[0]

        return {
            "engine": "backtrader",
            "status": "ok",
            "symbol": symbol,
            "date_range": [start_date, end_date],
            "final_value": float(cerebro.broker.getvalue()),
            "net_return": float(cerebro.broker.getvalue() / self.starting_cash - 1.0),
            "sharpe": strat.analyzers.sharpe.get_analysis().get("sharperatio"),
            "max_drawdown": strat.analyzers.dd.get_analysis().max.drawdown,
            "trade_analysis": strat.analyzers.trades.get_analysis(),
            "strategy_applied": plan,
            "data_source": self.data_source,
        }

    # ------- multi-day (prebuilt plans) -------
    def backtest_with_plans(self, plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for p in plans:
            res = self._run_single_backtest(p["symbol"], p["date"], p["date"], p["plan"])
            res["date"] = p["date"]
            results.append(res)
        return results

    # ------- multi-day (call agent each day) -------
    def backtest_with_agent(self, symbol: str, start_date: str, end_date: str, agent_pipeline) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for trade_date in pd.date_range(start_date, end_date, freq="B"):
            date_str = trade_date.strftime("%Y-%m-%d")
            agent_doc = agent_pipeline.run(symbol, today=date_str)

            # If the pipeline returns {"strategy": {...}}, use that. Otherwise assume it's already the planner dict.
            planner_block = agent_doc.get("strategy", agent_doc)

            # compose_strategy expects {"StrategyPlannerAgent": <planner>}
            plan = compose_strategy(symbol, {"StrategyPlannerAgent": planner_block}).get("plan")

            res = self._run_single_backtest(symbol, date_str, date_str, plan)
            res["date"] = date_str
            results.append(res)
        return results

