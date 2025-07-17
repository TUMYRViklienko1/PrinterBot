# cogs/utils/models.py

from dataclasses import dataclass

@dataclass(init=True,repr=False,eq=False)
class PrinterCredentials:
    ip: str
    access_code: str
    serial: str
