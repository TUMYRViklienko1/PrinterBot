import discord
from discord.ext import commands

from ..utils import MenuCallBack

class Menu(discord.ui.Select):
    def __init__(self, ctx:commands.Context, printer_utils_cog, parent_cog, callback_status: int):
        self.parent_cog = parent_cog
        self.ctx = ctx
        self.callback_status = callback_status
        self.printer_utils_cog = printer_utils_cog

        options = [
            discord.SelectOption(label=printer_name)
            for printer_name in printer_utils_cog.connected_printers.keys()
        ]

        super().__init__(
            placeholder="Please select a printer:",
            min_values=1,
            max_values=1,
            options=options,
            disabled= False
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("No printers are currently connected.", ephemeral=True)
            return
         
        await interaction.response.defer(ephemeral=True)

        if self.callback_status == MenuCallBack.CALLBACK_STATUS_SHOW:
            await self.parent_cog.status_show_callback(self.ctx, self.values[0], self.printer_utils_cog)
        elif self.callback_status == MenuCallBack.CALLBACK_CONNECTION_CHECK:
            await self.parent_cog.connection_check_callback(self.ctx, self.values[0], self.printer_utils_cog)

class MenuView(discord.ui.View):
    def __init__(self, printer_utils_cog, parent_cog, ctx:commands.Context, callback_status: int):
        super().__init__()
        self.add_item(Menu(
            ctx=ctx,
            printer_utils_cog=printer_utils_cog,
            parent_cog=parent_cog,
            callback_status=callback_status
        ))
