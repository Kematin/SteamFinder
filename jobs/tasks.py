import asyncio
from typing import List

from celery import Celery

from cache_worker.create_cache import main as create_cache
from config import CONFIG
from item_worker.update_stickers import find_by_name as fast_finder
from item_worker.update_stickers import main as slow_finder

CELERY_BROKER_URL = CONFIG.redis.url.format(db=1)
CELERY_RESULT_BACKEND = CONFIG.redis.url.format(db=2)

app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    broker_connection_retry_on_startup=True,
)


@app.task(bind=True, name="tasks.slow_sticker_task")
def slow_sticker_task(self, stickers: List[str]):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(slow_finder(stickers))
    finally:
        loop.close()


@app.task(bind=True, name="tasks.fast_sticker_task")
def fast_sticker_task(self, sticker_name: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(fast_finder(sticker_name))
    finally:
        loop.close()


@app.task(bind=True, name="tasks.create_sticker_cache")
def create_sticker_cache_task(self):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(create_cache())
    finally:
        loop.close()


def _test_stickers(fast_mode: bool):
    if fast_mode:
        for sticker in CONFIG.sticker.items:
            fast_sticker_task.delay(sticker)
    else:
        slow_sticker_task.delay(CONFIG.sticker.items)


def _test_cache():
    create_sticker_cache_task.delay()


if __name__ == "__main__":
    _test_stickers(CONFIG.fast_mode)
    _test_cache()
