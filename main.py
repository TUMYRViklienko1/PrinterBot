import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Event: on_ready
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.do_not_disturb,
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name='tessst'
        )
    )
    print("The bot is ready!")
    print("-" * 20)

# Load all cogs from the cogs directory
async def load_cogs():
    cogs_dir = './cogs'
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py'):
            cog_name = filename[:-3]
            await bot.load_extension(f'cogs.{cog_name}')

# Entry point
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
