from typing import List

from schemas import ProxyInfo

from .settings import CONFIG


def read_proxy(proxy_list: List[None], filename: str = CONFIG.path.proxy_filename):
    with open(f"{CONFIG.path.data_directory}/{filename}.txt", "r") as f:
        lines = f.readlines()
        for raw_url in lines:
            ip, port, user, password = raw_url.strip().split(":")
            url = f"socks5://{user}:{password}@{ip}:{port}"
            new_proxy: ProxyInfo = {"url": url, "is_used": False}
            proxy_list.append(new_proxy)
