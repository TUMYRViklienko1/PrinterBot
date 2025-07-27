"""Data models and utilities for printer and image credentials."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, TypedDict
import json
import discord


@dataclass(init=True, repr=False, eq=False)
class PrinterCredentials:
    """Represents credentials and connection information for a printer."""
    ip: str
    access_code: str
    serial: str


class PrinterDataDict(TypedDict):
    """Typed dictionary for representing printer data in a structured form."""
    ip: str
    access_code: str
    serial: str


@dataclass
class ImageCredentials:
    """Holds image-related metadata and constructs Discord file references."""
    image_filename: str = "camera_frame_.png"
    delete_image_flag: bool = False

    def __post_init__(self):
        self.image_main_location = discord.File(
            f"img/{self.image_filename}", filename=self.image_filename
        )
        self.embed_set_image_url = f"attachment://{self.image_filename}"


class PrinterStorage:
    """Handles loading and saving printer data to a JSON file."""

    def __init__(self, file_path: str = "data/printer.json"):
        """Initialize storage with given file path."""
        self.path = Path(file_path)

    def load(self) -> Dict:
        """Load printer data from the JSON file."""
        if not self.path.exists():
            return {}
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: Dict):
        """Save printer data to the JSON file."""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
