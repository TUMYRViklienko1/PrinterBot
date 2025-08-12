"""tests for the module printer_helpers"""


import pytest
from unittest.mock import AsyncMock, MagicMock

from cogs.printer_info import PrinterInfo
from cogs.printer_utils import PrinterUtils
@pytest.fixture(name="connected_printers")
def sample_printer_data() -> PrinterUtils:
    """
    Provides a sample dictionary representing printer data
    for use in tests.
    """
    test_printer_controller = PrinterUtils()

    # Example printer data
    test_printer_controller.connected_printers = {
        "printer_1": {
            "ip": "192.168.1.10",
            "access_code": "ABC123",
            "serial": "SN0001"
        },
        "printer_2": {
            "ip": "192.168.1.11",
            "access_code": "XYZ789",
            "serial": "SN0002"
        }
    }

    return test_printer_controller

@pytest.fixture(name="ctx_mock")
def mock_ctx():
    """
    Mock ctx
    """
    ctx = MagicMock()

    # Async method mock
    ctx.send = AsyncMock()

    return ctx

def test_delete_printer_data(ctx_mock, connected_printers):
    """
    Test delete_printer_callback ...
    """
    pass
