"""BME690 Temperature, Pressure, Humidity & Gas Sensor."""
import math
import time

from . import constants
from .constants import BME690Data

__version__ = '1.0.0'


# Export constants to global namespace
# so end-users can "from BME690 import NAME"
if hasattr(constants, '__dict__'):
    for key in constants.__dict__:
        value = constants.__dict__[key]
        if key not in globals():
            globals()[key] = value


class BME690(BME690Data):
    """BOSCH BME690.

    Gas, pressure, temperature and humidity sensor.

    :param i2c_addr: One of I2C_ADDR_PRIMARY (0x76) or I2C_ADDR_SECONDARY (0x77)
    :param i2c_device: Optional smbus or compatible instance for facilitating i2c communications.

    """

    def __init__(self, i2c_addr=constants.I2C_ADDR_PRIMARY, i2c_device=None):
        """Initialise BME690 sensor instance and verify device presence.

        :param i2c_addr: i2c address of BME690
        :param i2c_device: Optional SMBus-compatible instance for i2c transport

        """
        BME690Data.__init__(self)

        self.i2c_addr = i2c_addr
        self._i2c = i2c_device
        if self._i2c is None:
            import smbus2
            self._i2c = smbus2.SMBus(1)

        try:
            self.chip_id = self._get_regs(constants.CHIP_ID_ADDR, 1)
            if self.chip_id != constants.CHIP_ID:
                raise RuntimeError('BME690 Not Found. Invalid CHIP ID: 0x{0:02x}'.format(self.chip_id))
        except IOError:
            raise RuntimeError("Unable to identify BME690 at 0x{:02x} (IOError)".format(self.i2c_addr))

        self._variant = self._get_regs(constants.CHIP_VARIANT_ADDR, 1)

        self.soft_reset()
        self.set_power_mode(constants.SLEEP_MODE)
        self._get_calibration_data()

        self.set_humidity_oversample(constants.OS_2X)
        self.set_pressure_oversample(constants.OS_4X)
        self.set_temperature_oversample(constants.OS_8X)
        self.set_filter(constants.FILTER_SIZE_3)
        self.set_gas_status(constants.ENABLE_GAS_MEAS)
        self.set_temp_offset(0)
        self.get_sensor_data()

    def _get_calibration_data(self):
        """Retrieve the sensor calibration data and store it in .calibration_data."""
        calibration = self._get_regs(constants.COEFF_ADDR1, constants.COEFF_ADDR1_LEN)
        calibration += self._get_regs(constants.COEFF_ADDR2, constants.COEFF_ADDR2_LEN)

        heat_range = self._get_regs(constants.ADDR_RES_HEAT_RANGE_ADDR, 1)
        heat_value = constants.twos_comp(self._get_regs(constants.ADDR_RES_HEAT_VAL_ADDR, 1), bits=8)
        sw_error = constants.twos_comp(self._get_regs(constants.ADDR_RANGE_SW_ERR_ADDR, 1), bits=8)

        self.calibration_data.set_from_array(calibration)
        self.calibration_data.set_other(heat_range, heat_value, sw_error)

    def soft_reset(self):
        """Trigger a soft reset."""
        self._set_regs(constants.SOFT_RESET_ADDR, constants.SOFT_RESET_CMD)
        time.sleep(constants.RESET_PERIOD / 1000.0)

    def set_temp_offset(self, value):
        """Set temperature offset in celsius.

        If set, the temperature t_fine will be increased by given value in celsius.
        :param value: Temperature offset in Celsius, eg. 4, -8, 1.25

        """
        if value == 0:
            self.offset_temp_in_t_fine = 0
        else:
            # T_C = (T_FINE * 25) // 16384 / 100
            self.offset_temp_in_t_fine = int(math.copysign(((int(abs(value) * 100)) << 14) / 25, value))

    def set_humidity_oversample(self, value):
        """Set humidity oversampling.

        A higher oversampling value means more stable sensor readings,
        with less noise and jitter.

        However each step of oversampling adds about 2ms to the latency,
        causing a slower response time to fast transients.

        :param value: Oversampling value, one of: OS_NONE, OS_1X, OS_2X, OS_4X, OS_8X, OS_16X

        """
        self.tph_settings.os_hum = value
        self._set_bits(constants.CONF_OS_H_ADDR, constants.OSH_MSK, constants.OSH_POS, value)

    def get_humidity_oversample(self):
        """Get humidity oversampling."""
        return (self._get_regs(constants.CONF_OS_H_ADDR, 1) & constants.OSH_MSK) >> constants.OSH_POS

    def set_pressure_oversample(self, value):
        """Set temperature oversampling.

        A higher oversampling value means more stable sensor readings,
        with less noise and jitter.

        However each step of oversampling adds about 2ms to the latency,
        causing a slower response time to fast transients.

        :param value: Oversampling value, one of: OS_NONE, OS_1X, OS_2X, OS_4X, OS_8X, OS_16X

        """
        self.tph_settings.os_pres = value
        self._set_bits(constants.CONF_T_P_MODE_ADDR, constants.OSP_MSK, constants.OSP_POS, value)

    def get_pressure_oversample(self):
        """Get pressure oversampling."""
        return (self._get_regs(constants.CONF_T_P_MODE_ADDR, 1) & constants.OSP_MSK) >> constants.OSP_POS

    def set_temperature_oversample(self, value):
        """Set pressure oversampling.

        A higher oversampling value means more stable sensor readings,
        with less noise and jitter.

        However each step of oversampling adds about 2ms to the latency,
        causing a slower response time to fast transients.

        :param value: Oversampling value, one of: OS_NONE, OS_1X, OS_2X, OS_4X, OS_8X, OS_16X

        """
        self.tph_settings.os_temp = value
        self._set_bits(constants.CONF_T_P_MODE_ADDR, constants.OST_MSK, constants.OST_POS, value)

    def get_temperature_oversample(self):
        """Get temperature oversampling."""
        return (self._get_regs(constants.CONF_T_P_MODE_ADDR, 1) & constants.OST_MSK) >> constants.OST_POS

    def set_filter(self, value):
        """Set IIR filter size.

        Optionally remove short term fluctuations from the temperature and pressure readings,
        increasing their resolution but reducing their bandwidth.

        Enabling the IIR filter does not slow down the time a reading takes, but will slow
        down the BME690s response to changes in temperature and pressure.

        When the IIR filter is enabled, the temperature and pressure resolution is effectively 20bit.
        When it is disabled, it is 16bit + oversampling-1 bits.

        """
        self.tph_settings.filter = value
        self._set_bits(constants.CONF_ODR_FILT_ADDR, constants.FILTER_MSK, constants.FILTER_POS, value)

    def get_filter(self):
        """Get filter size."""
        return (self._get_regs(constants.CONF_ODR_FILT_ADDR, 1) & constants.FILTER_MSK) >> constants.FILTER_POS

    def select_gas_heater_profile(self, value):
        """Set current gas sensor conversion profile.

        Select one of the 10 configured heating durations/set points.

        :param value: Profile index from 0 to 9

        """
        if value > constants.NBCONV_MAX or value < constants.NBCONV_MIN:
            raise ValueError("Profile '{}' should be between {} and {}".format(value, constants.NBCONV_MIN, constants.NBCONV_MAX))

        self.gas_settings.nb_conv = value
        self._set_bits(constants.CONF_ODR_RUN_GAS_NBC_ADDR, constants.NBCONV_MSK, constants.NBCONV_POS, value)

    def get_gas_heater_profile(self):
        """Get gas sensor conversion profile: 0 to 9."""
        return self._get_regs(constants.CONF_ODR_RUN_GAS_NBC_ADDR, 1) & constants.NBCONV_MSK

    def set_gas_heater_status(self, value):
        """Enable/disable gas heater."""
        self.gas_settings.heater = value
        self._set_bits(constants.CONF_HEAT_CTRL_ADDR, constants.HCTRL_MSK, constants.HCTRL_POS, value)

    def get_gas_heater_status(self):
        """Get current heater status."""
        return (self._get_regs(constants.CONF_HEAT_CTRL_ADDR, 1) & constants.HCTRL_MSK) >> constants.HCTRL_POS

    def set_gas_status(self, value):
        """Enable/disable gas sensor."""
        if value == 1:
                value = constants.ENABLE_GAS_MEAS
        self.gas_settings.run_gas = value
        self._set_bits(constants.CONF_ODR_RUN_GAS_NBC_ADDR, constants.RUN_GAS_MSK, constants.RUN_GAS_POS, value)

    def get_gas_status(self):
        """Get the current gas status."""
        return (self._get_regs(constants.CONF_ODR_RUN_GAS_NBC_ADDR, 1) & constants.RUN_GAS_MSK) >> constants.RUN_GAS_POS

    def set_gas_heater_profile(self, temperature, duration, nb_profile=0):
        """Set temperature and duration of gas sensor heater.

        :param temperature: Target temperature in degrees celsius, between 200 and 400
        :param durarion: Target duration in milliseconds, between 1 and 4032
        :param nb_profile: Target profile, between 0 and 9

        """
        self.set_gas_heater_temperature(temperature, nb_profile=nb_profile)
        self.set_gas_heater_duration(duration, nb_profile=nb_profile)

    def set_gas_heater_temperature(self, value, nb_profile=0):
        """Set gas sensor heater temperature.

        :param value: Target temperature in degrees celsius, between 200 and 400

        When setting an nb_profile other than 0,
        make sure to select it with select_gas_heater_profile.

        """
        if nb_profile > constants.NBCONV_MAX or value < constants.NBCONV_MIN:
            raise ValueError('Profile "{}" should be between {} and {}'.format(nb_profile, constants.NBCONV_MIN, constants.NBCONV_MAX))

        self.gas_settings.heatr_temp = value
        temp = int(self._calc_heater_resistance(self.gas_settings.heatr_temp))
        self._set_regs(constants.RES_HEAT0_ADDR + nb_profile, temp)

    def set_gas_heater_duration(self, value, nb_profile=0):
        """Set gas sensor heater duration.

        Heating durations between 1 ms and 4032 ms can be configured.
        Approximately 20-30 ms are necessary for the heater to reach the intended target temperature.

        :param value: Heating duration in milliseconds.

        When setting an nb_profile other than 0,
        make sure to select it with select_gas_heater_profile.

        """
        if nb_profile > constants.NBCONV_MAX or value < constants.NBCONV_MIN:
            raise ValueError('Profile "{}" should be between {} and {}'.format(nb_profile, constants.NBCONV_MIN, constants.NBCONV_MAX))

        self.gas_settings.heatr_dur = value
        temp = self._calc_heater_duration(self.gas_settings.heatr_dur)
        self._set_regs(constants.GAS_WAIT0_ADDR + nb_profile, temp)

    def set_power_mode(self, value, blocking=True):
        """Set power mode."""
        if value not in (constants.SLEEP_MODE, constants.FORCED_MODE):
            raise ValueError('Power mode should be one of SLEEP_MODE or FORCED_MODE')

        self.power_mode = value

        self._set_bits(constants.CONF_T_P_MODE_ADDR, constants.MODE_MSK, constants.MODE_POS, value)

        while blocking and self.get_power_mode() != self.power_mode:
            time.sleep(constants.POLL_PERIOD_MS / 1000.0)

    def get_power_mode(self):
        """Get power mode."""
        self.power_mode = self._get_regs(constants.CONF_T_P_MODE_ADDR, 1)
        return self.power_mode

    def get_sensor_data(self):
        """Get sensor data.

        Stores data in .data and returns True upon success.

        """
        self.set_power_mode(constants.FORCED_MODE)

        for attempt in range(10):
            status = self._get_regs(constants.FIELD0_ADDR, 1)

            if (status & constants.NEW_DATA_MSK) == 0:
                time.sleep(constants.POLL_PERIOD_MS / 1000.0)
                continue

            regs = self._get_regs(constants.FIELD0_ADDR, constants.FIELD_LENGTH)

            self.data.status = regs[0] & constants.NEW_DATA_MSK
            # Contains the nb_profile used to obtain the current measurement
            self.data.gas_index = regs[0] & constants.GAS_INDEX_MSK
            self.data.meas_index = regs[1]

            adc_pres = (regs[2] << 16) | (regs[3] << 8) | (regs[4])
            adc_temp = (regs[5] << 16) | (regs[6] << 8) | (regs[7])
            adc_hum = (regs[8] << 8) | regs[9]
            adc_gas_res = (regs[15] << 2) | (regs[16] >> 6)
            gas_range = regs[16] & constants.GAS_RANGE_MSK

            self.data.status |= regs[16] & constants.GASM_VALID_MSK
            self.data.status |= regs[16] & constants.HEAT_STAB_MSK

            self.data.heat_stable = (self.data.status & constants.HEAT_STAB_MSK) > 0

            temperature = self._calc_temperature(adc_temp)
            self.data.temperature = temperature / 100.0
            self.data.pressure = self._calc_pressure(adc_pres) / 100.0
            self.data.humidity = self._calc_humidity(adc_hum) / 1000.0

            self.data.gas_resistance = self._calc_gas_resistance(adc_gas_res, gas_range)

            return True

        return False

    def _set_bits(self, register, mask, position, value):
        """Mask out and set one or more bits in a register."""
        temp = self._get_regs(register, 1)
        temp &= ~mask
        temp |= value << position
        self._set_regs(register, temp)

    def _set_regs(self, register, value):
        """Set one or more registers."""
        if isinstance(value, int):
            self._i2c.write_byte_data(self.i2c_addr, register, value)
        else:
            self._i2c.write_i2c_block_data(self.i2c_addr, register, value)

    def _get_regs(self, register, length):
        """Get one or more registers."""
        if length == 1:
            return self._i2c.read_byte_data(self.i2c_addr, register)
        else:
            return self._i2c.read_i2c_block_data(self.i2c_addr, register, length)

    def _calc_temperature(self, temperature_adc):

        part1 = temperature_adc - (256 * self.calibration_data.par_t1)
        part2 = part1 * self.calibration_data.par_t2
        part3 = part1 * part1
        part4 = part3 * self.calibration_data.par_t3
        part5 = (part2 * 262144) + part4
        part6 = part5 // 4294967296

        tem_comp = ((part6 + self.offset_temp_in_t_fine) * 25) // 16384
        self.calibration_data.t_fine = part6 + self.offset_temp_in_t_fine

        return tem_comp

    @property
    def ambient_temperature(self):
        return (self.calibration_data.t_fine * 25) // 16384

    def _calc_pressure(self, pressure_adc):

        part1 = self.calibration_data.t_fine * self.calibration_data.t_fine
        part2 = part1 // 64
        part3 = part2 * self.calibration_data.t_fine // 256
        part4 = self.calibration_data.par_p4 * part3 // 32
        part5 = self.calibration_data.par_p3 * part1 * 16
        part6 = self.calibration_data.par_p2 * self.calibration_data.t_fine * (1 << 22)

        offset = self.calibration_data.par_p1 * (1 << 47) + part4 + part5 + part6
        part2 = (self.calibration_data.par_p8 * part3) // (1 << 5)
        part4 = self.calibration_data.par_p7 * part1 * (1 << 2)

        part5 =(self.calibration_data.par_p6 - 16384) * self.calibration_data.t_fine * (1 << 21)
        sensitivity = (self.calibration_data.par_p5 - 16384) * (1 << 46) + part2 + part4 + part5
        part1 = sensitivity // (1 << 24) * pressure_adc

        part2 = self.calibration_data.par_p10 * self.calibration_data.t_fine
        part3 = part2 + self.calibration_data.par_p9 * (1 << 16)
        part4 = part3 * pressure_adc // (1 << 13)
        part5 = (pressure_adc * part4 // 10) // (1 << 9)
        part5 = part5 * 10
        part6 = pressure_adc * pressure_adc

        part2 = self.calibration_data.par_p11 * part6 // (1 << 16)
        part3 = part2 * pressure_adc // (1 << 7)
        part4 = offset // 4 + part1 + part5 + part3

        press_comp = (part4 // (1 << 40)) * 25

        return press_comp // 100

    def _calc_humidity(self, humidity_adc):
        t_comp = self.ambient_temperature
        t_fine = (t_comp * 256 - 128) // 5
        var_h = t_fine - 76800

        var_h = (((((humidity_adc * 16384) - (self.calibration_data.par_h1 * 1048576) - (self.calibration_data.par_h2 * var_h)) + 16384) // 32768) * ((((((var_h * self.calibration_data.par_h4) // 1024) * ((var_h * self.calibration_data.par_h1) / 2048 + 32768)) // 1024) + 2097152) * self.calibration_data.par_h5 + 8192) // 16384)
        var_h = var_h - (((((var_h // 32768) * (var_h / 32768)) // 128) * self.calibration_data.par_h6) // 16)
        hum_comp = var_h // 4096

        return hum_comp

    def _calc_gas_resistance(self, gas_res_adc, gas_range):
        """Convert the raw gas resistance using calibration data."""
        var1 = 262144 >> gas_range
        var2 = gas_res_adc - 512

        var2 *= 3
        var2 = 4096 + var2

        calc_gas_res = (10000 * var1) // var2
        calc_gas_res = calc_gas_res * 100

        return calc_gas_res

    def _calc_heater_resistance(self, temperature):
        """Convert raw heater resistance using calibration data."""
        temperature = min(max(temperature, 200), 400)

        var1 = ((self.ambient_temperature * self.calibration_data.par_gh3) / 1000) * 256
        var2 = (self.calibration_data.par_gh1 + 784) * (((((self.calibration_data.par_gh2 + 154009) * temperature * 5) / 100) + 3276800) / 10)
        var3 = var1 + (var2 / 2)
        var4 = (var3 / (self.calibration_data.res_heat_range + 4))
        var5 = (131 * self.calibration_data.res_heat_val) + 65536
        heatr_res_x100 = (((var4 / var5) - 250) * 34)
        heatr_res = ((heatr_res_x100 + 50) / 100)

        return heatr_res

    def _calc_heater_duration(self, duration):
        """Calculate correct value for heater duration setting from milliseconds."""
        if duration < 0xfc0:
            factor = 0

            while duration > 0x3f:
                duration /= 4
                factor += 1

            return int(duration + (factor * 64))

        return 0xff
