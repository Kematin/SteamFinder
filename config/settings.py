from asyncio import Lock
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio import Redis

from utils.schemas import ProxyInfo

BASE_DIR = Path(__file__).resolve().parent.parent


def get_model_config(env_dir: str = f"{BASE_DIR}/.env"):
    config = SettingsConfigDict(
        env_file=env_dir, env_file_encoding="utf-8", extra="ignore"
    )
    return config


class BotSettings(BaseSettings):
    token: str = Field(alias="BOT_TOKEN")

    model_config = get_model_config()


class RedisSettings(BaseSettings):
    url: str = Field(default="redis://localhost:6379/{db}", alias="REDIS_URL")
    db: int = Field(default=0)

    model_config = get_model_config()

    @property
    def client(self) -> Redis:
        return Redis.from_url(self.url.format(db=self.db))


class SleepSettings(BaseSettings):
    global_sleep: float = Field(default=15, alias="GLOBAL_SLEEP_TIME")
    task_sleep: float = Field(default=0.5, alias="TASK_SLEEP_TIME")
    request_sleep: float = Field(default=0.5, alias="REQUEST_SLEEP_TIME")

    model_config = get_model_config()


class PathSettings(BaseSettings):
    data_directory: str = Field(default="data", alias="DATA_DIRECTORY")
    stickers_folder: str = Field(default="stickers", alias="STICKERS_FOLDER")
    items_filename: str = Field(default="items", alias="ITEMS_FILENAME")
    proxy_filename: str = Field(default="proxy", alias="PROXY_FILENAME")
    search_settings_filename: str = Field(
        default="items_settings", alias="SEARCH_SETTINGS_FILENAME"
    )

    model_config = get_model_config()


class ServiceSettings(BaseSettings):
    float_service_url: str = Field(
        default="http://localhost:8001", alias="FLOAT_SERVICE_URL"
    )

    model_config = get_model_config()


class StickerSettings(BaseSettings):
    items: List[str] = Field(
        default=[
            "Katowice 2014",
            "DreamHack 2014",
            "Cologne 2014",
            "Katowice 2015",
            "Cologne 2015",
            "Cluj-Napoca 2015",
            "Columbus 2016",
            "Cologne 2016",
            "Atlanta 2017",
            "Krakow 2017",
            "Boston 2018",
            "London 2018",
            "Katowice 2019",
            "Berlin 2019",
            "Sticker | Battle Scarred",
            "Sticker | Stockholm 2021",
            "Sticker | Antwerp 2022",
            "Sticker | Rio 2022",
            "Sticker | Paris 2023",
        ],
        alias="STICKERS",
    )

    model_config = get_model_config()


class Config(BaseSettings):
    _bot: BotSettings = None
    _redis: RedisSettings = None
    _sleep: SleepSettings = None
    _path: PathSettings = None
    _service: ServiceSettings = None
    _sticker: StickerSettings = None

    global_lock: Lock = Field(default_factory=Lock)
    proxy_list: List[ProxyInfo] = Field(default_factory=list)
    fast_mode: bool = Field(default=False, alias="FAST_MODE")
    debug: bool = Field(default=True, alias="DEBUG")

    model_config = get_model_config()

    @property
    def bot(self) -> BotSettings:
        if self._bot is None:
            self._bot = BotSettings()
        return self._bot

    @property
    def redis(self) -> RedisSettings:
        if self._redis is None:
            self._redis = RedisSettings()
        return self._redis

    @property
    def sleep(self) -> SleepSettings:
        if self._sleep is None:
            self._sleep = SleepSettings()
        return self._sleep

    @property
    def path(self) -> PathSettings:
        if self._path is None:
            self._path = PathSettings()
        return self._path

    @property
    def service(self) -> ServiceSettings:
        if self._service is None:
            self._service = ServiceSettings()
        return self._service

    @property
    def sticker(self) -> StickerSettings:
        if self._sticker is None:
            self._sticker = StickerSettings()
        return self._sticker


@lru_cache()
def get_config():
    return Config()


CONFIG = get_config()
