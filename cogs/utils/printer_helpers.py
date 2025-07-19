from discord.ext import commands
import time
import datetime
import bambulabs_api as bl
import logging
from typing import Optional
import asyncio

from .models import PrinterCredentials
from .models import ImageCredentials

logger = logging.getLogger(__name__)

async def get_printer_data(
    ctx: commands.Context, 
    printer_name: str, 
    printer_utils_cog
) -> Optional[PrinterCredentials]:
    
    printer_info = printer_utils_cog.connected_printers.get(printer_name)

    if printer_info is None:
        logger.error(f"Printer '{printer_name}' not found.")
        return

    return PrinterCredentials(
        ip=printer_info["ip"],
        access_code=printer_info["access_code"],
        serial=printer_info["serial"]
    )

async def get_camera_frame(printer_object:bl.Printer, pinter_name: str):
    printer_image = printer_object.get_camera_image()
    printer_image.save(f"img/camera_frame_{pinter_name}.png")

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

async def set_image_default_credentials_callback()->ImageCredentials:
    return ImageCredentials()

async def set_image_custom_credentials_callback(printer_name, printer_object) -> ImageCredentials:
    await get_camera_frame(printer_object=printer_object, printer_name=printer_name)
    return ImageCredentials(image_filename=f"camera_frame_{printer_name}.png", delete_image_flag=True)

async def finish_time_format(remaining_time)->str:
    if remaining_time is not None:
        finish_time = datetime.datetime.now() + datetime.timedelta(
            minutes=int(remaining_time))
        return finish_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return "NA"
    
async def light_printer_check(ctx: commands.Context, printer:bl.Printer) -> bool:
    def check_light(action_func, action_name):
        if action_func():
            logger.debug(f"Light {action_name} successfully.")
            return True
        else:
            logger.error(f"Light NOT {action_name} successfully.")
            return False
    
    if not check_light(printer.turn_light_on, "turned on"):
        logger.error("Light turned on NOT successfully.")
        return False
    
    await asyncio.sleep(1)

    if not check_light(printer.turn_light_off, "turned off"):
        logger.error("Light turned OFF NOT successfully.")
        return False
    
    return True