"""
Tests for src/product_scrapers/celery/beat_schedule.py.

Strategy: patch SessionLocal and SearchConfig to avoid any DB connection;
patch celery.beat.ScheduleEntry / Scheduler internals to avoid Celery init.
"""

from datetime import time as dtime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# get_dynamic_schedule
# ---------------------------------------------------------------------------


def _make_search(id_: int, hour: int, minute: int, freq_days: int) -> SimpleNamespace:
    """Build a fake SearchConfig row."""
    return SimpleNamespace(
        id=id_,
        is_active=True,
        preferred_time=dtime(hour, minute),
        frequency_days=freq_days,
    )


@patch("src.app.infrastructure.database_config.SessionLocal")
def test_get_dynamic_schedule_returns_empty_when_no_searches(mock_session_local):
    from src.product_scrapers.celery.beat_schedule import get_dynamic_schedule

    db = MagicMock()
    mock_session_local.return_value = db
    db.query.return_value.filter.return_value.all.return_value = []

    result = get_dynamic_schedule()

    assert result == {}
    db.close.assert_called_once()


@patch("src.app.infrastructure.database_config.SessionLocal")
def test_get_dynamic_schedule_builds_entry_for_each_search(mock_session_local):
    from src.product_scrapers.celery.beat_schedule import get_dynamic_schedule

    db = MagicMock()
    mock_session_local.return_value = db
    db.query.return_value.filter.return_value.all.return_value = [
        _make_search(1, 8, 0, 1),
        _make_search(2, 14, 30, 7),
    ]

    result = get_dynamic_schedule()

    assert "run_search_1" in result
    assert "run_search_2" in result
    assert (
        result["run_search_1"]["task"]
        == "src.product_scrapers.celery.tasks.run_scraper_search"
    )
    assert result["run_search_1"]["args"] == (1,)
    assert result["run_search_2"]["args"] == (2,)
    db.close.assert_called_once()


@patch("src.app.infrastructure.database_config.SessionLocal")
def test_get_dynamic_schedule_closes_db_even_on_exception(mock_session_local):
    from src.product_scrapers.celery.beat_schedule import get_dynamic_schedule

    db = MagicMock()
    mock_session_local.return_value = db
    db.query.side_effect = RuntimeError("DB error")

    with pytest.raises(RuntimeError):
        get_dynamic_schedule()

    db.close.assert_called_once()


# ---------------------------------------------------------------------------
# DynamicDBScheduler.sync_from_db
# ---------------------------------------------------------------------------


@patch("src.product_scrapers.celery.beat_schedule.get_dynamic_schedule")
@patch("src.product_scrapers.celery.beat_schedule.ScheduleEntry")
def test_sync_from_db_populates_schedule(mock_entry_cls, mock_get_schedule):
    from src.product_scrapers.celery.beat_schedule import DynamicDBScheduler

    schedule_data = {
        "run_search_1": {
            "task": "src.product_scrapers.celery.tasks.run_scraper_search",
            "schedule": MagicMock(),
            "args": (1,),
        }
    }
    mock_get_schedule.return_value = schedule_data

    mock_entry = MagicMock()
    mock_entry_cls.return_value = mock_entry

    # Create scheduler without calling __init__ (avoids Celery setup)
    scheduler = DynamicDBScheduler.__new__(DynamicDBScheduler)
    scheduler.schedule = {}
    scheduler.app = MagicMock()

    scheduler.sync_from_db()

    assert "run_search_1" in scheduler.schedule
    assert scheduler.schedule["run_search_1"] is mock_entry
    mock_entry_cls.assert_called_once()


@patch("src.product_scrapers.celery.beat_schedule.get_dynamic_schedule")
@patch("src.product_scrapers.celery.beat_schedule.ScheduleEntry")
def test_sync_from_db_clears_old_entries_first(mock_entry_cls, mock_get_schedule):
    from src.product_scrapers.celery.beat_schedule import DynamicDBScheduler

    mock_get_schedule.return_value = {}

    scheduler = DynamicDBScheduler.__new__(DynamicDBScheduler)
    mock_schedule = MagicMock()
    scheduler.schedule = mock_schedule
    scheduler.app = MagicMock()

    scheduler.sync_from_db()

    mock_schedule.clear.assert_called_once()
