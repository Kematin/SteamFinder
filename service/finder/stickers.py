import asyncio
from typing import AsyncIterator, List, Optional

from bs4 import BeautifulSoup
from loguru import logger

from config import CONFIG
from service.cache.receive_cache import receive_sticker_price
from utils.schemas import ItemBase, StickerInfo, StickerItemInfo
from utils.utils import normalize_name

from .base import (
    get_average_price,
    get_base_items,
    get_normal_items,
    get_raw_items_data,
)


async def _get_sticker_info_from_raw(raw_data: dict) -> Optional[List[StickerInfo]]:
    if raw_data["name"] != "sticker_info":
        return None

    stickers = []

    raw_html = raw_data["value"]
    soup = BeautifulSoup(raw_html, "html.parser")
    imgs = soup.find_all("img")
    for img in imgs:
        sticker_name = img.get("title")
        price = await receive_sticker_price(
            normalize_name(sticker_name), CONFIG.redis.client
        )
        if price:
            new_sticker: StickerInfo = {"name": sticker_name, "price": price}
            stickers.append(new_sticker)

    return stickers if stickers else None


async def _get_items_info(
    base_items: List[ItemBase], *, raw_items: dict, average_price: int
) -> List[StickerItemInfo]:
    items = []

    for item in base_items:
        assets: dict = raw_items["assets"]["730"]["2"]
        listing = raw_items["listinginfo"][item.listing_id]

        asset_id = listing["asset"]["id"]
        asset = assets[asset_id]

        raw_stickers_data = asset["descriptions"][-1]
        stickers = await _get_sticker_info_from_raw(raw_stickers_data)
        total_stickers_price = 0
        if stickers:
            for sticker in stickers:
                total_stickers_price += sticker["price"]

        new_item = StickerItemInfo(
            listing_id=item.listing_id,
            name=item.name,
            page=item.page,
            price=item.price,
            average_price=average_price,
            sticker_info=stickers,
            total_stickers_price=total_stickers_price,
        )

        items.append(new_item)

    return items


async def find_success_item(
    item_name: str,
    *,
    start: int,
    average_price: int,
) -> AsyncIterator[Optional[StickerItemInfo]]:
    raw_items = await get_raw_items_data(item_name, start=start)
    base_items = await get_base_items(raw_items, start=start)
    items = await _get_items_info(
        base_items, raw_items=raw_items, average_price=average_price
    )

    if not items:
        yield None

    items = sorted(items, key=lambda item: item.price)
    max_price = average_price * 1.5
    logger.debug(f"Receive items {item_name} on page {(start // 10) + 1}")

    for item in items:
        if item.price > max_price:
            yield None
        if item.sticker_info:
            yield item

    yield 1


async def find_items(
    item_name: str, max_page: int = 3
) -> AsyncIterator[StickerItemInfo]:
    logger.info(
        f"Search item {item_name.replace('%20', ' ').replace('%E2%84%A2', 'TM')}"
    )
    start = 0
    average_price = await get_average_price(item_name)
    while start <= max_page * 10:
        is_finished = False

        async for item in find_success_item(
            item_name, start=start, average_price=average_price
        ):
            if item is None:
                is_finished = True
                break
            if item == 1:
                break

            logger.info(item.message)
            yield item

        if is_finished:
            break

        start += 10


async def main():
    item_names = get_normal_items()
    tasks = []
    try:
        for item_name in item_names:
            task = asyncio.create_task(find_items(item_name))
            tasks.append(task)

            await asyncio.sleep(1.5)

        await asyncio.gather(*tasks, return_exceptions=False)

    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
