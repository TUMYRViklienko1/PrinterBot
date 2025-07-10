# cogs/printer.py

from __future__ import annotations
from discord.ext import commands
import discord
import bambulabs_api as bl
import time
from discord import app_commands, Interaction
import json, asyncio, pathlib


class PrinterCog(commands.GroupCog, group_name="printer", group_description="Control 3D printers"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.printer = None

    @commands.hybrid_command(name="connect", description="Connect to a 3D printer")
    async def connect(
        self,
        ctx: commands.Context,
        name: str,
        ip: str,                               # ② add type hints (all default to str anyway)
        serial: str,
        access_code: str
    ):
        print('Starting bambulabs_api example')
        print('Connecting to BambuLab 3D printer')
        print(f'ip: {ip}')
        print(f'serial: {serial}')
        print(f'Access Code: {access_code}')

        # Create a new instance of the API
        self.printer = bl.Printer(ip, access_code, serial)

        # Connect to the BambuLab 3D printer
        self.printer.connect()
        self.status = self.printer.get_state()
        print(f'Printer status: {self.status}')
         
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
        


# discord‑py ≥ 2.0 expects an *async* setup function
async def setup(bot):
    await bot.add_cog(PrinterCog(bot))

