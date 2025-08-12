"""
Provides helper functions for establishing and validating connections to Bambu Lab printers.

This module encapsulates the logic for:
    - Validating printer network credentials (e.g., IP address format)
    - Creating and connecting printer instances via the Bambu Lab API
    - Establishing MQTT connections with retry/backoff
    - Checking printer operational status
    - Waiting for readiness after initial handshake

"""

import logging
import ipaddress
import asyncio

from typing import Optional
import bambulabs_api as bl
from bambulabs_api.states_info import GcodeState

from cogs.utils import (
    PrinterCredentials,
    backoff_checker,
    light_printer_check,
    PrinterDataDict
)

logger = logging.getLogger(__name__)

async def _validate_ip(ip: str) -> bool:
    """Validates the IP address format."""
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        logger.error("Invalid IP address: %s", ip)
        return False
    return True

def _create_printer(printer_data: PrinterCredentials) -> bl.Printer:
    """Creates and connects a printer instance."""
    printer = bl.Printer(printer_data.ip, printer_data.access_code, printer_data.serial)
    printer.connect()
    return printer

async def _connect_mqtt(printer: bl.Printer, printer_name: str) -> bool:
    """Establishes MQTT connection using backoff strategy."""
    action_name = f"MQTT connection to {printer_name}"
    result = await backoff_checker(
        action_func_callback=printer.mqtt_client.is_connected,
        action_name=action_name,
        interval=0.3,
        max_attempts=5,
        success_condition=lambda connected: connected is True
    )
    return result is True

async def _check_printer_status(printer: bl.Printer, printer_name: str) -> Optional[str]:
    """Checks if printer returns valid status."""
    return await backoff_checker(
        action_func_callback=printer.get_state,
        action_name=f"check_printer_status for {printer_name}",
        interval=0.3,
        max_attempts=10,
        success_condition=lambda state: state != GcodeState.UNKNOWN
    )

async def wait_for_printer_ready(printer: bl.Printer, timeout: float = 5.0) -> bool:
    """Waits for the printer to be ready after MQTT handshake."""
    end_time = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < end_time:
        if (printer.get_state() != GcodeState.UNKNOWN and
            printer.get_bed_temperature() is not None):
            return True
        await asyncio.sleep(0.5)
    logger.error("Printer Values Not Available Yet")
    return False
# pylint: disable=too-many-return-statements
async def connect_to_printer(
    printer_name: str,
    printer_data: PrinterCredentials
) -> Optional[bl.Printer]:
    """Connects to a printer and validates its state."""
    try:
        printer = _create_printer(printer_data=printer_data)
        if not await _connect_mqtt(printer=printer, printer_name=printer_name):
            logger.error("Could not connect to `%s` via MQTT.", printer_name)
            return None

        status = await _check_printer_status(
            printer=printer,
            printer_name=printer_name
        )

        if status is None:
            logger.warning("Connected to `%s`, but status is UNKNOWN.", printer_name)
            return None

        if not await wait_for_printer_ready(printer):
            logger.error("Printer values never became available")
            return None

        logger.info("Connected to `%s` with status `%s`.", printer_name, status)

        if not await light_printer_check(printer=printer):
            logger.error("Return None in the light_printer_check")
            return None

        return printer
    except (ConnectionError, TimeoutError) as e:
        logger.error("Connection issue while connecting to printer `%s`: %s", printer_name, e)
        return None
    except Exception: # pylint: disable=broad-exception-caught
        logger.exception("Unhandled exception during connect")
        return None

async def connection_check(
    printer_name: str,
    printer_utils_cog: 'PrinterUtils') -> Optional[bl.Printer]:
    """Check the connection to the existing printer"""
    try:
        printer_data_dict = printer_utils_cog.connected_printers[printer_name]
        printer_data_credentials = PrinterCredentials(**printer_data_dict)
        printer = await connect_to_printer(
            printer_name=printer_name,
            printer_data=printer_data_credentials
            )
        if printer is not None:
            return printer
        logger.warning("Can't reach the printer: '%s'", printer_name)
        return None
    except KeyError:
        return None

async def connect_new_printer(
    printer_name:str,
    printer_data:PrinterDataDict):
    """
    Attempts to establish a connection to a new printer using the provided credentials.

    This function wraps `connect_to_printer` and logs a warning if the connection fails.
    If the printer connects successfully, the printer instance is returned for further use.

    Args:
        printer_name (str): The human-readable name assigned to the printer.
        printer_data (PrinterDataDict): Dictionary containing printer connection parameters
            such as IP address, access code, and serial number.

    Returns:
        bl.Printer | None: The connected printer instance if successful, otherwise None.
    """
    printer = await connect_to_printer(
        printer_name=printer_name,
        printer_data=printer_data
    )

    if printer is not None:
        return printer
    logger.warning("Can't connect to the printer: '%s'", printer_name)
    return None
