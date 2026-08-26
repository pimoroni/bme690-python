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


def test_set_from_array_pressure_indices():
    """Validate 16-bit pressure coefficients against the Bosch BME690 index mapping."""
    coefficients = list(range(bme690.COEFF_ADDR1_LEN + bme690.COEFF_ADDR2_LEN))
    calibration = bme690.CalibrationData()
    calibration.set_from_array(coefficients)

    assert calibration.par_p5 == (coefficients[5] << 8) | coefficients[4]
    assert calibration.par_p1 == (coefficients[11] << 8) | coefficients[10]
    assert calibration.par_p2 == (coefficients[13] << 8) | coefficients[12]
    assert calibration.par_p6 == (coefficients[7] << 8) | coefficients[6]
    assert calibration.par_p9 == (coefficients[19] << 8) | coefficients[18]


def test_set_from_array_humidity_is_12_bit_signed():
    """Validate that par_h1 and par_h5 are sign-corrected as 12-bit values."""
    coefficients = list(range(bme690.COEFF_ADDR1_LEN + bme690.COEFF_ADDR2_LEN))
    calibration = bme690.CalibrationData()

    coefficients[23] = coefficients[24] = coefficients[25] = 0xff
    calibration.set_from_array(coefficients)
    assert calibration.par_h1 == -1
    assert calibration.par_h5 == -1

    coefficients[23] = coefficients[24] = coefficients[25] = 0x00
    calibration.set_from_array(coefficients)
    assert calibration.par_h1 == 0
    assert calibration.par_h5 == 0
