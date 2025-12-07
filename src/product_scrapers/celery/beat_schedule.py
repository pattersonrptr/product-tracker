import time

from celery.schedules import crontab
# from src.app.infrastructure.database.models.search_config_model import SearchConfig
from celery.beat import Scheduler, ScheduleEntry


def get_dynamic_schedule():
    from src.app.infrastructure.database_config import SessionLocal

    db = SessionLocal()
    try:
        schedules = {}
        searches = db.query(SearchConfig).filter(SearchConfig.is_active).all()

        for idx, search in enumerate(searches):
            schedules[f"run_search_{search.id}"] = {
                "task": "src.product_scrapers.celery.tasks.run_scraper_search",
                "schedule": crontab(
                    hour=search.preferred_time.hour,
                    minute=search.preferred_time.minute,
                    day_of_month=f"*/{search.frequency_days}",
                ),
                "args": (search.id,),
            }
        return schedules
    finally:
        db.close()


class DynamicDBScheduler(Scheduler):
    # last_sync = 0
    # sync_interval = 10

    def setup_schedule(self):
        while True:
            time.sleep(10)
            self.tick()
            self.sync_from_db()

    def sync_from_db(self):
        print("DynamicDBScheduler is running...")

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

    # def tick(self):
    #     now = time.time()
    #     if now - self.last_sync > self.sync_interval:
    #         self.sync_from_db()
    #         self.last_sync = now
    #     return super().tick()


# Celery beat static scheduling example:
# app.conf.beat_schedule = {
#     "run_olx_searches_daily": {
#         "task": "src.product_scrapers.celery.tasks.run_scraper_search",
#         "schedule": crontab(hour="00", minute="00"),
#         "args": ("olx",),
#     },
#     "run_enjoei_searches_daily": {
#         "task": "src.product_scrapers.celery.tasks.run_scraper_search",
#         "schedule": crontab(hour="01", minute="00"),
#         "args": ("enjoei",),
#     },
#     "run_olx_scraper_update_daily": {
#         "task": "scrapers.tasks.run_scraper_update",
#         "schedule": crontab(hour="02", minute="00"),
#         "args": ("olx",),
#     },
#     "run_enjoei_scraper_update_daily": {
#         "task": "scrapers.tasks.run_scraper_update",
#         "schedule": crontab(hour="03", minute="00"),
#         "args": ("enjoei",),
#     },
# }
