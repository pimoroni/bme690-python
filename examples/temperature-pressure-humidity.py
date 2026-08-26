#!/usr/bin/env python

import bme690

print("""temperature-pressure-humidity.py - Displays temperature, pressure, and humidity.

If you don't need gas readings, then you can read temperature,
pressure and humidity quickly.

Press Ctrl+C to exit

""")

try:
    sensor = bme690.BME690(bme690.I2C_ADDR_PRIMARY)
except (OSError, RuntimeError):
    sensor = bme690.BME690(bme690.I2C_ADDR_SECONDARY)

# These oversampling settings can be tweaked to
# change the balance between accuracy and noise in
# the data.

sensor.set_humidity_oversample(bme690.OS_2X)
sensor.set_pressure_oversample(bme690.OS_4X)
sensor.set_temperature_oversample(bme690.OS_8X)
sensor.set_filter(bme690.FILTER_SIZE_3)

print('Polling:')
try:
    while True:
        if sensor.get_sensor_data():
            output = f'{sensor.data.temperature:.2f} C,{sensor.data.pressure:.2f} hPa,{sensor.data.humidity:.3f} %RH'
            print(output)

except KeyboardInterrupt:
    pass
