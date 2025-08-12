"""add docstring ..."""

from dataclasses import asdict
import traceback
import re

from typing import TYPE_CHECKING

import discord

from cogs.utils import (
    PrinterCredentials,
    delete_printer,
    connect_new_printer
)

if TYPE_CHECKING:
    from cogs.printer_utils import PrinterUtils

class PrinterEditModal(discord.ui.Modal, title="printer_edit_modal"):
    """
    Modal dialog for editing the credentials of an existing printer.

    Attributes:
        printer_name_original (str): The original name of the printer being edited.
        printer_utils_cog (PrinterUtils): Reference to the printer utilities cog.
        field_name (discord.ui.TextInput): Input field for the printer name.
        field_ip (discord.ui.TextInput): Input field for the printer IP address.
        field_access_code (discord.ui.TextInput): Input field for the printer access code.
        field_serial (discord.ui.TextInput): Input field for the printer serial number.
    """

    def __init__(self, printer_name: str, printer_utils_cog: 'PrinterUtils') -> None:
        """
        Initialize the modal with current printer data pre-filled.

        Args:
            printer_name (str): The name of the printer to edit.
            printer_utils_cog (PrinterUtils): The cog managing printer utilities.
        """
        super().__init__()
        self.printer_name_original = printer_name
        self.printer_utils_cog = printer_utils_cog
        self.new_printer_name = ""
        printer_credentials = printer_utils_cog.connected_printers[printer_name]

        # Initialize input fields with existing printer data
        self.field_name = discord.ui.TextInput(
            label="Printer Name",
            style=discord.TextStyle.short,
            default=printer_name,
            placeholder="Enter new printer name",
            min_length=1,
            max_length=30
        )
        self.field_ip = discord.ui.TextInput(
            label="Printer IP",
            style=discord.TextStyle.short,
            default=printer_credentials["ip"],
            placeholder="Enter new IP address",
        )
        self.field_access_code = discord.ui.TextInput(
            label="Printer Access Code",
            style=discord.TextStyle.short,
            default=printer_credentials["access_code"],
            placeholder="Enter new access code"
        )
        self.field_serial = discord.ui.TextInput(
            label="Printer Serial",
            style=discord.TextStyle.short,
            default=printer_credentials["serial"],
            placeholder="Enter new serial number"
        )

        self.add_item(self.field_name)
        self.add_item(self.field_ip)
        self.add_item(self.field_access_code)
        self.add_item(self.field_serial)

    def normalize_raw_data(self):
        """Normalize and lowercase printer name; strip whitespace from all text input values."""
        strip_printer_name = (self.field_name.value or "").strip()
        self.new_printer_name = strip_printer_name.lower()

    def name_duplicate_check(self) -> bool:
        """Check for duplicates (case-insensitive) unless it's the same printer"""
        if self.new_printer_name == self.printer_name_original:
            return True

        existing_names = (name.lower() for name in self.printer_utils_cog.connected_printers.keys())
        if self.new_printer_name in existing_names:
            return False

        return True
    # pylint: disable=arguments-differ
    async def on_submit(self, interaction: discord.Interaction):
        """
        Handle the modal submission event.

        Attempts to update the printer credentials with the new data entered by the user.
        If the connection to the printer fails, informs the user of the failure.
        Otherwise, updates the stored printer data and confirms success.
        """

        await interaction.response.defer(ephemeral=True)

        self.normalize_raw_data()
        if not re.match(r'^[\w\s-]+$', self.new_printer_name):
            await interaction.followup.send(
            "❌ Printer name contains invalid characters."
            "Only letters, numbers, spaces, underscores, and hyphens are allowed.",
            ephemeral=True
            )
            return
        if self.name_duplicate_check() is False:
            await interaction.followup.send(
                "❌ Printer name already exists."
                "Please submit the edit again with a different name.",
                ephemeral=True
            )
            return
        try:
            new_printer_credentials = PrinterCredentials(
                self.field_ip.value.strip(),
                self.field_access_code.value.strip(),
                self.field_serial.value.strip()
            )

            if await connect_new_printer(
                printer_name=self.new_printer_name,
                printer_data=new_printer_credentials) is None:
                await interaction.followup.send(
                    f"❌ Can't connect to the printer: {self.new_printer_name.strip()}, "
                    "please check credentials",
                    ephemeral=True
                )
                return

            delete_printer(
                printer_name=self.printer_name_original,
                printer_utils_cog=self.printer_utils_cog
            )

            connected_printers = self.printer_utils_cog.storage.load()
            connected_printers[self.new_printer_name.strip()] = asdict(new_printer_credentials)
            self.printer_utils_cog.storage.save(connected_printers)
            self.printer_utils_cog.connected_printers = connected_printers

            await interaction.followup.send(
                f'✅ Successfully edited printer credentials: {self.new_printer_name.strip()}!',
                ephemeral=True
            )

        except Exception as error: # pylint: disable=broad-exception-caught
            await interaction.followup.send('Oops! Something went wrong.', ephemeral=True)
            traceback.print_exception(type(error), error, error.__traceback__)

    # pylint: disable=arguments-differ
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """
        Handle any errors raised during modal submission.

        Sends an ephemeral message informing the user of the error and logs the traceback.

        Args:
            interaction (discord.Interaction): The interaction during which the error occurred.
            error (Exception): The exception that was raised.
        """
        try:
            await interaction.followup.send('Oops! Something went wrong.', ephemeral=True)
        except Exception as e: # pylint: disable=broad-exception-caught
            print("Failed to send followup message:", e)
        # Log error
        traceback.print_exception(type(error), error, error.__traceback__)
