# cogs/PrinterInfo.py

import discord
from discord.ext import commands
from discord import app_commands
import logging
from .utils.enums import MenuCallBack
from .ui.printer_menu import MenuView
import bambulabs_api as bl
from typing import Optional


from .utils import get_printer_data
from .utils import printer_error_handler
from .utils import finish_time_format
from .utils import get_camera_frame

logger = logging.getLogger(__name__)

class PrinterInfo(commands.Cog, group_name="pinter_info", group_description="Display info about your 3D Printer"):
    def __init__(self, bot):
        self.bot = bot

    async def get_cog(self, ctx: commands.Context, name_of_cog: str)  -> Optional[bl.Printer]:
        printer_cog = self.bot.get_cog(name_of_cog)
        if not printer_cog:
            logger.error(f"Can't load cog with name: {name_of_cog}")
            return None
        return printer_cog

    async def check_printer_list(self, ctx: commands.Context, printer_utils_cog):
        if not printer_utils_cog.connected_printers:

            embed = discord.Embed(title="❌ No Printers in the list",
                                description="To add the printer use /connect", 
                                color=0x7309de)
            
            await ctx.send(embed=embed)

            return 

    async def embed_printer_info(self, ctx: commands.Context, printer_object:bl.Printer, name_of_printer: str):
        if printer_object.get_state() == "RUNNING":
            await get_camera_frame(printer_object=printer_object, name_of_printer=name_of_printer)
            image_filename = f"camera_frame_{name_of_printer}.png"
            image_main_location = discord.File(f"img/{image_filename}", filename=image_filename)
            embed_set_image_url = f"attachment://{image_filename}"
        else:
            image_filename = "default_camera_frame.png"
            image_main_location = discord.File(f"img/{image_filename}", filename=image_filename)
            embed_set_image_url = f"attachment://{image_filename}"

        embed = discord.Embed(
            title=f"Name: {name_of_printer}",
            description="Status of the printer:",
            color=0x7309de
        )
        
        embed.set_author(
            name=ctx.author.display_name,
            url="",
            icon_url=ctx.author.avatar.url  # updated to use ctx.author for clarity
        )
        
        embed.set_thumbnail(url="https://i.pinimg.com/736x/42/40/ce/4240ce1dbd35a77bea5138b9e1a5a9f7.jpg")

        embed.add_field(
            name="Print Time",
            value=(
                f"`Current:` {printer_object.get_time()}\n"
                f"`Finish:`  {await finish_time_format(printer_object.get_time())}\n"
            ),
            inline=True
        )

        embed.add_field(
            name="Progress",
            value=(
                f"`Percent:` {printer_object.get_percentage()}%\n"
                f"`Layer:`   {printer_object.current_layer_num()}/{printer_object.total_layer_num()}\n"
                f"`Speed:`   {printer_object.get_print_speed()} (100%)\n"
            ),
            inline=True
        )

        embed.add_field(
            name="Lights",
            value=(
                f"`Chamber:` {printer_object.get_light_state()}\n"
            ),
            inline=True
        )

        embed.add_field(
            name="Temps",
            value=(
                f"`Bed:`     {printer_object.get_bed_temperature()}°C\n"
                f"`Nozzle:`  {printer_object.get_nozzle_temperature()}°C\n"
                f"`Chamber:` {printer_object.get_chamber_temperature()}°C\n"
            ),
            inline=True
        )

        embed.add_field(
            name="Fans",
            value=(
                f"`Main 1:`   {printer_object.mqtt_client.get_part_fan_speed()}%\n"
                f"`Main 2:`   {printer_object.mqtt_client.get_aux_fan_speed()}%\n"
                f"`Cooling:`  {printer_object.mqtt_client.get_chamber_fan_speed()}%\n"
            ),
            inline=True
        )

        embed.add_field(
            name="Errors",
            value=f"`Error:` {await printer_error_handler(printer_object=printer_object)}",
            inline=False
        )

        embed.add_field(
            name="\u200b",  # Blank field name for layout
            value=f"{await printer_error_handler(printer_object=printer_object)}",
            inline=False
        )

        embed.set_image(url=embed_set_image_url)

        await ctx.send(file=image_main_location, embed=embed)


    async def connection_check_callback(self, ctx:commands.Context, name_of_printer: str, printer_utils_cog):
        ip_printer, serial_printer, access_code_printer = await get_printer_data(
                                        ctx = ctx,
                                        name_of_printer = name_of_printer,
                                        printer_utils_cog = printer_utils_cog
                                        )

        return await printer_utils_cog.connect_to_printer(  ctx = ctx, name = name_of_printer,
                                                            ip = ip_printer, serial = serial_printer, 
                                                            access_code  = access_code_printer
                                                            )

    async def status_show_callback(self, ctx: commands.Context, name_of_printer: str, printer_utils_cog):
        await ctx.send(f"Status for printer: {name_of_printer}")

        printer_object = await self.connection_check_callback(ctx=ctx, name_of_printer=name_of_printer, printer_utils_cog=printer_utils_cog)
        
        if printer_object is None:
            return
        
        await self.embed_printer_info(ctx=ctx, printer_object=printer_object, name_of_printer=name_of_printer)

    @commands.hybrid_command(name="status", description="Display status of the printer")
    async def status(self, ctx: commands.Context):
        name_of_cog = "PrinterUtils"
        printer_utils_cog = await self.get_cog(ctx = ctx, name_of_cog = name_of_cog)

        if printer_utils_cog is None:
            await ctx.send(f"Can't load cog with name: {name_of_cog}")
            return
        
        await ctx.send(
            "📋 Select the printer option:",
            view=MenuView(printer_utils_cog=printer_utils_cog, parent_cog=self, ctx=ctx , callback_status = MenuCallBack.CALLBACK_STATUS_SHOW)
        )

    @commands.hybrid_command(name="list", description="Display list of the printer")
    async def list_all_printers(self, ctx: commands.Context):
        name_of_cog = "PrinterUtils"
        printer_utils_cog = await self.get_cog(ctx = ctx, name_of_cog = name_of_cog)

        if not printer_utils_cog.connected_printers:
            await ctx.send("❌ No Printers in the list.")
            return 
        
        description = "\n".join(f"• {name}" for name in printer_utils_cog.connected_printers)
        embed = discord.Embed(
            title="🖨️ Connected Printers",
            description=description,
            color=discord.Color.blue()
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="check_connection", description="Check connection of the 3D printer")
    async def check_connection(self, ctx: commands.Context):
        name_of_cog = "PrinterUtils"
        printer_utils_cog = await self.get_cog(ctx = ctx, name_of_cog = name_of_cog)
        
        await self.check_printer_list(ctx = ctx, printer_utils_cog= printer_utils_cog)
        await ctx.send(
            "📋 Select the printer option:",
            view=MenuView(printer_utils_cog=printer_utils_cog, parent_cog=self, ctx=ctx,  callback_status = MenuCallBack.CALLBACK_CONNECTION_CHECK)
        )

# discord​‐py ≥ 2.0 expects an *async* setup function
async def setup(bot):
    await bot.add_cog(PrinterInfo(bot))
