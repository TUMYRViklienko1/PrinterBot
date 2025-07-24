"""Main Discord bot entry point."""

import asyncio
import logging
import os

import discord
from discord.ext import commands
from .config import DISCORD_TOKEN


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Called when bot connects."""
    await bot.change_presence(
        status=discord.Status.do_not_disturb,
        activity=discord.Activity(type=discord.ActivityType.listening, name='test')
    )
    logger.info("Bot is ready!")

@bot.command()
async def sync(_):  # Mark ctx as unused
    """Syncs application commands."""
    synced = await bot.tree.sync()
    logger.info("Synced %d command(s).", len(synced))  # Use lazy logging

async def load_cogs():
    """Loads all cogs from the cogs directory."""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    """Bot entrypoint."""
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
