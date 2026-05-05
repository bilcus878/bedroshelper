import sys
import os
from loguru import logger as _logger
from config import LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)

_logger.remove()
_logger.add(
    sys.stderr,
    level="INFO",
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
)
_logger.add(
    f"{LOG_DIR}/bot.log",
    rotation="10 MB",
    retention=3,
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

logger = _logger
