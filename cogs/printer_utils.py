"""Utilities for managing 3D printer connections, MQTT, and monitoring."""
# pylint: disable=too-many-arguments, too-many-positional-arguments

import asyncio
import logging
import ipaddress
import os
from dataclasses import asdict
from typing import Dict, Optional

import discord
from discord.ext import commands, tasks
import bambulabs_api as bl
from bambulabs_api.states_info import GcodeState

from .ui.embed_helpers import embed_printer_info

from .utils import ( # type: ignore[attr-defined]
    PrinterCredentials,
    PrinterStorage,
    set_image_custom_credentials_callback,
    get_printer_data_dict,
    PrinterDataDict,
    _validate_ip,
    _check_printer_status,
    connect_to_printer
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
        if CHANEL_ID is None:
            raise ValueError("CHANEL_ID environment variable not set")
        self.status_channel_id = int(CHANEL_ID)
        self.status_channel: Optional[discord.TextChannel] = None
        self.monitor_printers.start()

    @commands.hybrid_command(  # type: ignore[arg-type]
        name="connect",
        description="Connect to a 3D Printer")
    async def connect(self,
                      ctx: commands.Context[commands.Bot],
                      name: str,
                      ip: str,
                      serial: str,
                      access_code: str):  # pylint: disable=too-many-positional-arguments
        """Discord command to connect to a printer."""
        await ctx.defer(ephemeral=True)

        if not await _validate_ip(ip):
            logger.error("Invalid IP address: `%s`.", ip)
            return

        logger.info("Attempting connection to printer: `%s`", name)

        printer_data = PrinterCredentials(ip=ip, access_code=access_code, serial=serial)
        printer = await connect_to_printer(printer_name=name, printer_data=printer_data)
        if printer is not None:
            try:
                self.connected_printers[name] = asdict(printer_data)  # type: ignore[assignment]
                self.storage.save(self.connected_printers)
            finally:
                await asyncio.to_thread(printer.disconnect)
    # pylint: disable=too-many-branches
    @tasks.loop(seconds=15)
    async def monitor_printers(self):
        """Periodically checks printer states and sends updates to Discord."""
        if not self.connected_printers:
            logger.debug("No printers in the list")
            return

        if self.status_channel is None:
            try:
                self.status_channel = await self.bot.fetch_channel(
                    self.status_channel_id
                )  # type: ignore[assignment]
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

        for printer_name, printer_data in list(self.connected_printers.items()):
            printer = self.connected_printer_objects.get(printer_name)
            if printer is None or not printer.mqtt_client.is_connected():
                logger.warning("Printer %s is disconnected. Reconnecting...", printer_name)
                printer_object = await connect_to_printer(
                    printer_name=printer_name,
                    printer_data=get_printer_data_dict(printer_data=printer_data)
                )
                if printer_object is None:
                    logger.error("Failed to reconnect printer `%s`.", printer_name)
                    continue
                self.connected_printer_objects[printer_name] = printer_object
                logger.info("Reconnected to printer `%s`.", printer_name)

            printer = self.connected_printer_objects[printer_name]
            if printer is None:
                continue
            printer_current_state = await _check_printer_status(
                printer= printer,
                printer_name= printer_name
                )
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
                            set_image_callback=lambda pn=printer_name,# type: ignore[misc]
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
    try:
        await bot.add_cog(PrinterUtils(bot))
    except ValueError:
        logger.error("CHANEL_ID environment variable not set")
