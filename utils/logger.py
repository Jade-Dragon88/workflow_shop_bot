import sys
import logging
from loguru import logger

class InterceptHandler(logging.Handler):
    """
    A handler to intercept standard logging messages and redirect them to Loguru.
    """
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logger(log_file_path: str, level: str = "INFO", rotation: str = "1 week", retention: str = "1 month"):
    """
    Configures the Loguru logger.
    
    This function sets up a logger that outputs to both the console and a file.
    It also intercepts standard Python logging to ensure all logs are handled by Loguru.
    """
    # Remove default handler and add a new one with a custom format
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add a file handler for logging to a file
    logger.add(
        log_file_path,
        level=level,
        rotation=rotation,
        retention=retention,
        enqueue=True,  # Make it process-safe
        backtrace=True,
        diagnose=True,
        format="{time} {level} {message}"
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logging.getLogger("aiogram").setLevel(logging.INFO)
    
    logger.info("Logger configured successfully.")

