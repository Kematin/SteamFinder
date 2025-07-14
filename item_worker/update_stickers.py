import asyncio
import json
from typing import List

import aiofiles
from loguru import logger

from api import fetch_data
from config import CONFIG, configure_loguru
from schemas import StickerInfo
from utils import normalize_name


async def _write_json(filename: str, items: List[StickerInfo]) -> None:
    filename = f"{CONFIG.path.stickers_folder}/{filename}.json"

    try:
        async with aiofiles.open(filename, mode="r") as f:
            data = json.loads(await f.read())
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    for new_item in items:
        data.append(new_item)

    async with aiofiles.open(filename, mode="w") as f:
        await f.write(json.dumps(data, indent=2, ensure_ascii=False))


async def _get_raw_sticker_data(sticker: str, start: int) -> dict:
    url = f"https://steamcommunity.com/market/search/render/?query={sticker}&start={start}&count=10&search_descriptions=0&sort_column=default&sort_dir=desc&appid=730&category_730_ItemSet[]=any&category_730_ProPlayer[]=any&category_730_Tournament[]=any&category_730_TournamentTeam[]=any&category_730_Type[]=any&category_730_Weapon[]=any&norender=1"
    url = url.replace(" ", "%20")
    response = await fetch_data(url)
    while not response:
        response = await fetch_data(url)

    return response


async def _get_sticker_page_size(sticker: str) -> int:
    response = await _get_raw_sticker_data(sticker, 0)
    total_count: int = response["searchdata"]["total_count"]
    return total_count


async def _get_sticker_info(sticker: str, start: int) -> List[StickerInfo]:
    response = await _get_raw_sticker_data(sticker, start)
    data: List[dict] = response["results"]

    items = []

    for item_data in data:
        name = item_data["name"]
        price = (item_data["sell_price"] / 100) * 0.9

        if "Sticker" not in name:
            continue
        if price < 2.5:
            continue

        new_item: StickerInfo = {"name": name, "price": price}
        items.append(new_item)

    return items


async def find_by_name(sticker: str):
    start = 0
    total_count = await _get_sticker_page_size(sticker)
    while start < total_count:
        logger.info(
            f"Make request for sticker {sticker} ; Start {start} ; End {total_count}"
        )
        items = await _get_sticker_info(sticker, start)
        if items:
            await _write_json(normalize_name(sticker), items)
        start += 10


async def main(stickers: List[str] = CONFIG.sticker.items):
    tasks = []
    try:
        for sticker in stickers:
            task = asyncio.create_task(find_by_name(sticker))
            tasks.append(task)

            await asyncio.sleep(1.5)

        await asyncio.gather(*tasks, return_exceptions=True)

    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise


if __name__ == "__main__":
    configure_loguru(logger)
    asyncio.run(main())
    logger.warning("END.")
