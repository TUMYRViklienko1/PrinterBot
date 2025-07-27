# pylint: disable=unused-argument

"""
Discord UI View for controlling a Bambu Labs printer via buttons.
"""

import asyncio

import bambulabs_api as bl
from bambulabs_api.states_info import GcodeState

import discord


class PrinterControlView(discord.ui.View):
    """
    A Discord UI View that provides printer control buttons for a Bambu Labs printer.
    
    Controls are automatically disabled if the printer is unavailable.
    """

    def __init__(self, printer: bl.Printer, printer_name: str):
        """
        Initialize the printer control view.
        """
        super().__init__()
        self.printer = printer
        self.printer_name = printer_name
        self.disable_controls = printer is None

        # Dynamically disable certain buttons if the printer is unavailable
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id in {
                "pause_button", "resume_button", "stop_button", "light_button"
            }:
                child.disabled = self.disable_controls

    @discord.ui.button(
        style=discord.ButtonStyle.primary,
        emoji="⏸️",
        label="Pause",
        custom_id="pause_button",
    )
    async def pause_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button["PrinterControlView"]):
        """
        Pause the current print job on the printer.
        """

        await interaction.response.defer()

        success = self.printer.pause_print()
        await asyncio.sleep(1.5)  # Wait a moment for state to change
        new_state = self.printer.get_state()

        if success and new_state == GcodeState.PAUSE:
            message = f"✅ '{self.printer_name}' was paused successfully"
        else:
            message = f"❌ Failed to pause '{self.printer_name}'"

        await interaction.followup.send(message)

    @discord.ui.button(
        style=discord.ButtonStyle.primary,
        emoji="▶️",
        label="Resume",
        custom_id="resume_button",
    )
    async def resume_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button["PrinterControlView"]):
        """
        Resume the current paused print job on the printer.
        """
        await interaction.response.defer()

        success = self.printer.resume_print() if self.printer else False
        message = (
            f"✅ '{self.printer_name}' was resumed successfully"
            if success else
            f"❌ Failed to resume '{self.printer_name}'"
        )
        await interaction.followup.send(message)

    @discord.ui.button(
        style=discord.ButtonStyle.primary,
        emoji="🛑",
        label="Stop",
        custom_id="stop_button",
    )
    async def stop_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button["PrinterControlView"]):
        """
        Stop the current print job on the printer.
        """
        await interaction.response.defer()

        success = self.printer.stop_print() if self.printer else False
        message = (
            f"✅ '{self.printer_name}' was stopped successfully"
            if success else
            f"❌ Failed to stop '{self.printer_name}'"
        )
        await interaction.followup.send(message)

    @discord.ui.button(
        style=discord.ButtonStyle.primary,
        emoji="💡",
        label="Light",
        custom_id="light_button",
    )
    async def light_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button["PrinterControlView"]):
        """
        Toggle the printer's light on or off.
        """
        await interaction.response.defer()

        light_state = self.printer.get_light_state() if self.printer else None

        if light_state == "on":
            success = self.printer.turn_light_off()
            message = (
                f"✅ Light on '{self.printer_name}' was turned off successfully"
                if success else
                f"❌ Failed to turn off the light on '{self.printer_name}'"
            )
        else:
            success = self.printer.turn_light_on()
            message = (
                f"✅ Light on '{self.printer_name}' was turned on successfully"
                if success else
                f"❌ Failed to turn on the light on '{self.printer_name}'"
            )

        await interaction.followup.send(message)
