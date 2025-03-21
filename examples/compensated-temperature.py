#!/usr/bin/env python

import time
from subprocess import PIPE, Popen

import bme690

print("""compensated-temperature.py - Use the CPU temperature to compensate temperature
readings from the BME690 sensor. Method adapted from Initial State's Enviro pHAT
review: https://medium.com/@InitialState/tutorial-review-enviro-phat-for-raspberry-pi-4cd6d8c63441

Press Ctrl+C to exit!

""")

try:
    sensor = bme690.BME690(bme690.I2C_ADDR_PRIMARY)
except (RuntimeError, IOError):
    sensor = bme690.BME690(bme690.I2C_ADDR_SECONDARY)

# These oversampling settings can be tweaked to
# change the balance between accuracy and noise in
# the data.

sensor.set_humidity_oversample(bme690.OS_2X)
sensor.set_pressure_oversample(bme690.OS_4X)
sensor.set_temperature_oversample(bme690.OS_8X)
sensor.set_filter(bme690.FILTER_SIZE_3)


# Gets the CPU temperature in degrees C
def get_cpu_temperature():
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
    output, _error = process.communicate()
    return float(output[output.index(b'=') + 1:output.rindex(b"'")])


factor = 1.0  # Smaller numbers adjust temp down, vice versa
smooth_size = 10  # Dampens jitter due to rapid CPU temp changes

cpu_temps = []

while True:
    if sensor.get_sensor_data():
        cpu_temp = get_cpu_temperature()
        cpu_temps.append(cpu_temp)

        if len(cpu_temps) > smooth_size:
            cpu_temps = cpu_temps[1:]

        smoothed_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
        raw_temp = sensor.data.temperature
        comp_temp = raw_temp - ((smoothed_cpu_temp - raw_temp) / factor)

        print("Compensated temperature: {:05.2f} *C".format(comp_temp))

        time.sleep(1.0)
