# cogs/utils/models.py

from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import json
import discord
from typing import TypedDict

@dataclass(init=True,repr=False,eq=False)
class PrinterCredentials:
    ip: str
    access_code: str
    serial: str

class PrinterDataDict(TypedDict):
    ip: str
    access_code: str
    serial: str

@dataclass
class ImageCredentials:
    image_filename: str = "camera_frame_.png"
    delete_image_flag: bool = False

    def __post_init__(self):
        self.image_main_location = discord.File(f"img/{self.image_filename}", filename=self.image_filename)
        self.embed_set_image_url = f"attachment://{self.image_filename}"

class PrinterStorage:
    def __init__(self, file_path: str = "data/printer.json"):
        self.path = Path(file_path)

    def load(self) -> Dict:
        if not self.path.exists():
            return {}
        with open(self.path) as f:
            return json.load(f)

    def save(self, data: Dict):
        with open(self.path, "w") as f:
            json.dump(data, f, indent=4)

    

