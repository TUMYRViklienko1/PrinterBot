# cogs/printer.py

import asyncio
import json
import logging
import os
import ipaddress
from pathlib import Path
from dataclasses import asdict

import bambulabs_api as bl
from bambulabs_api import GcodeState
from discord.ext import commands, tasks
from typing import Optional

from .ui import embed_printer_info

from .utils import PrinterCredentials
from .utils import PrinterStorage
from .utils import light_printer_check
from .utils import get_cog
from .utils import set_image_custom_credentials_callback
from .utils import get_printer_data_dict

logger = logging.getLogger(__name__)
CHANEL_ID = os.getenv("CHANEL_ID")


class PrinterUtils(commands.GroupCog, group_name="printer_utils", group_description="Control 3D printers"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.storage = PrinterStorage()
        self.connected_printers:dict = self.storage.load()
        self.monitor_printers.start()
        self.ctx = commands.Context
        self.previous_state_dict:dict = {}


    async def _validate_ip(self, ctx: commands.Context, ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            await ctx.send(f"❌ Invalid IP address: `{ip}`.")
            return False
        return True
            
    def _create_printer(self, printer_data: PrinterCredentials) -> bl.Printer:
        printer = bl.Printer(printer_data.ip, printer_data.access_code, printer_data.serial)
        printer.connect()
        return printer
    
    async def _connect_mqtt(self, ctx:commands.Context, printer: bl.Printer, printer_name: str) -> bool:
        for _ in range(10):
            if printer.mqtt_client.is_connected():
                return True
            await asyncio.sleep(0.3)

        await ctx.send(f"❌ Could not connect to `{printer_name}` via MQTT.")
        await asyncio.to_thread(printer.disconnect)
        return False

    async def _check_printer_status(self, ctx:commands.Context, printer: bl.Printer, printer_name: str) -> Optional[str]:
        for _ in range(10):
            status = printer.get_state()
            if status != "UNKNOWN":
                return status
            await asyncio.sleep(0.3)

        await ctx.send(f"⚠️ Connected to `{printer_name}`, but status is UNKNOWN.")
        logger.warning(f"Connected to `{printer_name}`, but status is UNKNOWN.")
        return None


    async def connect_to_printer(
    self,
    ctx: commands.Context,
    printer_name: str,
    printer_data: PrinterCredentials
    ) -> Optional[bl.Printer]:
        try:

            printer = self._create_printer(printer_data = printer_data)

            if await self._connect_mqtt(ctx=ctx, printer=printer, printer_name=printer_name) is False:
                logger.error(f"Could not connect to `{printer_name}` via MQTT.")
                return None

            status = await self._check_printer_status(ctx=ctx, printer=printer, printer_name=printer_name) 

            if status is None:
                logger.warning(f"Connected to `{printer_name}`, but status is UNKNOWN.")
                return None
            
            await ctx.send(f"✅ Connected to `{printer_name}` with status `{status}`.")
            logger.debug(f"Connected to `{printer_name}` with status `{status}`.")

            if not await light_printer_check(ctx = ctx, printer = printer):
                logger.error("return none in the light_printer_check")
                return None

            return printer
        
        except Exception as e:
            logger.exception("Unhandled exception during connect")
            await ctx.send(f"❌ Error occurred: `{str(e)}`")
            return None
            
        

    @commands.hybrid_command(name="connect", description="Connect to a 3D Printer")
    async def connect(self, ctx: commands.Context, name: str, ip: str, access_code: str, serial: str):
        await ctx.defer(ephemeral=True)

        # Continue as usual...
        if not await self._validate_ip(ctx, ip):
            logger.error(f" Invalid IP address: `{ip}`.")
            return

        logger.info(f"Attempting connection to printer: {name}")

        printer_data = PrinterCredentials(ip=ip, access_code= access_code, serial= serial)

        printer = await self.connect_to_printer(ctx, name=name, printer_data= printer_data)

        if printer is not None:
            try:

                self.connected_printers[name] = asdict(printer_data)
                self.storage.save(self.connected_printers)

            finally:
                await asyncio.to_thread(printer.disconnect)

    @tasks.loop(seconds=5)
    async def monitor_printers(self):
        if not self.connected_printers:
            logger.debug("No printers in the list")
            return

        for printer_name, printer_data in self.connected_printers.items():
            printer_credentials = get_printer_data_dict(printer_data=printer_data)
            printer = await self.connect_to_printer(
                ctx=self.ctx,
                printer_name=printer_name,
                printer_data=printer_credentials
            )
            if printer is None:
                logger.info(f"Skip status check for printer {printer_name}")
                continue

            printer_current_state = printer.get_state()
            previous_state = self.previous_state_dict.get(printer_name)

            if printer_current_state in (GcodeState.RUNNING, GcodeState.FINISH, GcodeState.FAILED):
                if previous_state != printer_current_state:
                    await embed_printer_info(
                        ctx=self.ctx,
                        printer_object=printer,
                        printer_name=printer_name,
                        set_image_callback=set_image_custom_credentials_callback(
                            printer_name=printer_name,
                            printer_object=printer
                        )
                    )
                    self.previous_state_dict[printer_name] = printer_current_state
                
            

async def setup(bot):
    await bot.add_cog(PrinterUtils(bot))

