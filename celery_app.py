from celery import Celery
from celery.schedules import crontab

from config.settings import CONFIG

CELERY_BROKER_URL = CONFIG.redis.url.format(db=1)
CELERY_RESULT_BACKEND = CONFIG.redis.url.format(db=2)


app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    broker_connection_retry_on_startup=True,
    include=["src.jobs.tasks"],
)


def configure_schedule(app: Celery):
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Europe/Moscow",
        enable_utc=True,
    )

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
