from discord.ext import commands
import discord

import bambulabs_api as bl

import os
import logging
from typing import Callable, Awaitable
from typing import Optional

from ..utils.printer_helpers import finish_time_format
from ..utils.printer_helpers import printer_error_handler

from ..utils.models import ImageCredentials

logger = logging.getLogger(__name__)

async def embed_printer_info(
    printer_object: bl.Printer,
    printer_name: str,
    set_image_callback: Callable[[], Awaitable[ImageCredentials]],
    ctx: Optional[commands.Context] = None,
    status_channel: Optional[discord.abc.GuildChannel] = None):     

    image_credentials = await set_image_callback()
    embed = await build_printer_status_embed(
        printer_object=printer_object,
        printer_name=printer_name,
        image_url=image_credentials.embed_set_image_url,
        ctx=ctx
    )
    if status_channel is not None:
        await status_channel.send(file=image_credentials.image_main_location, embed=embed)
    else:
        await ctx.send(file=image_credentials.image_main_location, embed=embed)

    await delete_image(
        delete_image_callback=image_credentials.delete_image_flag,
        image_filename=image_credentials.image_filename
    )

async def build_printer_status_embed(
    printer_object: bl.Printer,
    printer_name: str,
    image_url: str,
    ctx: Optional[commands.Context] = None
    ) -> discord.Embed:

    embed = discord.Embed(
        title=f"Name: {printer_name}",
        description="Status of the printer:",
        color=0x7309de
    )

    # Add author info only if ctx is provided (e.g., during a command)
    if ctx and ctx.author:
        try:
            embed.set_author(
                name=ctx.author.display_name,
                icon_url=ctx.author.avatar.url
            )
        except Exception:
            pass  # Fail silently if avatar or other info is missing

    embed.set_thumbnail(url="https://i.pinimg.com/736x/42/40/ce/4240ce1dbd35a77bea5138b9e1a5a9f7.jpg")

    embed.add_field(
        name="Print Time",
        value=(
            f"`Current:` {printer_object.get_time()}\n"
            f"`Finish:`  {await finish_time_format(printer_object.get_time())}"
        ),
        inline=True
    )

    embed.add_field(
        name="Progress",
        value=(
            f"`Percent:` {printer_object.get_percentage()}%\n"
            f"`Layer:`   {printer_object.current_layer_num()}/{printer_object.total_layer_num()}\n"
            f"`Speed:`   {printer_object.get_print_speed()} (100%)"
        ),
        inline=True
    )

    embed.add_field(
        name="Lights",
        value=f"`Chamber:` {printer_object.get_light_state()}",
        inline=True
    )

    embed.add_field(
        name="Temps",
        value=(
            f"`Bed:`     {printer_object.get_bed_temperature()}°C\n"
            f"`Nozzle:`  {printer_object.get_nozzle_temperature()}°C\n"
            f"`Chamber:` {printer_object.get_chamber_temperature()}°C"
        ),
        inline=True
    )

    embed.add_field(
        name="Fans",
        value=(
            f"`Main 1:`   {printer_object.mqtt_client.get_part_fan_speed()}%\n"
            f"`Main 2:`   {printer_object.mqtt_client.get_aux_fan_speed()}%\n"
            f"`Cooling:`  {printer_object.mqtt_client.get_chamber_fan_speed()}%"
        ),
        inline=True
    )

    error_msg = await printer_error_handler(printer_object=printer_object)
    embed.add_field(
        name="Errors",
        value=f"`Error:` {error_msg}",
        inline=False
    )

    embed.add_field(
        name="\u200b",  # Spacer
        value=error_msg,
        inline=False
    )

    embed.set_image(url=image_url)

    return embed

async def delete_image(delete_image_callback: bool, image_filename: str) -> bool:
    if delete_image_callback:
        try: 
            os.remove(f"img/{image_filename}")
            logger.debug(f"File '{image_filename}' deleted successfully.")
            return True
        
        except FileNotFoundError: 
            logger.exception(f"File '{image_filename}' not found.")
            return False