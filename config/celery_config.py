from celery import Celery
from celery.schedules import crontab


def configure_schedule(app: Celery):
    app.conf.beat_schedule = {
        "weekly-sticker-update": {
            "task": "tasks.slow_sticker_task",
            "schedule": crontab(day_of_week=1, hour=7, minute=30),
            "args": (),
        },
        "daily-sticker-cache-create": {
            "task": "tasks.create_sticker_cache",
            "schedule": crontab(hour=10, minute=30),
            "args": (),
        },
    }
