import asyncio

import aiohttp
from aiohttp_socks import ProxyConnector, ProxyError

from config import CONFIG
from exceptions import RequestError
from utils import api_sleep, get_proxy


@api_sleep(sleep=CONFIG.sleep.global_sleep)
async def fetch_data(url) -> dict:
    await asyncio.sleep(CONFIG.sleep.request_sleep)
    proxy_url = get_proxy(CONFIG.proxy_list)["url"]

    try:
        connector = ProxyConnector.from_url(proxy_url) if proxy_url else None
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                raise RequestError(response.status)

    except (aiohttp.ClientOSError, ProxyError):
        raise RequestError(f"bad proxy connection: {proxy_url}")

    except aiohttp.ConnectionTimeoutError:
        raise RequestError("connection timeout")


async def fetch_inner_data(url: str) -> dict:
    """Use only for localhost requests

    Args:
        url (str): http://localhost:port/...

    Returns:
        dict: data
    """

    await asyncio.sleep(1.5)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                raise RequestError(response.status)

    except aiohttp.ConnectionTimeoutError:
        raise RequestError("connection timeout")
