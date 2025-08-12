"""Global role check and error handler setup for the bot."""

import discord
from discord.ext import commands

def setup_global_check(bot: commands.Bot):
    """
    Registers a global check on the bot to ensure that only users with
    the 'PrinterManager' role can execute commands.

    Args:
        bot (commands.Bot): The bot instance to register the check on.
    """
    @bot.check
    async def has_printer_role(ctx):
        printer_role = discord.utils.get(ctx.author.roles, name="PrinterManager")
        return printer_role is not None

def setup_global_error_handler(bot: commands.Bot):
    """
    Registers a global error handler to catch permission-related errors
    and send user-friendly messages.

    Args:
        bot (commands.Bot): The bot instance to register the error handler on.
    """
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send(f"❌ You need the **{error.missing_role}** role to use this command.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("❌ You do not have permission to use this command.")
        else:
            raise error
