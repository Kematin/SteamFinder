from .celery_config import configure_schedule
from .loguru_config import configure_loguru
from .proxy_config import read_proxy
from .search_config import SEARCH
from .settings import CONFIG

read_proxy(CONFIG.proxy_list)

__all__ = [CONFIG, configure_loguru, configure_schedule, SEARCH]
