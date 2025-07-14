import logging
import sys

from loguru import logger

from .settings import CONFIG


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_loguru(logger, debug: bool = CONFIG.debug):
    logger.remove()

    logger.add(
        sink=sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>",
        colorize=True,
        level="DEBUG" if debug else "INFO",
        backtrace=True,
        diagnose=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
