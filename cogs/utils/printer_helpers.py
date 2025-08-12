
"""Utility functions for managing printer operations, camera, and backoff retries."""
# pylint: disable=too-many-arguments, too-many-positional-arguments

import datetime
import logging
import asyncio
import math
from typing import Optional, Any, Callable, TYPE_CHECKING

import bambulabs_api as bl

from .models import PrinterCredentials, ImageCredentials, PrinterDataDict

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from cogs.printer_utils import PrinterUtils

def get_printer_data_dict(printer_data: PrinterDataDict) -> PrinterCredentials:
    """Converts dictionary data to a PrinterCredentials object."""
    return PrinterCredentials(
        ip=printer_data["ip"],
        access_code=printer_data["access_code"],
        serial=printer_data["serial"]
    )


async def get_printer_data(printer_name: str, printer_utils_cog) -> Optional[PrinterCredentials]:
    """Fetches printer credentials for a given printer name."""
    printer_data = printer_utils_cog.connected_printers.get(printer_name)
    if printer_data is None:
        logger.error("Printer '%s' not found.", printer_name)
        return None
    return get_printer_data_dict(printer_data)


async def get_camera_frame(printer_object: bl.Printer, printer_name: str) -> bool:
    """Attempts to get a camera frame and save it to file."""
    try:
        printer_image = printer_object.get_camera_image()
    except Exception: # pylint: disable=broad-exception-caught
        logger.warning("Printer: %s. Can't take a frame", printer_name)
        return False

    printer_image.save(f"img/camera_frame_{printer_name}.png")
    return True


async def get_cog(bot, name_of_cog: str) -> Optional[Any]:
    """Retrieves a bot cog by name."""
    printer_cog = bot.get_cog(name_of_cog)
    if not printer_cog:
        logger.error("Can't load cog with name: %s", name_of_cog)
        return None
    return printer_cog


async def printer_error_handler(printer_object: bl.Printer) -> str:
    """Returns a human-readable error message from the printer."""
    error_code = printer_object.print_error_code()
    if error_code == 0:
        return "No errors."
    return f"Printer Error Code: {error_code}"


async def set_image_default_credentials_callback() -> ImageCredentials:
    """Returns default image credentials."""
    return ImageCredentials()


async def set_image_custom_credentials_callback(
    printer_name: str, printer_object: bl.Printer
) -> ImageCredentials:
    """Generates custom image credentials after capturing a frame."""
    image_filename = "camera_frame_.png"
    delete_image_flag = False

    if await get_camera_frame(printer_object, printer_name):
        image_filename = f"camera_frame_{printer_name}.png"
        delete_image_flag = True

    return ImageCredentials(
        image_filename=image_filename,
        delete_image_flag=delete_image_flag
    )


async def finish_time_format(remaining_time) -> str:
    """Formats a finish timestamp from remaining minutes."""
    if remaining_time is not None:
        finish_time = datetime.datetime.now() + datetime.timedelta(minutes=int(remaining_time))
        return finish_time.strftime("%Y-%m-%d %H:%M:%S")
    return "NA"


async def light_printer_check(printer: bl.Printer) -> bool:
    """Checks that light on the printer can turn on and off."""
    def check_light(action_func, action_name):
        if action_func():
            logger.debug("Light %s successfully.", action_name)
            return True
        logger.error("Light NOT %s successfully.", action_name)
        return False

    if not check_light(printer.turn_light_on, "turned on"):
        return False

    await asyncio.sleep(1)

    if not check_light(printer.turn_light_off, "turned off"):
        return False

    return True


async def backoff_checker(
    action_func_callback: Callable[[], Any],
    action_name: str,
    interval: float = 0.3,
    max_attempts: int = 5,
    exponential: int = 2,
    success_condition: Callable[[Any], bool] = bool
) -> Optional[Any]:   # pylint: disable=too-many-arguments
    """Performs an action with exponential backoff if it fails."""
    for attempt in range(1, max_attempts + 1):
        result = action_func_callback()

        if success_condition(result):
            logger.info("Successfully done %s", action_name)
            return result

        sleep_time = interval * math.pow(exponential, attempt - 1)
        logger.info(
            "Retrying to %s. Retry %d/%d. Sleeping %.1fs",
            action_name, attempt, max_attempts, sleep_time
        )
        await asyncio.sleep(sleep_time)

    logger.error("Could not perform %s after %d attempts.", action_name, max_attempts)
    return None

def delete_printer(
    printer_name: str,
    printer_utils_cog) -> bool:
    """Delete the printer from the list of all printers"""
    logger.debug("Deleting printer: %s", printer_name)
    try:
        printer_utils_cog.connected_printers.pop(printer_name)
        printer_utils_cog.storage.delete(printer_name)
        return True
    except KeyError:
        logger.warning("printer is not in the list")
        return False

async def connection_check(
    printer_name: str,
    printer_utils_cog: 'PrinterUtils') -> Optional[bl.Printer]:
    """Check the connection to the existing printer"""
    try:
        printer_data = printer_utils_cog.connected_printers[printer_name]
        printer = await printer_utils_cog.connect_to_printer(
            printer_name=printer_name,
            printer_data=printer_data
            )
        if printer is not None:
            return printer
        logger.warning("Can't connect to a printer: '%s'", printer_name)
        return None
    except KeyError:
        return None

# async def connect_new_printer(
#     printer_name:str,
#     printer_data:PrinterDataDict):
#     printer = await self.printer_utils_cog.connect_to_printer(
#         printer_name=self.printer_name_original,
#         printer_data=new_printer_credentials
#     )

#     if printer is not None:
#         return printer
#     logger.warning("Can't connect to a printer: '%s'", printer_name)
#     return None

