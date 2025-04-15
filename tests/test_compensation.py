import bme690


def test_calc_temperature(smbus, calibration):
    """Validate temperature calculation against mock calibration data."""
    sensor = bme690.BME690()
    sensor.calibration_data = calibration
    assert sensor._calc_temperature(7000500) == 2669
    assert sensor.calibration_data.t_fine == 1749524


def test_calc_pressure(smbus, calibration):
    """Validate pressure calculation against mock calibration data."""
    sensor = bme690.BME690()
    sensor.calibration_data = calibration
    sensor._calc_temperature(7000500)
    assert sensor._calc_pressure(6794608) == 99693


def test_calc_humidity(smbus, calibration):
    """Validate humidity calculation against mock calibration data."""
    sensor = bme690.BME690()
    sensor.calibration_data = calibration
    sensor._calc_temperature(7000500)
    assert sensor._calc_humidity(24214) == 56192.0


def test_calc_gas_resistance_low(smbus, calibration):
    """Validate gas calculation against mock calibration data."""
    sensor = bme690.BME690()
    sensor.calibration_data = calibration
    sensor._calc_temperature(7000500)
    assert int(sensor._calc_gas_resistance(0, 0)) == 102400000

""" There is no variant 1 for BME690... yet
def test_calc_gas_resistance_high(smbus, calibration):
    # Validate gas calculation against mock calibration data.
    sensor = bme690.BME690()
    sensor.calibration_data = calibration
    sensor._variant = 1
    sensor._calc_temperature(7000500)
    assert int(sensor._calc_gas_resistance(0, 0)) == 102400000
"""

def test_temp_offset(smbus, calibration):
    """Validate temperature calculation with offset against mock calibration data."""
    sensor = bme690.BME690()
    sensor.calibration_data = calibration
    sensor.set_temp_offset(1.99)
    assert sensor._calc_temperature(7000500) == 2669 + 199
    assert sensor.calibration_data.t_fine == 1879940
