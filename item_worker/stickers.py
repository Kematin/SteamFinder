import asyncio
from typing import AsyncIterator, List, Optional, Tuple

from bs4 import BeautifulSoup
from loguru import logger

from cache_worker.receive_cache import receive_sticker_price
from config import CONFIG, SEARCH, configure_loguru
from schemas import ItemBase, StickerInfo, StickerItemInfo
from utils import normalize_name

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
    base_items: List[ItemBase], raw_items: dict, average_price: int
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
            price=item.price,
            average_price=average_price,
            sticker_info=stickers,
            total_stickers_price=total_stickers_price,
        )

        items.append(new_item)

    return items


def _pretty_message_item(item: StickerItemInfo, start: int):
    url = f"https://steamcommunity.com/market/listings/730/{item.name}"
    url = url.replace(" ", "%20")

    message = (
        "Page: {page}\nURL:\n{url}\n\nItem: {name}\nAverage Price: <b>{average_price}$</b>\nPrice: <b>{price}$</b>"
        + "\n\nSticker overprice <b>{overprice}$</b>\nSticker overpice %: <b>{overprice_percent}%</b>\nStickers total price: <b>{stickers_price}$</b>"
        + "\n\nStickers {stickers_count}: {sticker_info}"
    )
    sticker_info = ""
    for sticker in item.sticker_info:
        sticker_info += f"\n{sticker['name']}, Price: {round(sticker['price'], 2)}$"

    return message.format(
        page=(start // 10) + 1,
        url=url,
        name=item.name,
        price=item.price,
        average_price=round(item.average_price, 2),
        overprice=round(item.price - item.average_price, 2),
        overprice_percent=item.overprice,
        stickers_count=len(item.sticker_info),
        stickers_price=round(item.total_stickers_price, 2),
        sticker_info=sticker_info,
    )


async def find_success_item(
    item_name: str,
    *,
    start: int,
    average_price: int,
    max_overpice_percent: int = SEARCH.settings.overprice.max_overprice_sticker,
) -> AsyncIterator[Optional[StickerItemInfo]]:
    raw_items = await get_raw_items_data(item_name, start=start)
    base_items = await get_base_items(raw_items)
    items = await _get_items_info(base_items, raw_items, average_price)

    if not items:
        yield None

    items = sorted(items, key=lambda item: item.price)
    max_price = average_price * 1.5
    logger.debug(f"Receive items {item_name} on page {(start // 10) + 1}")

    for item in items:
        if item.overprice <= max_overpice_percent:
            yield item
        if item.price > max_price:
            yield None

    yield 1


async def find_items(
    item_name: str, max_page: int = 3
) -> AsyncIterator[Tuple[str, str]]:
    logger.info(
        f"Search item {item_name.replace('%20', ' ').replace('%E2%84%A2', 'TM')}"
    )
    start = 0
    average_price = await get_average_price(item_name)
    while start <= max_page * 10:
        flag = False

        async for item in find_success_item(
            item_name, start=start, average_price=average_price
        ):
            if item is None:
                flag = True
                break
            if item == 1:
                break

            message = _pretty_message_item(item, start)
            logger.info(message)
            yield (item.listing_id, message)

        if flag:
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


if __name__ == "__main__":
    try:
        configure_loguru(logger)
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.warning("END.")
