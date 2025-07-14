import asyncio

from loguru import logger

from cache_worker.create_cache import main as update_cache
from config import configure_loguru
from item_worker.float import main as float_search_items
from item_worker.stickers import main as sticker_search_items
from item_worker.update_stickers import main as sticker_update


async def select_function():
    functions = {
        1: sticker_search_items,
        2: float_search_items,
        3: sticker_update,
        4: update_cache,
    }
    message = "Select option:\n1. Sticker items\n2. Float search\n3. Update sticker base\n4. Update cache\n"
    num = int(input(message))
    await functions[num]()


if __name__ == "__main__":
    try:
        configure_loguru(logger)
        asyncio.run(select_function())
    except KeyboardInterrupt:
        logger.warning("End.")
