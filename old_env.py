"""
import logging
import sys
from asyncio import Lock
from typing import List

from celery import Celery
from celery.schedules import crontab
from loguru import logger
from redis.asyncio import Redis

from schemas import ProxyInfo

GLOBAL_LOCK = Lock()
GLOBAL_SLEEP_TIME = 15
TASK_SLEEP_TIME = 0
REQUEST_SLEEP_TIME = 0
MAX_OVERPRICE_STICKER = 6
MAX_OVERPRICE_FLOAT = 15
FAST_MODE = False
DEBUG = True
PROXY_LIST: List[ProxyInfo] = []
STICKERS = [
    "Katowice 2014",
    "DreamHack 2014",
    "Cologne 2014",
    "Katowice 2015",
    "Cologne 2015",
    "Cluj-Napoca 2015",
    "Columbus 2016",
    "Cologne 2016",
    "Atlanta 2017",
    "Krakow 2017",
    "Boston 2018",
    "London 2018",
    "Katowice 2019",
    "Berlin 2019",
    "Sticker | Battle Scarred",
    "Sticker | Stockholm 2021",
    "Sticker | Antwerp 2022",
    "Sticker | Rio 2022",
    "Sticker | Paris 2023",
]
STICKERS_FOLDER = "stickers"
DATA_DIRECTORY = "data"
ITEMS_FILENAME = "items"
PROXY_FILENAME = "proxy"
REDIS_URL = "redis://localhost:6379/{db}"
FLOAT_SERVICE_URL = "http://localhost:8001"
REDIS = Redis.from_url(REDIS_URL.format(db=0))


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_loguru(logger, debug: bool = DEBUG):
    logger.remove()

    logger.add(
        sink=sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>",
        colorize=True,
        level="DEBUG" if debug else "INFO",
        backtrace=True,
        diagnose=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


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

"""
