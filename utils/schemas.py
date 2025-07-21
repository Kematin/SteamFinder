from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Optional, TypedDict


class StickerInfo(TypedDict):
    name: str
    price: float


class ProxyInfo(TypedDict):
    url: str
    is_used: bool


@dataclass
class ItemBase:
    listing_id: str
    name: str
    page: int
    price: int

    @abstractmethod
    def message(self):
        pass


@dataclass
class StickerItemInfo(ItemBase):
    average_price: int
    sticker_info: Optional[List[StickerInfo]]
    total_stickers_price: int = 0

    @property
    def overprice(self) -> float:
        if not self.total_stickers_price:
            return 100
        overprice = round(
            (self.price - self.average_price) / (self.total_stickers_price / 100), 2
        )
        return overprice

    @property
    def message(self) -> str:
        url = f"https://steamcommunity.com/market/listings/730/{self.name}"
        url = url.replace(" ", "%20")

        message = (
            "Page: {page}\nURL:\n{url}\n\nItem: {name}\nAverage Price: <b>{average_price}$</b>\nPrice: <b>{price}$</b>"
            + "\n\nSticker overprice <b>{overprice}$</b>\nSticker overpice %: <b>{overprice_percent}%</b>\nStickers total price: <b>{stickers_price}$</b>"
            + "\n\nStickers {stickers_count}: {sticker_info}"
        )

        sticker_info = ""
        for sticker in self.sticker_info:
            sticker_info += f"\n{sticker['name']}, Price: {round(sticker['price'], 2)}$"

        return message.format(
            page=self.page,
            url=url,
            name=self.name,
            price=self.price,
            average_price=round(self.average_price, 2),
            overprice=round(self.price - self.average_price, 2),
            overprice_percent=self.overprice,
            stickers_count=len(self.sticker_info),
            stickers_price=round(self.total_stickers_price, 2),
            sticker_info=sticker_info,
        )


@dataclass
class FloatItemInfo(ItemBase):
    average_price: int
    float_value: float
    pattern: int

    @property
    def overprice(self) -> float:
        overprice = round(
            (self.price - self.average_price) / self.average_price * 100, 2
        )

        return overprice

    @property
    def message(self) -> str:
        url = f"https://steamcommunity.com/market/listings/730/{self.name}"
        url = url.replace(" ", "%20")

        message = (
            "Page: {page}\nURL:\n{url}"
            + "\n\nItem: {name}\nAverage Price: <b>{average_price}$</b>\nPrice: <b>{price}$</b>"
            + "\n\nFloat Overprice: {overprice}$\nFloat Overprice %: {overprice_percent}%"
            + "\n\nFloat: <b>{float_value}</b>\nPattern: <b>{pattern}</b>"
        )

        return message.format(
            page=self.page,
            url=url,
            float_value=self.float_value,
            pattern=self.pattern,
            overprice=round(self.price - self.average_price, 2),
            overprice_percent=self.overprice,
            name=self.name,
            price=self.price,
            average_price=round(self.average_price, 2),
        )
