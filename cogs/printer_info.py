# cogs/PrinterInfo.py

import discord
from discord.ext import commands
from discord import app_commands
import logging

import bambulabs_api as bl
from bambulabs_api import GcodeState

from typing import Optional
from functools import partial 
from typing import Callable, Awaitable

from .ui import MenuView
from .ui import build_printer_status_embed
from .ui import delete_image

from .utils import MenuCallBack
from .utils import get_printer_data
from .utils import printer_error_handler
from .utils import finish_time_format
from .utils import get_camera_frame
from .utils import get_cog
from .utils import ImageCredentials
from .utils import set_image_default_credentials_callback
from .utils import set_image_custom_credentials_callback

logger = logging.getLogger(__name__)

class PrinterInfo(commands.Cog, group_name="pinter_info", group_description="Display info about your 3D Printer"):
    def __init__(self, bot):
        self.bot = bot



    async def check_printer_list(self, ctx, printer_utils_cog) -> bool:
        if not printer_utils_cog.connected_printers:
            embed = discord.Embed(title="❌ No Printers in the list", description="To add the printer use /connect", color=0x7309de)
            await ctx.send(embed=embed)
            return False
        return True

    async def _get_printer_utils_cog(self, ctx:commands.Context):
        cog = await get_cog(ctx, self.bot, "PrinterUtils")
        if cog is None:
            await ctx.send("❌ Can't load cog with name: PrinterUtils")
        return cog


    async def embed_printer_info(
        self,
        ctx: commands.Context,
        printer_object: bl.Printer,
        printer_name: str,
        set_image_callback: Callable[[], Awaitable[ImageCredentials]]):     

        image_credentials = await set_image_callback()
        embed = await build_printer_status_embed(
            ctx=ctx,
            printer_object=printer_object,
            printer_name=printer_name,
            image_url=image_credentials.embed_set_image_url
        )

        await ctx.send(file=image_credentials.image_main_location, embed=embed)

        await delete_image(
            delete_image_callback=image_credentials.delete_image_flag,
            image_filename=image_credentials.image_filename
        )
        
    async def connection_check_callback(self, ctx:commands.Context, printer_name: str, printer_utils_cog) -> bl.Printer:

        printer_data = await get_printer_data(ctx = ctx, printer_name = printer_name, printer_utils_cog = printer_utils_cog)
        
        return await printer_utils_cog.connect_to_printer(ctx = ctx, printer_name = printer_name, printer_data = printer_data)

    async def status_show_callback(self, ctx: commands.Context, printer_name: str, printer_utils_cog):
        logger.debug(f"Status for printer: {printer_name}")

        printer_object = await self.connection_check_callback(ctx=ctx, printer_name=printer_name, printer_utils_cog=printer_utils_cog)
        
        if printer_object.get_state() == GcodeState.RUNNING:
            set_image_cb = partial(set_image_custom_credentials_callback, printer_name=printer_name, printer_object=printer_object)
        else:
            set_image_cb = set_image_default_credentials_callback

        await self.embed_printer_info(
            ctx=ctx,
            printer_object=printer_object,
            printer_name=printer_name,
            set_image_callback=set_image_cb
        )
                    
    @commands.hybrid_command(name="status", description="Display status of the printer")
    async def status(self, ctx: commands.Context):
        name_of_cog = "PrinterUtils"


        printer_utils_cog = await self._get_printer_utils_cog(ctx = ctx)
        
        if not await self.check_printer_list(ctx=ctx, printer_utils_cog=printer_utils_cog):
            logger.debug("No Printers in the list")
            return

        await ctx.send(
            "📋 Select the printer option:",
            view=MenuView(printer_utils_cog=printer_utils_cog, parent_cog=self, ctx=ctx , callback_status = MenuCallBack.CALLBACK_STATUS_SHOW)
        )

    @commands.hybrid_command(name="list", description="Display list of the printer")
    async def list_all_printers(self, ctx: commands.Context):
        name_of_cog = "PrinterUtils"
        printer_utils_cog = await self._get_printer_utils_cog(ctx = ctx)
        
        if not await self.check_printer_list(ctx=ctx, printer_utils_cog=printer_utils_cog):
            logger.debug("No Printers in the list")
            return

        description = "\n".join(f"• {name}" for name in printer_utils_cog.connected_printers)
        embed = discord.Embed(
            title="🖨️ Connected Printers",
            description=description,
            color= 0x7309de
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="check_connection", description="Check connection of the 3D printer")
    async def check_connection(self, ctx: commands.Context):
        name_of_cog = "PrinterUtils"
        printer_utils_cog = await self._get_printer_utils_cog(ctx = ctx)
        
        if not await self.check_printer_list(ctx = ctx, printer_utils_cog= printer_utils_cog):
            logger.debug("No Printers in the list")
            return
        
        await ctx.send(
            "📋 Select the printer option:",
            view=MenuView(printer_utils_cog=printer_utils_cog, parent_cog=self, ctx=ctx,  callback_status = MenuCallBack.CALLBACK_CONNECTION_CHECK)
        )

# discord​‐py ≥ 2.0 expects an *async* setup function
async def setup(bot):
    await bot.add_cog(PrinterInfo(bot))
