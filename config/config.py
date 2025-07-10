import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read and validate Discord token
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing from environment variables.")

# Read debug level
debug_level_str = os.getenv("DEBUG", "ERROR").upper()
DEBUG_LEVEL = getattr(logging, debug_level_str, logging.ERROR)

# Optional: create log directory
os.makedirs("log", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=DEBUG_LEVEL,
    filename="log/bot.log",
    filemode="w",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("discord_bot")
logger.info("Logging initialized with level: %s", debug_level_str)
