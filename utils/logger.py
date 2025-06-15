# logger.py
import logging

logger = logging.getLogger("documenter ai logger")
logger.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Format
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] - %(name)s - %(message)s"
)
console_handler.setFormatter(formatter)

# Add the handler if not already added
if not logger.handlers:
    logger.addHandler(console_handler)
