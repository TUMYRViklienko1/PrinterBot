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

logger = logging.getLogger(__name__)

class PrinterCog(commands.GroupCog, group_name="printer", group_description="Control 3D printers"):
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
    
    

    @commands.hybrid_command(name="connect", description="Connect to a 3D printer")
    async def connect(
        self,
        ctx: commands.Context,
        name: str,
        ip: str,                              
        serial: str,
        access_code: str
    ):

        logger.debug(f'ip: {ip}')
        logger.debug(f'serial: {serial}')
        logger.debug(f'Access Code: {access_code}')
        
        self.connected_printers[name] = {
            "ip" : ip,
            "serial" : serial,
            "access_code" : access_code
        }
        self.save_printers()
        # Create a new instance of the API
        self.printer = bl.Printer(ip, access_code, serial)

        # Connect to the BambuLab 3D printer
        logger.info(f"Connection to the print: {name}")
        self.printer.connect()

        for _ in range(10):  # max 10 attempts (~3s)
            status = self.printer.get_state()
            if status != "UNKNOWN":
                break
            time.sleep(0.3)

        logger.info(f'Printer status: {self.status}')
         
        self.printer.disconnect()

    @commands.hybrid_command(name="status", description="Status of the printer")
    async def status(
        self,
        ctx: commands.Context,
        name: str
    ):
        bed_temperature = self.printer.get_bed_temperature()
        chamber_temperature = self.printer.get_chamber_temperature()
        nozzle_temperature = self.printer.get_nozzle_temperature()


        embed = discord.Embed(  title=f"Name of the printer: {name}",
                                url="https://google.com",
                                description="This is your printer", 
                                color=0x7309de)
        embed.set_author(name=ctx.author.display_name, url="", icon_url=ctx.message.author.avatar.url)
        embed.set_thumbnail(url="https://i.pinimg.com/736x/42/40/ce/4240ce1dbd35a77bea5138b9e1a5a9f7.jpg")
        embed.add_field(name="Full temperature", value=f"The bed temperature: {bed_temperature}", inline=True)
        embed.add_field(name="Full temperature", value=f"The bed temperature: {chamber_temperature}", inline=True)
        embed.add_field(name="Full temperature", value=f"The bed temperature: {nozzle_temperature}", inline=True)

        embed.set_footer(text="Thank you for reading")
        await ctx.send(embed=embed)
        


async def setup(bot):
    await bot.add_cog(PrinterCog(bot))

