import json
from dataclasses import dataclass
from typing import List

from .settings import CONFIG


@dataclass
class _OverpriceSettings:
    max_overprice_sticker: int
    max_overprice_float: int


@dataclass
class _StickerSettings:
    min_item_price: int
    max_item_price: int
    min_total_sticker_price: int
    search_sticker_qualities: List[str]


@dataclass
class _SearchSettingsData:
    overprice: _OverpriceSettings
    sticker: _StickerSettings


class SearchSettings:
    __slots__ = ["overprice", "sticker"]

    def __init__(self):
        settings = self.load_search_settings()
        self.overprice = settings.overprice
        self.sticker = settings.sticker

    def load_search_settings(
        self,
        filename: str = CONFIG.path.search_settings_filename,
    ) -> _SearchSettingsData:
        file_path = f"{CONFIG.path.data_directory}/{filename}.json"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            default_settings = self._get_default_settings()
            self._save_settings_to_file(default_settings, filename)
            return default_settings

        return _SearchSettingsData(
            overprice=_OverpriceSettings(
                max_overprice_sticker=data["overprice_settings"][
                    "max_overprice_sticker"
                ],
                max_overprice_float=data["overprice_settings"]["max_overprice_float"],
            ),
            sticker=_StickerSettings(
                min_item_price=data["sticker_search_settings"][
                    "min_item_sticker_price"
                ],
                max_item_price=data["sticker_search_settings"][
                    "max_item_sticker_price"
                ],
                min_total_sticker_price=data["sticker_search_settings"][
                    "min_total_sticker_price"
                ],
                search_sticker_qualities=data["sticker_search_settings"][
                    "search_sticker_qualities"
                ],
            ),
        )

    def change_search_settings(self, new_settings: _SearchSettingsData):
        self.overprice = new_settings.overprice
        self.sticker = new_settings.sticker
        self._save_settings_to_file(new_settings)

    def _save_settings_to_file(
        self,
        settings: _SearchSettingsData,
        filename: str = CONFIG.path.search_settings_filename,
    ):
        file_path = f"{CONFIG.path.data_directory}/{filename}.json"

        data = {
            "overprice_settings": {
                "max_overprice_sticker": settings.overprice.max_overprice_sticker,
                "max_overprice_float": settings.overprice.max_overprice_float,
            },
            "sticker_search_settings": {
                "min_item_sticker_price": settings.sticker.min_item_price,
                "max_item_sticker_price": settings.sticker.max_item_price,
                "min_total_sticker_price": settings.sticker.min_total_sticker_price,
                "search_sticker_qualities": settings.sticker.search_sticker_qualities,
            },
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def _get_default_settings(self) -> _SearchSettingsData:
        return _SearchSettingsData(
            overprice=_OverpriceSettings(
                max_overprice_sticker=6, max_overprice_float=15
            ),
            sticker=_StickerSettings(
                min_item_price=0,
                max_item_price=10000,
                min_total_sticker_price=5,
                search_sticker_qualities=[
                    "Battle-Scarred",
                    "Well-Worn",
                    "Field-Tested",
                    "Minimal Wear",
                    "Factory New",
                ],
            ),
        )


SEARCH = SearchSettings()
