# cogs/PrinterInfo.py

import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class Menu(discord.ui.Select):
    def __init__(self, ctx, printer_utils_cog, parent_cog, callback_status: int):
        self.parent_cog = parent_cog
        self.ctx = ctx
        self.callback_status = callback_status
        self.printer_utils_cog = printer_utils_cog

        options = [
            discord.SelectOption(label=printer_name)
            for printer_name in printer_utils_cog.connected_printers.keys()
        ]

        if not options:
            options = [discord.SelectOption(label="No printers connected", value="none", default=True)]

        super().__init__(
            placeholder="Please select a printer:",
            min_values=1,
            max_values=1,
            options=options,
            disabled=(options[0].value == "none")
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("No printers are currently connected.", ephemeral=True)
            return
         
        await interaction.response.defer(ephemeral=True)

        if self.callback_status == 0:
            await self.parent_cog.status_show_callback(self.ctx, self.values[0], self.printer_utils_cog)
        elif self.callback_status == 1:
            await self.parent_cog.connection_check_callback(self.ctx, self.values[0], self.printer_utils_cog)

class MenuView(discord.ui.View):
    def __init__(self, printer_utils_cog, parent_cog, ctx, callback_status: int):
        super().__init__()
        self.add_item(Menu(
            ctx=ctx,
            printer_utils_cog=printer_utils_cog,
            parent_cog=parent_cog,
            callback_status=callback_status
        ))


class PrinterInfo(commands.Cog, group_name="pinter_info", group_description="Display info about your 3D Printer"):
    def __init__(self, bot):
        self.bot = bot

    async def get_cog(self, ctx: commands.Context, name_of_cog: str):
        printer_utils_cog = self.bot.get_cog(name_of_cog)
        if not printer_utils_cog:
            await ctx.send("❌ Printer utilities not loaded.")
            return
        return printer_utils_cog

    async def check_printer_list(self, ctx: commands.Context, printer_utils_cog):
        if not printer_utils_cog.connected_printers:

            embed = discord.Embed(title="❌ No Printers in the list",
                                description="To add the printer use /connect", 
                                color=0x7309de)
            await ctx.send(embed=embed)

            return 
    async def get_printer_data(self, ctx: commands.Context, name_of_printer: str, printer_utils_cog):
        printer_info = printer_utils_cog.connected_printers.get(name_of_printer)

        if printer_info is None:
            # Handle the case where the printer doesn't exist
            print(f"❌ Printer '{name_of_printer}' not found.")
            return

        ip_printer = printer_info["ip"]
        serial_printer = printer_info["serial"]
        access_code_printer = printer_info["access_code"]

        return ip_printer, serial_printer, access_code_printer
    
    async def status_show_callback(self, ctx: commands.Context, name_of_printer: str, printer_utils_cog):
        await ctx.send(f"Status for printer: {name_of_printer}")

        ip_printer, serial_printer, access_code_printer = await self.get_printer_data(
                                        ctx = ctx,
                                        name_of_printer = name_of_printer,
                                        printer_utils_cog = printer_utils_cog
                                        )

        await printer_utils_cog.connect_to_printer(   ctx = ctx, name = name_of_printer,
                                                ip = ip_printer, serial = serial_printer, access_code  = access_code_printer)

        embed = discord.Embed(  title= f"Name {name_of_printer}:",
                                description="hmmmm 2D girl", 
                                color=0x7309de)
        embed.set_author(name=ctx.author.display_name, url="", icon_url=ctx.message.author.avatar.url)
        embed.set_thumbnail(url="https://i.pinimg.com/736x/42/40/ce/4240ce1dbd35a77bea5138b9e1a5a9f7.jpg")
        embed.add_field(name="Field 1", value="bla bla bla", inline=True)
        embed.add_field(name="Field 2", value="bla bla bla", inline=True)
        embed.set_footer(text="Thank you for reading")
        await ctx.send(embed=embed)


    async def connection_check_callback(self, ctx:commands.Context, name_of_printer: str, printer_utils_cog) -> (bool):
        ip_printer, serial_printer, access_code_printer = await self.get_printer_data(
                                        ctx = ctx,
                                        name_of_printer = name_of_printer,
                                        printer_utils_cog = printer_utils_cog
                                        )

        return await printer_utils_cog.connect_to_printer(  ctx = ctx, name = name_of_printer,
                                                            ip = ip_printer, serial = serial_printer, 
                                                            access_code  = access_code_printer
                                                            )


    @commands.hybrid_command(name="status", description="Display status of the printer")
    async def status(self, ctx: commands.Context):
        name_of_cog = "PrinterUtils"
        printer_utils_cog = await self.get_cog(ctx = ctx, name_of_cog = name_of_cog)
        await ctx.send(
            "📋 Select the printer option:",
            view=MenuView(printer_utils_cog=printer_utils_cog, parent_cog=self, ctx=ctx , callback_status = 0)
        )

    @commands.hybrid_command(name="list", description="Display list of the printer")
    async def list_all_printers(self, ctx: commands.Context):
        name_of_cog = "PrinterUtils"
        printer_utils_cog = await self.get_cog(ctx = ctx, name_of_cog = name_of_cog)

        if not printer_utils_cog.connected_printers:
            await ctx.send("No Printers in the list")
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
            view=MenuView(printer_utils_cog=printer_utils_cog, parent_cog=self, ctx=ctx,  callback_status = 1)
        )

# discord​‐py ≥ 2.0 expects an *async* setup function
async def setup(bot):
    await bot.add_cog(PrinterInfo(bot))
