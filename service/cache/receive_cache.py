from typing import Optional

from loguru import logger
from redis.asyncio import Redis

from config import CONFIG
from utils.utils import normalize_name


async def receive_sticker_price(name: str, redis: Redis) -> Optional[float]:
    price = await redis.hget(normalize_name(name), "price")
    if price is None:
        logger.debug(f"Sticker with name {name} wasn`t find in cache")

    return float(price) if price else None


async def main():
    redis = CONFIG.redis.client
    test_data = [
        "Sticker | Jame | Boston 2018",
        "Sticker | devoduvek | Boston 2018",
        "Sticker | fox (Foil) | Cluj-Napoca 2015",
        "Sticker | NONe",
        "Sticker | n0thing (Foil) | Krakow 2017",
    ]

    try:
        if not await redis.ping():
            raise ConnectionError("Redis is off")

        for item in test_data:
            price = await receive_sticker_price(item, redis)
            if price:
                logger.info(f"{item}: {price}")

    finally:
        await redis.aclose()
