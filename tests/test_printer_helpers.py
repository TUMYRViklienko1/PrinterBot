"""tests for the module printer_helpers"""


import pytest
from cogs.utils.printer_helpers import get_printer_data_dict
from cogs.utils.models import PrinterCredentials

@pytest.fixture(name="sample_data")
def sample_printer_data():
    """
    Provides a sample dictionary representing printer data
    for use in tests.
    """
    return {
        "ip": "1.1.1.1",
        "access_code": "12345",
        "serial": "AD12345"
    }

def test_get_printer_data_dict(sample_data):
    """
    Test that `get_printer_data_dict` correctly converts a dictionary
    of printer data into a PrinterCredentials instance, preserving
    all fields accurately.
    """
    result = get_printer_data_dict(sample_data)

    assert isinstance(result, PrinterCredentials)
    assert result.ip == "1.1.1.1"
    assert result.access_code == "12345"
    assert result.serial == "AD12345"
