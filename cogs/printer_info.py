# cogs/PrinterInfo.py

import discord
from discord.ext import commands
from discord import app_commands  
import logging

logger = logging.getLogger(__name__)

class Menu(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(
                    label="Option 1",
                    description= "This is option 1"
                ),
                discord.SelectOption(
                    label="Option 2",
                    description= "This is option 2"
                ),
                discord.SelectOption(
                    label="Option 3",
                    description= "This is option 3"
                ),
            ]

            super().__init__(placeholder="Please choose an option:", min_values= 1, max_values= 1, options = options)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message(f"You picked {self.values[0]}")

class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Menu())

class PrinterInfo(commands.Cog, group_name="pinter_info", group_description="Display info about your 3D Printer"):
    def __init__(self, bot):
        self.bot = bot        

    @commands.hybrid_command(name="status", description="Display status of the printer")
    async def status(self, ctx: commands.Context):
        await ctx.send("📋 Select a printer option:", view=MenuView())
# discord‑py ≥ 2.0 expects an *async* setup function
async def setup(bot):
    await bot.add_cog(PrinterInfo(bot))

