# cogs/PrinterInfo.py

import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class Menu(discord.ui.Select):
    def __init__(self, printer_utils_cog, parent_cog, ctx):
        self.parent_cog = parent_cog
        self.ctx = ctx

        options = [
            discord.SelectOption(label=printer_name)
            for printer_name in printer_utils_cog.connected_printers.keys()
        ]

        if not options:
            options = [discord.SelectOption(label="No printers connected", value="none", default=True)]

        super().__init__(
            placeholder="Please select a printer:",
            min_values=1,
            max_values=1,
            options=options,
            disabled=(options[0].value == "none")
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("No printers are currently connected.", ephemeral=True)
        else:
            await self.parent_cog.status_show(self.ctx, self.values[0])


class MenuView(discord.ui.View):
    def __init__(self, printer_utils_cog, parent_cog, ctx):
        super().__init__()
        self.add_item(Menu(printer_utils_cog, parent_cog, ctx))


class PrinterInfo(commands.Cog, group_name="pinter_info", group_description="Display info about your 3D Printer"):
    def __init__(self, bot):
        self.bot = bot

    async def status_show(self, ctx: commands.Context, name_of_printer: str):
        await ctx.send(f"Status for printer: {name_of_printer}")

    @commands.hybrid_command(name="status", description="Display status of the printer")
    async def status(self, ctx: commands.Context):
        printer_utils_cog = self.bot.get_cog("PrinterUtils")
        if not printer_utils_cog:
            await ctx.send("❌ Printer utilities not loaded.")
            return

        await ctx.send(
            "📋 Select a printer option:",
            view=MenuView(printer_utils_cog=printer_utils_cog, parent_cog=self, ctx=ctx)
        )


# discord​‐py ≥ 2.0 expects an *async* setup function
async def setup(bot):
    await bot.add_cog(PrinterInfo(bot))
