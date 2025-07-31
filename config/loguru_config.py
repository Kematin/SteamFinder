import logging
import sys

from loguru import logger

from .settings import CONFIG


class LoguruInterceptHandler(logging.Handler):
    LEVELS_MAP = {
        logging.CRITICAL: "CRITICAL",
        logging.ERROR: "ERROR",
        logging.WARNING: "WARNING",
        logging.INFO: "INFO",
        logging.DEBUG: "DEBUG",
    }

    def _get_level(self, record):
        return self.LEVELS_MAP.get(record.levelno, record.levelno)

    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(self._get_level(record), record.getMessage())


def configure_logger(capture_exceptions: bool = False, subfolder: str = None) -> None:
    config = CONFIG
    logger.remove()

    level = "DEBUG" if config.debug else "INFO"
    log_format = "log_{time:YYYY-MM-DD}.log"

    logger.add(
        f"logs/{log_format}" if not subfolder else f"logs/{subfolder}/{log_format}",
        rotation="12:00",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}",
        level="INFO",
        encoding="utf-8",
        compression="zip",
        colorize=True,
    )
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | "
        + "<level>{level}</level> | {file}:{line} | "
        "{message}",
        level=level,
    )
    if capture_exceptions:
        logger.add(
            f"logs/errors/error_{log_format}"
            if not subfolder
            else f"logs/{subfolder}/errors/error_{log_format}",
            rotation="12:00",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}",
            level="ERROR",
            encoding="utf-8",
            compression="zip",
        )

    level = logging.DEBUG if config.debug else logging.INFO
    logging.basicConfig(handlers=[LoguruInterceptHandler()], level=level)
