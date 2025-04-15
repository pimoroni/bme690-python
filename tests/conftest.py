import sys

import mock
import pytest

import bme690
from bme690.constants import CalibrationData


class MockSMBus:
    """Mock a basic non-presence SMBus device to cause BME690 to fail.

    Returns 0 in all cases, so that CHIP_ID will never match.

    """

    def __init__(self, bus):  # noqa D107
        pass

    def read_byte_data(self, addr, register):
        """Return 0 for all read attempts."""
        return 0


class MockSMBusPresent:
    """Mock enough of the BME690 for the library to initialise and test."""

    def __init__(self, bus):
        """Initialise with test data."""
        self.regs = [0 for _ in range(256)]
        self.regs[bme690.CHIP_ID_ADDR] = bme690.CHIP_ID

    def read_byte_data(self, addr, register):
        """Read a single byte from fake registers."""
        return self.regs[register]

    def write_byte_data(self, addr, register, value):
        """Write a single byte to fake registers."""
        self.regs[register] = value

    def read_i2c_block_data(self, addr, register, length):
        """Read up to length bytes from register."""
        return self.regs[register:register + length]


@pytest.fixture(scope='function', autouse=False)
def smbus_notpresent():
    """Mock smbus module."""
    smbus = mock.MagicMock()
    smbus.SMBus = MockSMBus
    sys.modules['smbus2'] = smbus
    yield smbus
    del sys.modules['smbus2']


@pytest.fixture(scope='function', autouse=False)
def smbus():
    """Mock smbus module."""
    smbus = mock.MagicMock()
    smbus.SMBus = MockSMBusPresent
    sys.modules['smbus2'] = smbus
    yield smbus
    del sys.modules['smbus2']


@pytest.fixture(scope='function', autouse=False)
def calibration():
    """Mock bme690 calibration."""
    calibration = CalibrationData()
    # Dump of calibration data borrowed from:
    # https://github.com/pimoroni/bme690-python/issues/11
    data = {
        'par_gh1': -38,
        'par_gh2': -6406,
        'par_gh3': 18,
        'par_h1': 238,
        'par_h2': 50,
        'par_h3': 0,
        'par_h4': 30,
        'par_h5': 399,
        'par_h6': 75,
        'par_p1': 20021,
        'par_p10': 6,
        'par_p11': -11,
        'par_p2': 25517,
        'par_p3': 3,
        'par_p4': -6,
        'par_p5': 5941,
        'par_p6': 4090,
        'par_p7': 6,
        'par_p8': 1,
        'par_p9': 4631,
        'par_t1': 22288,
        'par_t2': 22173,
        'par_t3': -7,
        'range_sw_err': 1,
        'res_heat_range': 1,
        'res_heat_val': 56,
        't_fine': 1627524
    }
    for k, v in data.items():
        setattr(calibration, k, v)
    return calibration
