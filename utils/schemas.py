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
    price: int


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
