"""
Tests for src/celery/beat_schedule.py.

Strategy: patch ApiClient and _get_celery_worker_token to avoid any HTTP
calls; patch celery.beat.ScheduleEntry / Scheduler internals to avoid Celery init.
"""

from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# get_dynamic_schedule
# ---------------------------------------------------------------------------


@patch("src.celery.beat_schedule._get_celery_worker_token", return_value=None)
def test_get_dynamic_schedule_returns_empty_when_no_token(mock_token):
    from src.celery.beat_schedule import get_dynamic_schedule

    result = get_dynamic_schedule()
    assert result == {}


@patch("src.celery.beat_schedule._get_celery_worker_token", return_value="tok")
@patch("src.celery.beat_schedule.ApiClient")
def test_get_dynamic_schedule_returns_empty_when_no_searches(mock_client_cls, _):
    from src.celery.beat_schedule import get_dynamic_schedule

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.get_active_search_configs.return_value = []

    result = get_dynamic_schedule()
    assert result == {}


@patch("src.celery.beat_schedule._get_celery_worker_token", return_value="tok")
@patch("src.celery.beat_schedule.ApiClient")
def test_get_dynamic_schedule_builds_entry_for_each_search(mock_client_cls, _):
    from src.celery.beat_schedule import get_dynamic_schedule

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.get_active_search_configs.return_value = [
        {"id": 1, "preferred_time": "08:00:00", "frequency_days": 1},
        {"id": 2, "preferred_time": "14:30:00", "frequency_days": 7},
    ]

    result = get_dynamic_schedule()

    assert "run_search_1" in result
    assert "run_search_2" in result
    assert result["run_search_1"]["task"] == "src.celery.tasks.run_scraper_search"
    assert result["run_search_1"]["args"] == (1,)
    assert result["run_search_2"]["args"] == (2,)


@patch("src.celery.beat_schedule._get_celery_worker_token", return_value="tok")
@patch("src.celery.beat_schedule.ApiClient")
def test_get_dynamic_schedule_skips_entries_without_id(mock_client_cls, _):
    from src.celery.beat_schedule import get_dynamic_schedule

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.get_active_search_configs.return_value = [
        {"preferred_time": "08:00:00", "frequency_days": 1},
    ]

    result = get_dynamic_schedule()
    assert result == {}


# ---------------------------------------------------------------------------
# _parse_time
# ---------------------------------------------------------------------------


def test_parse_time_from_string():
    from src.celery.beat_schedule import _parse_time

    assert _parse_time("14:30:00") == (14, 30)
    assert _parse_time("08:00") == (8, 0)


def test_parse_time_from_time_object():
    from datetime import time as dtime

    from src.celery.beat_schedule import _parse_time

    assert _parse_time(dtime(9, 15)) == (9, 15)


def test_parse_time_fallback():
    from src.celery.beat_schedule import _parse_time

    assert _parse_time(None) == (0, 0)
    assert _parse_time(12345) == (0, 0)


# ---------------------------------------------------------------------------
# DynamicScheduler.sync_from_api
# ---------------------------------------------------------------------------


@patch("src.celery.beat_schedule.get_dynamic_schedule")
@patch("src.celery.beat_schedule.ScheduleEntry")
def test_sync_from_api_populates_schedule(mock_entry_cls, mock_get_schedule):
    from src.celery.beat_schedule import DynamicScheduler

    schedule_data = {
        "run_search_1": {
            "task": "src.celery.tasks.run_scraper_search",
            "schedule": MagicMock(),
            "args": (1,),
        }
    }
    mock_get_schedule.return_value = schedule_data

    mock_entry = MagicMock()
    mock_entry_cls.return_value = mock_entry

    scheduler = DynamicScheduler.__new__(DynamicScheduler)
    scheduler.schedule = {}
    scheduler.app = MagicMock()

    scheduler.sync_from_api()

    assert "run_search_1" in scheduler.schedule
    assert scheduler.schedule["run_search_1"] is mock_entry
    mock_entry_cls.assert_called_once()


@patch("src.celery.beat_schedule.get_dynamic_schedule")
@patch("src.celery.beat_schedule.ScheduleEntry")
def test_sync_from_api_clears_old_entries_first(mock_entry_cls, mock_get_schedule):
    from src.celery.beat_schedule import DynamicScheduler

    mock_get_schedule.return_value = {}

    scheduler = DynamicScheduler.__new__(DynamicScheduler)
    mock_schedule = MagicMock()
    scheduler.schedule = mock_schedule
    scheduler.app = MagicMock()

    scheduler.sync_from_api()

    mock_schedule.clear.assert_called_once()
