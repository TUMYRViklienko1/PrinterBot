import pytest
from cogs.utils.printer_helpers import get_printer_data_dict
from cogs.utils.models import PrinterCredentials

@pytest.fixture
def sample_printer_data():
    return {
        "ip": "1.1.1.1",
        "access_code": "12345",
        "serial": "AD12345"
    }

def test_get_printer_data_dict(sample_printer_data):
    result = get_printer_data_dict(sample_printer_data)

    assert isinstance(result, PrinterCredentials)
    assert result.ip == "1.1.1.1"
    assert result.access_code == "12345"
    assert result.serial == "AD12345"