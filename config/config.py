"""Configuration and environment setup for the Discord bot."""

import os
import logging
from dotenv import load_dotenv

LOG_DIR_NAME = "log"  # store log data
DATA_DIR_NAME = "data"  # store data about the printers

# Creates the 'log' and 'data' folders if they don't exist
os.makedirs(LOG_DIR_NAME, exist_ok=True)
os.makedirs(DATA_DIR_NAME, exist_ok=True)

# Load environment variables
load_dotenv()

# Read and validate Discord token
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing from environment variables.")

# Read debug level
debug_level_str = os.getenv("DEBUG", "DEBUG").upper()
DEBUG_LEVEL = getattr(logging, debug_level_str, logging.ERROR)

# Configure logging
logging.basicConfig(
    level=DEBUG_LEVEL,
    filename=os.path.join(LOG_DIR_NAME, "bot.log"),
    filemode="w",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

logger = logging.getLogger("discord_bot")
logger.info("Logging initialized with level: %s", debug_level_str)
