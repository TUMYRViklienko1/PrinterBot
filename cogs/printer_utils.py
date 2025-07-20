# cogs/printer.py

import asyncio
import json
import logging
import os
import ipaddress
from pathlib import Path
from dataclasses import asdict
from typing import Dict, Optional

import bambulabs_api as bl
from bambulabs_api import GcodeState
from discord.ext import commands, tasks

from .ui import embed_printer_info

from .utils import PrinterCredentials
from .utils import PrinterStorage
from .utils import light_printer_check
from .utils import get_cog
from .utils import set_image_custom_credentials_callback
from .utils import get_printer_data_dict
from .utils import backoff_checker
from .utils import PrinterDataDict

logger = logging.getLogger(__name__)
CHANEL_ID = os.getenv("CHANEL_ID")


class PrinterUtils(commands.GroupCog, group_name="printer_utils", group_description="Control 3D printers"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.storage = PrinterStorage()
        self.connected_printers:    Dict[str, PrinterDataDict] = self.storage.load()
        self.previous_state_dict:   Dict[str, Optional[str]] = dict.fromkeys(self.connected_printers.keys(), "")
        self.connected_printer_objects: Dict[str, Optional[bl.Printer]] = dict.fromkeys(self.connected_printers.keys(), None)
        self.status_channel_id: int = int(CHANEL_ID)
        self.status_channel = self.bot.get_channel(self.status_channel_id)
        self.monitor_printers.start()
    async def _validate_ip(self, ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            logging.error(f"Invalid IP address: `{ip}`.")
            return False
        return True
            
    def _create_printer(self, printer_data: PrinterCredentials) -> bl.Printer:
        printer = bl.Printer(printer_data.ip, printer_data.access_code, printer_data.serial)
        printer.connect()
        return printer
    
    async def _connect_mqtt(self, printer: bl.Printer, printer_name: str) -> bool:
        action_name = f"MQTT connection to {printer_name}"
        result = await backoff_checker(
            action_func_callback=lambda: printer.mqtt_client.is_connected(),
            action_name=action_name,
            interval=0.3,
            max_attempts=5,
            success_condition=lambda connected: connected is True
        )
        return result is True


    async def _check_printer_status(self, printer: bl.Printer, printer_name: str) -> Optional[str]:
        return await backoff_checker(
            action_func_callback=lambda: printer.get_state(),
            action_name=f"check_printer_status for {printer_name}",
            interval=0.3,
            max_attempts=10,
            success_condition=lambda state: state != GcodeState.UNKNOWN
        )

    async def wait_for_printer_ready(self, printer: bl.Printer, timeout: float = 5.0) -> bool:
        """Waits for the printer to have usable values after MQTT handshake."""
        end_time = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < end_time:
            try:
                if printer.get_state() != GcodeState.UNKNOWN and printer.get_bed_temperature() is not None:
                    return True
            except Exception:
                pass
            await asyncio.sleep(0.5)
        logger.error("Printer Values Not Available Yet")
        return False

    async def connect_to_printer(
    self,
    printer_name: str,
    printer_data: PrinterCredentials
    ) -> Optional[bl.Printer]:
        try:

            printer = self._create_printer(printer_data = printer_data)

            if await self._connect_mqtt(printer=printer, printer_name=printer_name) is False:
                logger.error(f"Could not connect to `{printer_name}` via MQTT.")
                return None

            status = await self._check_printer_status(printer=printer, printer_name=printer_name) 

            if status is None:
                logger.warning(f"Connected to `{printer_name}`, but status is UNKNOWN.")
                return None
            
            if not await self.wait_for_printer_ready(printer):
                logger.error("Printer values never became available")
                return None
            
            logger.info(f"Connected to `{printer_name}` with status `{status}`.")

            if not await light_printer_check(printer = printer):
                logger.error("return none in the light_printer_check")
                return None

            return printer
        
        except Exception as e:
            logger.exception("Unhandled exception during connect")
            return None
            
        

    @commands.hybrid_command(name="connect", description="Connect to a 3D Printer")
    async def connect(self, ctx: commands.Context, name: str, ip: str,serial: str, access_code: str):
        await ctx.defer(ephemeral=True)

        # Continue as usual...
        if not await self._validate_ip(ip):
            logger.error(f" Invalid IP address: `{ip}`.")
            return

        logger.info(f"Attempting connection to printer: {name}")

        printer_data = PrinterCredentials(ip=ip, access_code= access_code, serial= serial)

        printer = await self.connect_to_printer(printer_name=name, printer_data= printer_data)

        if printer is not None:
            try:

                self.connected_printers[name] = asdict(printer_data)
                self.storage.save(self.connected_printers)

            finally:
                await asyncio.to_thread(printer.disconnect)

    @tasks.loop(seconds=15)
    async def monitor_printers(self):
        if not self.connected_printers:
            logger.debug("No printers in the list")
            return

        try:
            status_channel = await self.bot.fetch_channel(self.status_channel_id)
            logging.info("Successfully fetched channel")
        except Exception as e:
            logger.error(f"Failed to fetch status channel: {e}")
            return

        for printer_name, printer_data in self.connected_printers.items():
            printer = self.connected_printer_objects.get(printer_name)

            if printer is None or not printer.mqtt_client.is_connected():
                logger.warning(f"Printer {printer_name} is disconnected. Reconnecting...")
                printer_object = await self.connect_to_printer(
                printer_name=printer_name,
                printer_data=get_printer_data_dict(printer_data=printer_data)
                )
                if printer_object is None:
                    logger.error(f"Failed to reconnect printer `{printer_name}`.")
                    continue
                self.connected_printer_objects[printer_name] = printer_object
                logger.info(f"Reconnected to printer `{printer_name}`.") 
            
            printer = self.connected_printer_objects[printer_name]

            try:
                printer_current_state = printer.get_state()
                previous_state = self.previous_state_dict.get(printer_name)
                logger.info(f"Current state: {printer_name} is {printer_current_state}")
                logging.info(f"previous state: {previous_state}")
                
                if printer_current_state in (GcodeState.RUNNING, GcodeState.FINISH, GcodeState.FAILED):
                    if previous_state != printer_current_state:
                        await embed_printer_info(
                            printer_object=printer,
                            printer_name=printer_name,
                            set_image_callback=lambda: set_image_custom_credentials_callback(
                                printer_name=printer_name,
                                printer_object=printer
                            ),
                            status_channel=status_channel
                        )
                        self.previous_state_dict[printer_name] = printer_current_state
            except Exception as e:
                logger.exception(f"Failed to read state for `{printer_name}`. Removing from active list.")
                await asyncio.to_thread(printer.disconnect)
                del self.connected_printer_objects[printer_name]
            

async def setup(bot):
    await bot.add_cog(PrinterUtils(bot))

