import asyncio
import json
import os
from typing import List

from loguru import logger
from redis.asyncio import Redis

from config import CONFIG
from utils.schemas import StickerInfo
from utils.utils import normalize_name


async def _read_file(filename: str) -> List[StickerInfo]:
    try:
        filepath = os.path.join(CONFIG.path.stickers_folder, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [
            StickerInfo(name=item["name"], price=float(item["price"])) for item in data
        ]
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Error while reading file {filename}: {e}")
        return []


async def _get_filenames(subfolder: str = CONFIG.path.stickers_folder) -> List[str]:
    try:
        return [f for f in os.listdir(subfolder) if f.endswith(".json")]
    except FileNotFoundError:
        logger.error(f"Folder {subfolder} does not exist")
        return []


async def _create_cache(filename: str, redis: Redis) -> None:
    items = await _read_file(filename)
    if not items:
        return

    added_count = 0

    for item in items:
        cache_key = normalize_name(item["name"])

        await redis.hset(
            cache_key,
            mapping={
                "name": item["name"],
                "price": item["price"],
                "source_file": filename,
            },
        )
        await redis.expire(cache_key, 86400 * 3)  # 3 дня TTL
        added_count += 1

    logger.info(f"File {filename}: added {added_count} stickers")


async def main():
    filenames = await _get_filenames()
    if not filenames:
        logger.warning("Empty folder for recreate cache")
        return

    redis = CONFIG.redis.client

    try:
        if not await redis.ping():
            raise ConnectionError("Redis is off")

        tasks = [
            asyncio.create_task(_create_cache(filename, redis))
            for filename in filenames
        ]
        await asyncio.gather(*tasks)

    finally:
        await redis.aclose()
