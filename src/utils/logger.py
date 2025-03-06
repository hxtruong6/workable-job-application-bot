import sys
from pathlib import Path
from loguru import logger
from src.config.settings import settings

# Remove default logger
logger.remove()

# Configure console logging
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True,
)

# Configure file logging
logger.add(
    settings.LOG_FILE,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.LOG_LEVEL,
    rotation="500 MB",
    retention="10 days",
    compression="zip",
)


def get_logger(name: str):
    """Get a logger instance with the specified name."""
    return logger.bind(name=name)
