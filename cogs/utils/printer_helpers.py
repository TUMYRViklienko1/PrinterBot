import discord
from discord.ext import commands

async def get_printer_data(ctx: commands.Context, name_of_printer: str, printer_utils_cog):
    printer_info = printer_utils_cog.connected_printers.get(name_of_printer)

    if printer_info is None:
        # Handle the case where the printer doesn't exist
        print(f"❌ Printer '{name_of_printer}' not found.")
        return

    ip_printer = printer_info["ip"]
    serial_printer = printer_info["serial"]
    access_code_printer = printer_info["access_code"]

    return ip_printer, serial_printer, access_code_printer

async def printer_error_handler(printer_object):
    printer_error_code = printer_object.print_error_code()
    if printer_error_code == 0:
        return "No errors."
    else:
        return f"Printer Error Code: {printer_error_code}"