import asyncio, os, logging
import discord
from discord.ext import commands
from dotenv import load_dotenv


os.makedirs("log", exist_ok=True)  # Creates the 'log' folder if it doesn't exist
os.makedirs("data", exist_ok=True)  # Creates the 'data' folder if it doesn't exist


# --- Load environment variables ---
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
debug_level_str = os.getenv("DEBUG", "ERROR").upper()
DEBUG_LEVEL = getattr(logging, debug_level_str, logging.ERROR)

# --- Setup logging BEFORE defining loggers ---
os.makedirs("log", exist_ok=True)
logging.basicConfig(
    level=DEBUG_LEVEL,
    filename='log/bot.log', 
    filemode='w',
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)

logger = logging.getLogger(__name__)

# --- Configure bot intents ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Events ---
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.do_not_disturb,
        activity=discord.Activity(type=discord.ActivityType.listening, name='tessst')
    )
    logger.info("The bot is ready!")
    logger.info("-" * 20)

# --- Sync slash commands ---
@bot.command(name="sync")
async def sync(ctx):
    synced = await bot.tree.sync()
    logger.info(f"Synced {len(synced)} command(s).")

# --- Load Cogs ---
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

# --- Entry point ---
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
