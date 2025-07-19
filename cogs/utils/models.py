# cogs/utils/models.py

from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import json

@dataclass(init=True,repr=False,eq=False)
class PrinterCredentials:
    ip: str
    access_code: str
    serial: str

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