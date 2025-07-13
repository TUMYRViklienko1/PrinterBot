# cogs/printer.py

from __future__ import annotations
from discord.ext import commands
import discord
import bambulabs_api as bl
import time
from discord import app_commands, Interaction
import json, asyncio, pathlib
from pathlib import Path
import logging
import ipaddress

from discord import app_commands


logger = logging.getLogger(__name__)

class PrinterUtils(commands.GroupCog, group_name="printer_utils", group_description="Control 3D printers"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.printer_file = Path("data/printer.jason")
        self.connected_printers = self.load_printers()
        self.printer = None 

    def load_printers(self):
        if not self.printer_file.exists():
            return {}
        with open(self.printer_file) as file_read:
            return json.load(file_read)
    
    def save_printers(self):
        with open(self.printer_file, "w") as file_write:
            json.dump(self.connected_printers, file_write, indent=4)
    
    async def validate_ip(self, ctx: commands.Context, ip:str) -> (bool):
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            await ctx.send(f"❌ Invalid IP address: `{ip}`.")
            return False


    async def connect_to_printer(self,ctx: commands.Context , name: str, ip: str, serial: str, access_code: str) -> (bl.Printer):
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
                #printer.mqtt_stop()
                printer.camera_client.stop()
                printer.mqtt_stop()
                #stop connection
                return None

            for _ in range(10):
                status = printer.get_state()
                if status != "UNKNOWN":
                    break
                await asyncio.sleep(0.3)
            else:
                await ctx.send(f"⚠️ Connected to `{name}`, but status is UNKNOWN.")
                return None
            
            
            await ctx.send(f"✅ Connected to `{name}` with status `{status}`.")
            return printer
        
        except Exception as e:
            logger.exception("Unhandled exception during connect")
            await ctx.send(f"❌ Error occurred: `{str(e)}`")
        

    @commands.hybrid_command(name="connect", description="Connect to a 3D printer")
    async def connect(self, ctx: commands.Context, name: str, ip: str, serial: str, access_code: str):
        await ctx.defer(ephemeral=True)

        # Continue as usual...
        if await self.validate_ip(ctx, ip) == False:
            logger.warning(f"❌ Invalid IP address: `{ip}`.")
            return

        logger.info(f"Attempting connection to printer: {name}")

        self.connected_printers[name] = {
            "ip": ip,
            "serial": serial,
            "access_code": access_code
        }

        printer = await self.connect_to_printer(ctx, name=name, ip=ip, serial=serial, access_code=access_code)
        if printer:
            self.save_printers()
            printer.disconnect()


    # @commands.hybrid_command(name="status", description="Status of the printer")
    # async def status(
    #     self,
    #     ctx: commands.Context,
    #     name: str
    # ):
    #     bed_temperature = self.printer.get_bed_temperature()
    #     chamber_temperature = self.printer.get_chamber_temperature()
    #     nozzle_temperature = self.printer.get_nozzle_temperature()


    #     embed = discord.Embed(  title=f"Name of the printer: {name}",
    #                             url="https://google.com",
    #                             description="This is your printer", 
    #                             color=0x7309de)
    #     embed.set_author(name=ctx.author.display_name, url="", icon_url=ctx.message.author.avatar.url)
    #     embed.set_thumbnail(url="https://i.pinimg.com/736x/42/40/ce/4240ce1dbd35a77bea5138b9e1a5a9f7.jpg")
    #     embed.add_field(name="Full temperature", value=f"The bed temperature: {bed_temperature}", inline=True)
    #     embed.add_field(name="Full temperature", value=f"The bed temperature: {chamber_temperature}", inline=True)
    #     embed.add_field(name="Full temperature", value=f"The bed temperature: {nozzle_temperature}", inline=True)

    #     embed.set_footer(text="Thank you for reading")
    #     await ctx.send(embed=embed)
        


async def setup(bot):
    await bot.add_cog(PrinterUtils(bot))

