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

    async def get_cog(self, ctx: commands.Context, name_of_cog: str):
        printer_utils_cog = self.bot.get_cog(name_of_cog)
        if not printer_utils_cog:
            await ctx.send("❌ Printer utilities not loaded.")
            return
        return printer_utils_cog

    async def status_show(self, ctx: commands.Context, name_of_printer: str):
        await ctx.send(f"Status for printer: {name_of_printer}")

    @commands.hybrid_command(name="status", description="Display status of the printer")
    async def status(self, ctx: commands.Context):
        name_of_cog = "PrinterUtils"
        printer_utils_cog = await self.get_cog(ctx = ctx, name_of_cog = name_of_cog)

        await ctx.send(
            "📋 Select a printer option:",
            view=MenuView(printer_utils_cog=printer_utils_cog, parent_cog=self, ctx=ctx)
        )

    @commands.hybrid_command(name="list", description="Display list of the printer")
    async def list_all_printers(self, ctx: commands.Context):
        name_of_cog = "PrinterUtils"
        printer_utils_cog = await self.get_cog(ctx = ctx, name_of_cog = name_of_cog)

        if not printer_utils_cog.connected_printers:
            await ctx.send("No Printers in the list")
            return 
        
        description = "\n".join(f"• {name}" for name in printer_utils_cog.connected_printers)
        embed = discord.Embed(
            title="🖨️ Connected Printers",
            description=description,
            color=discord.Color.blue()
        )

        await ctx.send(embed=embed)

# discord​‐py ≥ 2.0 expects an *async* setup function
async def setup(bot):
    await bot.add_cog(PrinterInfo(bot))
