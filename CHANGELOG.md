2.0.0
-----

* Enhancement: Repackage to the uv/hatchling method, with PyPI trusted publishing
* Enhancement: Version is derived from the git tag, __version__ from package metadata
* New: data.gas_valid, exposing the sensor's gasm_valid status bit
* Fix: par_p5 read its low byte from the wrong coefficient index
* Fix: par_h1 and par_h5 are 12-bit signed and were not sign-corrected
* Fix: get_power_mode now masks out the oversampling bits
* Fix: set_power_mode's blocking wait had no effect
* Python 3.9 or later, 3.7 and 3.8 support dropped

1.0.0
-----

* Initial release
