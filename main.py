
import asyncio
import discord
from discord.ext import commands
from config.config import DISCORD_TOKEN, logger 

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.do_not_disturb,
        activity=discord.Activity(type=discord.ActivityType.listening, name='tessst')
    )
    logger.info("Bot is ready!")

@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    logger.info(f"Synced {len(synced)} command(s).")

async def load_cogs():
    import os
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
