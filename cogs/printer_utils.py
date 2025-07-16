# cogs/printer.py

from __future__ import annotations
from discord.ext import commands
import bambulabs_api as bl
import asyncio
import json, asyncio, pathlib
from pathlib import Path
import logging
import ipaddress
from discord.ext import commands, tasks

from typing import Optional

logger = logging.getLogger(__name__)

class PrinterUtils(commands.GroupCog, group_name="printer_utils", group_description="Control 3D printers"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.printer_file = Path("data/printer.jason")
        self.connected_printers = self.load_printers()
        self.bot.connected_printers = self.connected_printers
        self.printer = None 
        self.monitor_printers.start()

    def get_connected_printers(self) -> (dict):
        return self.connected_printers

    def load_printers(self):
        if not self.printer_file.exists():
            return {}
        with open(self.printer_file) as file_read:
            return json.load(file_read)
    
    def save_printers(self):
        with open(self.printer_file, "w") as file_write:
            json.dump(self.connected_printers, file_write, indent=4)
    
    async def validate_ip(self, ctx: commands.Context, ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            logger.error(f"❌ Invalid IP address: `{ip}`.")
            await ctx.send(f"Invalid IP address: `{ip}`.")
            return False
        return True
            

    async def light_printer_check(self, ctx, printer):
        async def check_light(action_func, action_name):
            if action_func():
                print(f"Light {action_name} successfully.")
            else:
                print(f"Light NOT {action_name} successfully.")
        
        await check_light(printer.turn_light_on, "turned on")
        await asyncio.sleep(1)
        await check_light(printer.turn_light_off, "turned off")

    async def connect_to_printer(
    self,
    ctx: commands.Context,
    name: str,
    ip: str,
    serial: str,
    access_code: str
    ) -> Optional[bl.Printer]:
        try:
            printer = bl.Printer(ip, access_code, serial)
            printer.connect()

            for _ in range(10):
                if printer.mqtt_client.is_connected():
                    break
                await asyncio.sleep(0.3)
            else:
                logger.error("Failed to connect to printer via MQTT.")
                await ctx.send(f"❌ Could not connect to `{name}` via MQTT.")
                #Could be incorrect solution. 
                await asyncio.to_thread(printer.disconnect)

                return None

            for _ in range(10):
                status = printer.get_state()
                if status != "UNKNOWN":
                    break
                await asyncio.sleep(0.3)
            else:
                await ctx.send(f"⚠️ Connected to `{name}`, but status is UNKNOWN.")
                logger.warning(f"Connected to `{name}`, but status is UNKNOWN.")
                return None
            
            
            await ctx.send(f"✅ Connected to `{name}` with status `{status}`.")
            logger.debug(f"✅ Connected to `{name}` with status `{status}`.")

            await self.light_printer_check(ctx = ctx, printer = printer)

            return printer
        
        except Exception as e:
            logger.exception("Unhandled exception during connect")
            await ctx.send(f"❌ Error occurred: `{str(e)}`")
            return None
            
        

    @commands.hybrid_command(name="connect", description="Connect to a 3D Printer")
    async def connect(self, ctx: commands.Context, name: str, ip: str, serial: str, access_code: str):
        await ctx.defer(ephemeral=True)

        # Continue as usual...
        if not await self.validate_ip(ctx, ip):
            return

        logger.info(f"Attempting connection to printer: {name}")

        printer = await self.connect_to_printer(ctx, name=name, ip=ip, serial=serial, access_code=access_code)

        if printer is not None:
            try:

                self.connected_printers[name] = {
                    "ip": ip,
                    "serial": serial,
                    "access_code": access_code
                }

                self.save_printers()
            finally:
                await asyncio.to_thread(printer.disconnect)

    @tasks.loop(seconds = 5)
    async def monitor_printers(self):
        channel = self.bot.get_channel(1391080605122297916)
        if channel:
            await channel.send(f"🟢 Print started on")

async def setup(bot):
    await bot.add_cog(PrinterUtils(bot))

