from discord.ext import commands
import discord

import bambulabs_api as bl

import time
import datetime

from ..utils.printer_helpers import finish_time_format
from ..utils.printer_helpers import printer_error_handler


async def build_printer_status_embed(ctx: commands.Context,
                                     printer_object: bl.Printer,
                                     name_of_printer: str,
                                     image_url: str) -> discord.Embed:
    embed = discord.Embed(
                title=f"Name: {name_of_printer}",
                description="Status of the printer:",
                color=0x7309de
            )
        
    embed.set_author(
        name=ctx.author.display_name,
        url="",
        icon_url=ctx.author.avatar.url  # updated to use ctx.author for clarity
    )
    
    embed.set_thumbnail(url="https://i.pinimg.com/736x/42/40/ce/4240ce1dbd35a77bea5138b9e1a5a9f7.jpg")

    embed.add_field(
        name="Print Time",
        value=(
            f"`Current:` {printer_object.get_time()}\n"
            f"`Finish:`  {await finish_time_format(printer_object.get_time())}\n"
        ),
        inline=True
    )

    embed.add_field(
        name="Progress",
        value=(
            f"`Percent:` {printer_object.get_percentage()}%\n"
            f"`Layer:`   {printer_object.current_layer_num()}/{printer_object.total_layer_num()}\n"
            f"`Speed:`   {printer_object.get_print_speed()} (100%)\n"
        ),
        inline=True
    )

    embed.add_field(
        name="Lights",
        value=(
            f"`Chamber:` {printer_object.get_light_state()}\n"
        ),
        inline=True
    )

    embed.add_field(
        name="Temps",
        value=(
            f"`Bed:`     {printer_object.get_bed_temperature()}°C\n"
            f"`Nozzle:`  {printer_object.get_nozzle_temperature()}°C\n"
            f"`Chamber:` {printer_object.get_chamber_temperature()}°C\n"
        ),
        inline=True
    )

    embed.add_field(
        name="Fans",
        value=(
            f"`Main 1:`   {printer_object.mqtt_client.get_part_fan_speed()}%\n"
            f"`Main 2:`   {printer_object.mqtt_client.get_aux_fan_speed()}%\n"
            f"`Cooling:`  {printer_object.mqtt_client.get_chamber_fan_speed()}%\n"
        ),
        inline=True
    )

    embed.add_field(
        name="Errors",
        value=f"`Error:` {await printer_error_handler(printer_object=printer_object)}",
        inline=False
    )

    embed.add_field(
        name="\u200b",  # Blank field name for layout
        value=f"{await printer_error_handler(printer_object=printer_object)}",
        inline=False
    )

    embed.set_image(url=image_url)

    return embed
