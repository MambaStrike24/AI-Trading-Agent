from __future__ import annotations

"""Daily scheduler for running the trading pipeline.

The function :func:`schedule_daily_run` creates an APScheduler background
scheduler that will execute ``job_func`` once per day for each symbol at the
specified time (default ``08:00`` Eastern).  The caller is responsible for
shutting the scheduler down when the application exits.
"""

from datetime import datetime
from typing import Callable, Iterable

from .pipeline import Pipeline


def schedule_daily_run(
    job_func: Callable[[str], None],
    symbols: Iterable[str],
    run_time: str = "08:00",
    timezone: str = "US/Eastern",
) -> BackgroundScheduler:
    """Schedule ``job_func`` for each symbol once per day."""

    try:
        from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "apscheduler is required to schedule daily runs. Install it with 'pip install apscheduler'."
        ) from exc

    hour, minute = (int(part) for part in run_time.split(":", 1))
    scheduler = BackgroundScheduler(timezone=timezone)
    for symbol in symbols:
        scheduler.add_job(
            job_func,
            "cron",
            args=[symbol],
            id=symbol,
            hour=hour,
            minute=minute,
        )
    scheduler.start()
    return scheduler


def run_daily_pipeline(
    pipeline: Pipeline,
    symbols: Iterable[str],
    run_time: str = "08:00",
    timezone: str = "US/Eastern",
) -> BackgroundScheduler:
    """Schedule :class:`Pipeline` to run once per day for each symbol.

    The pipeline's :meth:`~trading_bot.pipeline.Pipeline.run` method is invoked
    with ``today`` set to the execution date.
    """

    def job(sym: str) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        pipeline.run(sym, today=today)

    return schedule_daily_run(job, symbols, run_time=run_time, timezone=timezone)


__all__ = ["schedule_daily_run", "run_daily_pipeline"]
