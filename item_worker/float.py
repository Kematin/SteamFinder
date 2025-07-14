import asyncio
from typing import AsyncIterator, List, Optional

from loguru import logger

from api import fetch_inner_data
from config import CONFIG, SEARCH, configure_loguru
from exceptions import RequestError
from schemas import FloatItemInfo, ItemBase

from .base import (
    get_average_price,
    get_base_items,
    get_normal_items,
    get_raw_items_data,
)


def _check_float(float_value: float) -> bool:
    if float_value < 0.01:
        return True
    if 0.07 <= float_value <= 0.08:
        return True
    if 0.15 <= float_value <= 0.18:
        return True
    if 0.38 <= float_value <= 0.39:
        return True
    if float_value >= 0.99:
        return True
    return False


def _pretty_message_item(item: FloatItemInfo, start: int):
    url = f"https://steamcommunity.com/market/listings/730/{item.name}"
    url = url.replace(" ", "%20")

    message = (
        "Page: {page}\nURL:\n{url}"
        + "\n\nItem: {name}\nAverage Price: <b>{average_price}$</b>\nPrice: <b>{price}$</b>"
        + "\n\nFloat Overprice: {overprice}$\nFloat Overprice %: {overprice_percent}%"
        + "\n\nFloat: <b>{float_value}</b>\nPattern: <b>{pattern}</b>"
    )

    return message.format(
        page=(start % 10) + 1,
        url=url,
        float_value=item.float_value,
        pattern=item.pattern,
        overprice=round(item.price - item.average_price, 2),
        overprice_percent=item.overprice,
        name=item.name,
        price=item.price,
        average_price=round(item.average_price, 2),
    )


async def _get_items_info(
    base_items: List[ItemBase], *, raw_items: dict, average_price: int
) -> List[FloatItemInfo]:
    items = []

    for item in base_items:
        listing = raw_items["listinginfo"][item.listing_id]

        asset_id = listing["asset"]["id"]
        game_link = listing["asset"]["market_actions"][0]["link"]
        game_link = game_link.replace("%listingid%", item.listing_id)
        game_link = game_link.replace("%assetid%", asset_id)

        url = f"{CONFIG.service.float_service_url}/?url={game_link}"
        async with CONFIG.global_lock:
            try:
                response = await fetch_inner_data(url)
            except RequestError:
                logger.warning(f"bad float request, sleep 10 secs: {url}")
                await asyncio.sleep(10)
                continue
        data = response["iteminfo"]

        new_item = FloatItemInfo(
            listing_id=item.listing_id,
            name=item.name,
            price=item.price,
            average_price=average_price,
            float_value=data["floatvalue"],
            pattern=data["paintseed"],
        )

        items.append(new_item)

    return items


async def find_success_item(
    item_name: str,
    *,
    start: int,
    average_price: int,
    max_overpice_percent: int = SEARCH.settings.overprice.max_overprice_float,
) -> AsyncIterator[Optional[FloatItemInfo]]:
    raw_items = await get_raw_items_data(item_name, start=start)
    base_items = await get_base_items(raw_items)
    items = await _get_items_info(
        base_items, raw_items=raw_items, average_price=average_price
    )

    if not items:
        yield None

    items = sorted(items, key=lambda item: item.price)
    max_price = average_price * 1.5

    for item in items:
        logger.debug(f"item {item}")
        if item.overprice <= max_overpice_percent and _check_float(item.float_value):
            yield item
        if item.price > max_price:
            yield None

    yield 1


async def find_items(item_name: str, max_page: int = 3) -> AsyncIterator[str]:
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

            logger.debug(f"FIND {item}")
            message = _pretty_message_item(item, start)
            logger.info(message)
            yield message

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

        await asyncio.gather(*tasks)

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
