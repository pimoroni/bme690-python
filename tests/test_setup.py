import pytest

import bme690


def test_setup_not_present(smbus_notpresent):
    """Mock the adbsence of a BME690 and test initialisation."""
    with pytest.raises(RuntimeError):
        sensor = bme690.BME690()  # noqa F841


def test_setup_mock_present(smbus):
    """Mock the presence of a BME690 and test initialisation."""
    sensor = bme690.BME690()  # noqa F841
