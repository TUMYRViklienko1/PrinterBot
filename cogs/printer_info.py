# cogs/printer_UI.py

import discord
from discord.ext import commands
from discord import app_commands  
import logging

logger = logging.getLogger(__name__)

class PinterInfo(commands.Cog, group_name="pinter_info", group_description="Display info about your 3D Printer"):
    def __init__(self, bot):
        self.bot = bot        

    

# discord‑py ≥ 2.0 expects an *async* setup function
async def setup(bot):
    await bot.add_cog(PinterInfo(bot))

