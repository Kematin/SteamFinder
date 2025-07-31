import asyncio
from typing import List

from celery_app import app
from service.cache.create_cache import main as create_cache
from service.finder.update_stickers import find_by_name as fast_finder
from service.finder.update_stickers import main as slow_finder


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
