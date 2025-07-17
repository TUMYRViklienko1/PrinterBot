from discord.ext import commands
import time
import datetime
import bambulabs_api as bl
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def get_printer_data(
    ctx: commands.Context, 
    name_of_printer: str, 
    printer_utils_cog
) -> Optional[tuple[str, str, str]]:
    printer_info = printer_utils_cog.connected_printers.get(name_of_printer)

    if printer_info is None:
        # Handle the case where the printer doesn't exist
        print(f"❌ Printer '{name_of_printer}' not found.")
        return

    ip_printer = printer_info["ip"]
    serial_printer = printer_info["serial"]
    access_code_printer = printer_info["access_code"]

    return ip_printer, serial_printer, access_code_printer

async def get_camera_frame(printer_object:bl.Printer, name_of_printer: str):
    printer_image = printer_object.get_camera_image()
    printer_image.save(f"img/camera_frame_{name_of_printer}.png")

async def get_cog(ctx: commands.Context, bot, name_of_cog: str)  -> Optional[bl.Printer]:
    printer_cog = bot.get_cog(name_of_cog)
    if not printer_cog:
        logger.error(f"Can't load cog with name: {name_of_cog}")
        return None
    return printer_cog

async def printer_error_handler(printer_object)->str:
    printer_error_code = printer_object.print_error_code()
    if printer_error_code == 0:
        return "No errors."
    else:
        return f"Printer Error Code: {printer_error_code}"
    
async def finish_time_format(remaining_time)->str:
    if remaining_time is not None:
        finish_time = datetime.datetime.now() + datetime.timedelta(
            minutes=int(remaining_time))
        return finish_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return "NA"
    
