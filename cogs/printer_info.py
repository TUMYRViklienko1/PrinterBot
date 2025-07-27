"""Cog for displaying printer information in a Discord bot."""

from functools import partial
from typing import Optional

import logging
import discord
from discord.ext import commands

import bambulabs_api as bl
from bambulabs_api import GcodeState

from .ui import (
    MenuView,
    embed_printer_info,
)

from .utils import (
    MenuCallBack,
    get_printer_data,
    get_cog,
    set_image_default_credentials_callback,
    set_image_custom_credentials_callback
)

logger = logging.getLogger(__name__)

class PrinterInfo(commands.Cog):
    """Cog that provides commands to display 3D printer info."""

    def __init__(self, bot):
        self.bot = bot

    async def check_printer_list(self, ctx, printer_utils_cog) -> bool:
        """Check if there are connected printers."""
        if not printer_utils_cog.connected_printers:
            embed = discord.Embed(
                title="❌ No Printers in the list",
                description="To add the printer use /connect",
                color=0x7309de
            )
            await ctx.send(embed=embed)
            return False
        return True

    async def _get_printer_utils_cog(self, ctx: commands.Context):
        """Get the PrinterUtils cog."""
        cog = await get_cog(self.bot, "PrinterUtils")
        if cog is None:
            await ctx.send("❌ Can't load cog with name: PrinterUtils")
        return cog

    async def connection_check_callback(self,
                                        ctx: commands.Context,
                                        printer_name: str,
                                        printer_utils_cog) -> Optional[bl.Printer]:
        """Ensure a valid connection to the printer."""

        printer_data = await get_printer_data(printer_name=printer_name,
                                              printer_utils_cog=printer_utils_cog)
        printer = await printer_utils_cog.connect_to_printer(printer_name=printer_name,
                                                          printer_data=printer_data)
        if printer is not None:
            await ctx.send(f"Successfully connected to the printer: '{printer_name}'")
            return printer
        await ctx.send(f"❌ Can't connect to a printer: '{printer_name}'")
        return None

    async def status_show_callback(self,ctx: commands.Context,printer_name: str,printer_utils_cog):
        """Display printer status information."""
        logger.debug("Status for printer: %s", printer_name)

        printer_object = await self.connection_check_callback(
            ctx=ctx,
            printer_name=printer_name,
            printer_utils_cog=printer_utils_cog
        )
        if printer_object is None:
            return

        if printer_object.get_state() == GcodeState.RUNNING:
            set_image_cb = partial(
                set_image_custom_credentials_callback,
                printer_name=printer_name,
                printer_object=printer_object
            )
        else:
            set_image_cb = set_image_default_credentials_callback

        await embed_printer_info(
            ctx=ctx,
            printer_object=printer_object,
            printer_name=printer_name,
            set_image_callback=set_image_cb
        )

    @commands.hybrid_command(name="status", description="Display status of the printer")
    async def status(self, ctx: commands.Context):
        """Hybrid command to display the printer status."""
        printer_utils_cog = await self._get_printer_utils_cog(ctx=ctx)

        if not await self.check_printer_list(ctx=ctx, printer_utils_cog=printer_utils_cog):
            logger.debug("No Printers in the list")
            return

        await ctx.send(
            "📋 Select the printer option:",
            view=MenuView(
                printer_utils_cog=printer_utils_cog,
                parent_cog=self,
                ctx=ctx,
                callback_status=MenuCallBack.CALLBACK_STATUS_SHOW
            )
        )

    @commands.hybrid_command(name="list", description="Display list of the printer")
    async def list_all_printers(self, ctx: commands.Context):
        """Hybrid command to list all connected printers."""
        printer_utils_cog = await self._get_printer_utils_cog(ctx=ctx)

        if not await self.check_printer_list(ctx=ctx, printer_utils_cog=printer_utils_cog):
            logger.debug("No Printers in the list")
            return

        description = "\n".join(f"\u2022 {name}" for name in printer_utils_cog.connected_printers)
        embed = discord.Embed(
            title="📨 Connected Printers",
            description=description,
            color=0x7309de
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="check_connection",
                             description="Check connection of the 3D printer")
    async def check_connection(self, ctx: commands.Context):
        """Hybrid command to check printer connection."""
        printer_utils_cog = await self._get_printer_utils_cog(ctx=ctx)

        if not await self.check_printer_list(ctx=ctx, printer_utils_cog=printer_utils_cog):
            logger.debug("No Printers in the list")
            return

        await ctx.send(
            "📋 Select the printer option:",
            view=MenuView(
                printer_utils_cog=printer_utils_cog,
                parent_cog=self,
                ctx=ctx,
                callback_status=MenuCallBack.CALLBACK_CONNECTION_CHECK
            )
        )

async def setup(bot):
    """Setup function to add this cog to the bot."""
    await bot.add_cog(PrinterInfo(bot))
