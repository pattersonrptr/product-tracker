import logging
import time
from datetime import datetime

from celery.beat import ScheduleEntry, Scheduler
from celery.schedules import crontab

from src.api.api_client import ApiClient

logger = logging.getLogger(__name__)


def _get_celery_worker_token():
    """Re-use the same auth helper used by Celery tasks."""
    import os

    import requests

    api_base_url = os.getenv("API_URL", "http://web:8000")
    auth_url = f"{api_base_url}/auth/login"
    payload = {
        "username": os.getenv("CELERY_WORKER_USERNAME"),
        "password": os.getenv("CELERY_WORKER_PASSWORD"),
        "grant_type": "password",
        "scope": "",
        "client_id": "",
        "client_secret": "",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(auth_url, data=payload, headers=headers)
        response.raise_for_status()
        body = response.json()
        token = body.get("data", {}).get("attributes", {}).get(
            "access_token"
        ) or body.get("access_token")
        return token
    except requests.exceptions.RequestException as e:
        logger.error("Error retrieving Celery worker token for beat: %s", e)
        return None


def _parse_time(value) -> tuple[int, int]:
    """Extract hour and minute from a time string or time object."""
    if hasattr(value, "hour") and hasattr(value, "minute"):
        return value.hour, value.minute
    if isinstance(value, str):
        try:
            parsed = datetime.strptime(value, "%H:%M:%S").time()
            return parsed.hour, parsed.minute
        except ValueError:
            parsed = datetime.strptime(value, "%H:%M").time()
            return parsed.hour, parsed.minute
    return 0, 0


def get_dynamic_schedule():
    """Fetch active search configs via the backend HTTP API."""
    token = _get_celery_worker_token()
    if not token:
        logger.error("Could not authenticate for beat schedule — skipping sync.")
        return {}

    client = ApiClient(token)
    searches = client.get_active_search_configs()

    schedules = {}
    for search in searches:
        search_id = search.get("id")
        if not search_id:
            continue

        hour, minute = _parse_time(search.get("preferred_time", "00:00"))
        frequency_days = search.get("frequency_days", 1)

        schedules[f"run_search_{search_id}"] = {
            "task": "src.celery.tasks.run_scraper_search",
            "schedule": crontab(
                hour=hour,
                minute=minute,
                day_of_month=f"*/{frequency_days}",
            ),
            "args": (search_id,),
        }
    return schedules


class DynamicScheduler(Scheduler):
    """Celery Beat scheduler that dynamically fetches schedules from the API."""

    def setup_schedule(self):
        while True:
            time.sleep(10)
            self.tick()
            self.sync_from_api()

    def sync_from_api(self):
        logger.info("DynamicScheduler: syncing schedule from API...")

        self.schedule.clear()

        for name, entry in get_dynamic_schedule().items():
            self.schedule[name] = ScheduleEntry(
                name=name,
                task=entry["task"],
                schedule=entry["schedule"],
                args=entry.get("args", ()),
                kwargs=entry.get("kwargs", {}),
                options=entry.get("options", {}),
                app=self.app,
            )
