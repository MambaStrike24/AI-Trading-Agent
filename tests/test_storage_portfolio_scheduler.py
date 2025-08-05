import os
from datetime import datetime

from trading_bot.storage import JSONStorage
from trading_bot.portfolio import Portfolio
from trading_bot.scheduler import schedule_daily_run


def test_json_storage_roundtrip(tmp_path):
    storage = JSONStorage(base_dir=tmp_path)
    data = {"foo": 1}
    path = storage.save("strategy", "TSLA", "2024-01-01", data)
    assert path.exists()
    loaded = storage.load("strategy", "TSLA", "2024-01-01")
    assert loaded == data


def test_portfolio_tracks_positions():
    pf = Portfolio()
    pos = pf.open_position(
        "TSLA", 10, 100.0, datetime(2024, 1, 1, 9, 30), "strat1"
    )
    assert pf.open_positions() == [pos]
    pf.close_position(pos, 110.0, datetime(2024, 1, 2, 10, 0))
    assert pf.closed_positions() == [pos]
    assert pos.pnl() == 100.0


def test_scheduler_creates_jobs():
    calls = []

    def job(symbol):
        calls.append(symbol)

    scheduler = schedule_daily_run(job, ["TSLA", "AAPL"], run_time="00:00", timezone="UTC")
    try:
        jobs = scheduler.get_jobs()
        assert len(jobs) == 2
        assert {job.id for job in jobs} == {"TSLA", "AAPL"}
    finally:
        scheduler.shutdown()
