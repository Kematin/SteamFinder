from random import shuffle
from typing import List

from loguru import logger

from config import CONFIG
from utils.api import fetch_data
from utils.schemas import ItemBase

BASE_URL = "https://steamcommunity.com/market/listings/730/{name}/render/?query=&start={start}&count=10&country=NL&language=english&currency=1"


def _get_item_list(filename: str) -> List[str]:
    items = []
    with open(f"{CONFIG.path.data_directory}/{filename}.txt", "r") as f:
        for row in f:
            items.append(row)

    return items


def _normalize_items(items: List[str]) -> List[str]:
    qualities = [
        "(Field-Tested)",
        "(Minimal Wear)",
        "(Factory New)",
        "(Well-Worn)",
        "(Battle-Scarred)",
    ]
    normal_items = []
    for item in items:
        for st in ["", "StatTrak%E2%84%A2%20"]:
            for quality in qualities:
                normal_item = st + item.replace("\n", "") + " " + quality
                normal_item = normal_item.strip().replace(" ", "%20").replace("\n", "")
                normal_items.append(normal_item)

    shuffle(normal_items)
    return normal_items


def get_normal_items(
    items_filename: str = CONFIG.path.items_filename, is_raw: bool = True
):
    if is_raw:
        item_names = _normalize_items(_get_item_list(items_filename))
    else:
        item_names = _get_item_list(items_filename)
    return item_names


async def get_raw_items_data(item: str, start: int = 0) -> List[dict]:
    url = BASE_URL.format(name=item, start=start)
    url = url.replace(" ", "%20")

    response = await fetch_data(url)
    while not response:
        response = await fetch_data(url)
    data = response

    return data


async def get_base_items(raw_items: dict) -> List[ItemBase]:
    items = []

    try:
        listings: dict = raw_items["listinginfo"]
        assets: dict = raw_items["assets"]["730"]["2"]
    except (KeyError, TypeError):
        return items

    for listing_id, listing in listings.items():
        asset_id = listing["asset"]["id"]
        asset = assets[asset_id]

        try:
            price = (listing["converted_price"] + listing["converted_fee"]) / 100
            name = asset["market_name"]
        except KeyError:
            logger.warning(f"Key error in listing: {listing}")
            continue

        new_item = ItemBase(listing_id=listing_id, name=name, price=price)

        items.append(new_item)

    return items


async def get_average_price(item_name: str, count: int = 3) -> int:
    """Get the average price from items.
    For best result, put only the first N items

    Args:
        item_name (str),
        count (int, optional): How many items affect the price. Defaults to 3.

    Returns:
        average_price: int
    """

    raw_items = await get_raw_items_data(item_name, start=0)
    items = await get_base_items(raw_items)

    average_price = 0
    for i, item in enumerate(items):
        average_price += item.price
        if i == (count - 1):
            break

    return average_price / count
