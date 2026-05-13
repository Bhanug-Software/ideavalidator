import sys
from loguru import logger

def setup_logger():
    """Configure loguru logger"""

    # Remove default handler
    logger.remove()

    # Console output with colors (only INFO and above)
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <white>{message}</white>",
        colorize=True,
    )

    # File logging with rotation
    logger.add(
        "logs/ideavalidator.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
    )

    return logger

# Initialize logger
logger = setup_logger()
