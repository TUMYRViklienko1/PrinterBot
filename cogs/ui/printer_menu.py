"""UI components for printer selection menu."""

import discord
from discord.ext import commands

from cogs.utils.enums import MenuCallBack


class Menu(discord.ui.Select):  # type: ignore[type-arg]
    """Dropdown menu for selecting a printer."""

    def __init__(
        self,
        ctx: commands.Context[commands.Bot],
        printer_utils_cog,
        parent_cog,
        callback_status: int,
    ):
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
            disabled=False,
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle selection callback."""
        if self.values[0] == "none":
            await interaction.response.send_message(
                "No printers are currently connected.",
                ephemeral=True,
            )
            return

        if self.callback_status == MenuCallBack.CALLBACK_STATUS_SHOW:
            await interaction.response.defer(ephemeral=True)
            await self.parent_cog.status_show_callback(
                ctx=self.ctx,
                printer_name=self.values[0],
                printer_utils_cog=self.printer_utils_cog,
            )
        elif self.callback_status == MenuCallBack.CALLBACK_CONNECTION_CHECK:
            await interaction.response.defer(ephemeral=True)
            await self.parent_cog.connection_check_callback(
                ctx=self.ctx,
                printer_name=self.values[0],
                printer_utils_cog=self.printer_utils_cog
            )
        elif self.callback_status == MenuCallBack.CALLBACK_DELETE_PRINTER:
            await self.parent_cog.delete_printer_callback(
                ctx=self.ctx,
                printer_name=self.values[0],
                printer_utils_cog=self.printer_utils_cog
            )
        elif self.callback_status == MenuCallBack.CALLBACK_EDIT_PRINTER:
            await self.parent_cog.edit_printer_callback(
                interaction = interaction,
                printer_name=self.values[0],
                printer_utils_cog=self.printer_utils_cog
            )

class MenuView(discord.ui.View):
    """View containing the printer selection menu."""

    def __init__(
        self,
        printer_utils_cog,
        parent_cog,
        ctx: commands.Context[commands.Bot],
        callback_status: int,
    ):
        super().__init__()
        self.add_item(
            Menu(
                ctx=ctx,
                printer_utils_cog=printer_utils_cog,
                parent_cog=parent_cog,
                callback_status=callback_status,
            )
        )
