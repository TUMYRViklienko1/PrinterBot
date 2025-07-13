# cogs/PrinterInfo.py

import discord
from discord.ext import commands
from discord import app_commands  
import logging

logger = logging.getLogger(__name__)
printer_utils_cog = None

class Menu(discord.ui.Select):
        def __init__(self, printer_utils_cog):
            
            
            options = []

            for printer_name in printer_utils_cog.connected_printers.keys():
                printer_option = discord.SelectOption(label = printer_name)
                options.append(printer_option)
            
            super().__init__(placeholder="Please select a printer:", min_values= 1, max_values= 1, options = options)

        async def callback(self, interaction: discord.Interaction):
            await PrinterInfo.status_show(name_of_printer = self.values[0]) 

class MenuView(discord.ui.View):
    def __init__(self, printer_utils_cog):
        super().__init__()
        self.add_item(Menu(printer_utils_cog))

class PrinterInfo(commands.Cog, group_name="pinter_info", group_description="Display info about your 3D Printer"):
    def __init__(self, bot):
        self.bot = bot     
    async def status_show(self, ctx: commands.Context, name_of_printer: str):
        await ctx.send(f"name_of_printer")

    @commands.hybrid_command(name="status", description="Display status of the printer")
    async def status(self, ctx: commands.Context):
        printer_utils_cog = self.bot.get_cog("PrinterUtils")
        await ctx.send("📋 Select a printer option:",
                        view=MenuView(printer_utils_cog = printer_utils_cog))
# discord‑py ≥ 2.0 expects an *async* setup function
async def setup(bot):
    await bot.add_cog(PrinterInfo(bot))

