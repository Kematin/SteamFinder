import asyncio
import json
import time
from functools import wraps
from typing import Callable, List

import aiofiles
from loguru import logger

from config import CONFIG

from .exceptions import RequestError
from .schemas import ProxyInfo


def api_sleep(sleep: int):
    """Stop global thread for async function
    after except RequestError

    Args:
        sleep (int): sleep time
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with CONFIG.global_lock:
                try:
                    start_time = time.perf_counter()
                    result = await func(*args, **kwargs)
                except RequestError as e:
                    logger.warning(f"Get bad request: {e}, sleep {sleep} secs")
                    await asyncio.sleep(sleep)
                    return 0
                elapsed = time.perf_counter() - start_time
                logger.debug(f"Request by {elapsed:.4f} sec")
                return result

        return wrapper

    return decorator


def get_proxy(proxy_list: List[ProxyInfo]) -> ProxyInfo:
    for proxy in proxy_list:
        if not proxy["is_used"]:
            proxy["is_used"] = True
            return proxy

    for proxy in proxy_list:
        proxy["is_used"] = False

    return proxy_list[0]


def normalize_name[T: str](name: T) -> T:
    return name.replace(" ", "").replace(":", "|").lower()


async def create_test_file(filename: str, data: dict):
    async with aiofiles.open(filename, mode="w") as f:
        await f.write(json.dumps(data, indent=2, ensure_ascii=False))


async def read_test_file(filename: str) -> dict:
    try:
        async with aiofiles.open(filename, mode="r") as f:
            data = json.loads(await f.read())
    except (FileNotFoundError, json.JSONDecodeError):
        data = None

    return data
