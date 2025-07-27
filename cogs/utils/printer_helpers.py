from discord.ext import commands
import time
import datetime
import bambulabs_api as bl
import logging
from typing import Optional, Dict
import asyncio
import math

from .models import PrinterCredentials
from .models import ImageCredentials

logger = logging.getLogger(__name__)

def get_printer_data_dict(printer_data:Dict[str,str]) -> PrinterCredentials:
    return PrinterCredentials(
    ip=printer_data["ip"],
    access_code=printer_data["access_code"],
    serial=printer_data["serial"]
    )   
 

async def get_printer_data(
    ctx: commands.Context, 
    printer_name: str, 
    printer_utils_cog
) -> Optional[PrinterCredentials]:
    
    printer_data = printer_utils_cog.connected_printers.get(printer_name)

    if printer_data is None:
        logger.error(f"Printer '{printer_name}' not found.")
        return

    return get_printer_data_dict(printer_data=printer_data)

async def get_camera_frame(printer_object:bl.Printer, printer_name: str) -> bool:
    try:
        printer_image = printer_object.get_camera_image()
    except Exception as e:
        logging.warning(f"Printer: {printer_name}. Can't take a frame")
        return False
    printer_image.save(f"img/camera_frame_{printer_name}.png")
    return True

async def get_cog(ctx: commands.Context, bot, name_of_cog: str)  -> Optional[bl.Printer]:
    printer_cog = bot.get_cog(name_of_cog)
    if not printer_cog:
        logger.error(f"Can't load cog with name: {name_of_cog}")
        return None
    return printer_cog

async def printer_error_handler(printer_object:bl.Printer)->str:
    printer_error_code = printer_object.print_error_code()
    if printer_error_code == 0:
        return "No errors."
    else:
        return f"Printer Error Code: {printer_error_code}"

async def set_image_default_credentials_callback()->ImageCredentials:
    return ImageCredentials()

async def set_image_custom_credentials_callback(printer_name:str, printer_object:bl.Printer) -> ImageCredentials:
    image_filename = "camera_frame_.png"
    delete_image_flag = False
    if await get_camera_frame(printer_object=printer_object, printer_name=printer_name):
        image_filename = f"camera_frame_{printer_name}.png"
        delete_image_flag = True
    return ImageCredentials(image_filename=image_filename, delete_image_flag=delete_image_flag)

async def finish_time_format(remaining_time)->str:
    if remaining_time is not None:
        finish_time = datetime.datetime.now() + datetime.timedelta(
            minutes=int(remaining_time))
        return finish_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return "NA"
    
async def light_printer_check(printer:bl.Printer) -> bool:
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

async def backoff_checker(
    action_func_callback,
    action_name: str,
    interval: float = 0.3,
    max_attempts: int = 5,
    exponential: int = 2,
    success_condition=lambda result: bool(result)
) -> Optional[any]:
    for attempt in range(1, max_attempts + 1):
        result = action_func_callback()

        if success_condition(result):
            logger.info(f"Successfully done {action_name}")
            return result

        sleep_time = interval * math.pow(exponential, attempt - 1)
        logger.info(f"Retrying to {action_name}. Retry {attempt}/{max_attempts}. Sleeping {sleep_time:.1f}s")
        await asyncio.sleep(sleep_time)

    logger.error(f"Could not perform {action_name} after {max_attempts} attempts.")
    return None
