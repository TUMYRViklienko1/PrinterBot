"""Utilities for managing 3D printer connections, MQTT, and monitoring."""

import asyncio
import logging
import ipaddress
import os
from dataclasses import asdict
from typing import Dict, Optional

import discord
from discord.ext import commands, tasks
import bambulabs_api as bl
from bambulabs_api import GcodeState

from .ui import embed_printer_info
from .utils import (
    PrinterCredentials,
    PrinterStorage,
    light_printer_check,
    set_image_custom_credentials_callback,
    get_printer_data_dict,
    backoff_checker,
    PrinterDataDict,
)
logger = logging.getLogger(__name__)
CHANEL_ID = os.getenv("CHANEL_ID")


class PrinterUtils(commands.GroupCog,
                   group_name="printer_utils",
                   group_description="Control 3D printers"):
    """GroupCog for managing printer-related commands and background monitoring."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.storage = PrinterStorage()
        self.connected_printers: Dict[str, PrinterDataDict] = self.storage.load()
        self.previous_state_dict: Dict[str, Optional[str]] = dict.fromkeys(
            self.connected_printers.keys(), ""
        )
        self.connected_printer_objects: Dict[str, Optional[bl.Printer]] = dict.fromkeys(
            self.connected_printers.keys(), None
        )
        self.status_channel_id: int = int(CHANEL_ID)
        self.status_channel: Optional[discord.abc.GuildChannel] = None
        self.monitor_printers.start()

    async def _validate_ip(self, ip: str) -> bool:
        """Validates the IP address format."""
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            logger.error("Invalid IP address: %s", ip)
            return False
        return True

    def _create_printer(self, printer_data: PrinterCredentials) -> bl.Printer:
        """Creates and connects a printer instance."""
        printer = bl.Printer(printer_data.ip, printer_data.access_code, printer_data.serial)
        printer.connect()
        return printer

    async def _connect_mqtt(self, printer: bl.Printer, printer_name: str) -> bool:
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

    async def _check_printer_status(self, printer: bl.Printer, printer_name: str) -> Optional[str]:
        """Checks if printer returns valid status."""
        return await backoff_checker(
            action_func_callback=printer.get_state,
            action_name=f"check_printer_status for {printer_name}",
            interval=0.3,
            max_attempts=10,
            success_condition=lambda state: state != GcodeState.UNKNOWN
        )

    async def wait_for_printer_ready(self, printer: bl.Printer, timeout: float = 5.0) -> bool:
        """Waits for the printer to be ready after MQTT handshake."""
        end_time = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < end_time:
            if (printer.get_state() != GcodeState.UNKNOWN and
                printer.get_bed_temperature() is not None):
                return True
            await asyncio.sleep(0.5)
        logger.error("Printer Values Not Available Yet")
        return False

    async def connect_to_printer(
        self,
        printer_name: str,
        printer_data: PrinterCredentials
    ) -> Optional[bl.Printer]:
        """Connects to a printer and validates its state."""
        try:
            printer = self._create_printer(printer_data=printer_data)
            if not await self._connect_mqtt(printer=printer, printer_name=printer_name):
                logger.error("Could not connect to `%s` via MQTT.", printer_name)
                return None

            status = await self._check_printer_status(
                printer=printer,
                printer_name=printer_name
            )

            if status is None:
                logger.warning("Connected to `%s`, but status is UNKNOWN.", printer_name)
                return None

            if not await self.wait_for_printer_ready(printer):
                logger.error("Printer values never became available")
                return None

            logger.info("Connected to `%s` with status `%s`.", printer_name, status)

            if not await light_printer_check(printer=printer):
                logger.error("Return None in the light_printer_check")
                return None

            return printer
        except (ConnectionError, TimeoutError) as e:
            logger.error("Connection issue while connecting to printer `%s`: %s", printer_name, e)
        except Exception: # pylint: disable=broad-exception-caught
            logger.exception("Unhandled exception during connect")
            return None

    @commands.hybrid_command(name="connect", description="Connect to a 3D Printer")
    async def connect(self,
                      ctx: commands.Context,
                      name: str,
                      ip: str,
                      serial: str,
                      access_code: str):  # pylint: disable=too-many-positional-arguments
        """Discord command to connect to a printer."""
        await ctx.defer(ephemeral=True)

        if not await self._validate_ip(ip):
            logger.error("Invalid IP address: `%s`.", ip)
            return

        logger.info("Attempting connection to printer: `%s`", name)

        printer_data = PrinterCredentials(ip=ip, access_code=access_code, serial=serial)
        printer = await self.connect_to_printer(printer_name=name, printer_data=printer_data)

        if printer is not None:
            try:
                self.connected_printers[name] = asdict(printer_data)
                self.storage.save(self.connected_printers)
            finally:
                await asyncio.to_thread(printer.disconnect)

    @tasks.loop(seconds=15)
    async def monitor_printers(self):
        """Periodically checks printer states and sends updates to Discord."""
        if not self.connected_printers:
            logger.debug("No printers in the list")
            return

        if self.status_channel is None:
            try:
                self.status_channel = await self.bot.fetch_channel(self.status_channel_id)
                logger.info("Successfully fetched channel")
            except discord.NotFound:
                # Channel ID is invalid or the bot can't find it
                logger.error("Channel with ID %s not found.", self.status_channel_id)
                return
            except discord.Forbidden:
                # Bot doesn't have permission to access the channel
                logger.error("Forbidden: Bot lacks permissions to fetch channel %s.",
                             self.status_channel_id)
                return
            except discord.HTTPException as e:
                # General HTTP request error (e.g., network issue, Discord API error)
                logger.error("HTTP error while fetching channel %s: %s", self.status_channel_id, e)
                return

        for printer_name, printer_data in self.connected_printers.items():
            printer = self.connected_printer_objects.get(printer_name)
            if printer is None or not printer.mqtt_client.is_connected():
                logger.warning("Printer %s is disconnected. Reconnecting...", printer_name)
                printer_object = await self.connect_to_printer(
                    printer_name=printer_name,
                    printer_data=get_printer_data_dict(printer_data=printer_data)
                )
                if printer_object is None:
                    logger.error("Failed to reconnect printer `%s`.", printer_name)
                    continue
                self.connected_printer_objects[printer_name] = printer_object
                logger.info("Reconnected to printer `%s`.", printer_name)

            printer = self.connected_printer_objects[printer_name]
            printer_current_state = self._check_printer_status(printer= printer,
                                                               printer_name= printer_name)
            if printer_current_state is not None:
                previous_state = self.previous_state_dict.get(printer_name)
                logger.info("Current state: %s is %s", printer_name, printer_current_state)
                logger.info("Previous state: %s", previous_state)

                if printer_current_state in (
                    GcodeState.RUNNING,
                    GcodeState.FINISH,
                    GcodeState.FAILED
                ):
                    if previous_state != printer_current_state:
                        await embed_printer_info(
                            printer_object=printer,
                            printer_name=printer_name,
                            set_image_callback=lambda pn=printer_name,
                            po=printer: set_image_custom_credentials_callback(
                                printer_name=pn,
                                printer_object=po
                            ),
                            status_channel=self.status_channel
                        )
                        logger.info(
                            "Printer `%s` state changed: %s ➜ %s",
                            printer_name,
                            previous_state,
                            printer_current_state
                        )
                        self.previous_state_dict[printer_name] = printer_current_state
            else:
                logger.exception("Can't get state for the `%s`. Removing from active list.",
                                 printer_name)
                await asyncio.to_thread(printer.disconnect)
                del self.connected_printer_objects[printer_name]


async def setup(bot):
    """Sets up the PrinterUtils cog."""
    await bot.add_cog(PrinterUtils(bot))
