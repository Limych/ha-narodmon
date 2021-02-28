#
#  Copyright (c) 2021, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
#
"""
The NarodMon.ru Cloud Integration Component.

For more details about this sensor, please refer to the documentation at
https://github.com/Limych/ha-narodmon/
"""
from datetime import timedelta

from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    ATTR_ID,
    ATTR_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    DEGREE,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_PRESSURE,
    LIGHT_LUX,
    TEMP_CELSIUS,
)

# Base component constants
NAME = "Narodmon.ru Cloud Integration"
DOMAIN = "narodmon"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.0+dev"
ATTRIBUTION = "Data provided by http://narodmon.ru/"
ISSUE_URL = "https://github.com/Limych/ha-narodmon/issues"

# Configuration and options
CONF_APIKEY = "apikey"

# Defaults
DEFAULT_SCAN_INTERVAL = timedelta(minutes=3)
DEFAULT_VERIFY_SSL = True
DEFAULT_TIMEOUT = 10  # seconds

# Attributes
ATTR_DISTANCE = "distance"
ATTR_DEVICE_NAME = "device_name"
ATTR_SENSOR_NAME = "sensor_name"


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have ANY issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""


SENSOR_TYPES = {
    "temperature": {
        ATTR_ID: 1,
        ATTR_NAME: "Temperature",
        ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_HUMIDITY,
        ATTR_ICON: None,
    },
    "humidity": {
        ATTR_ID: 2,
        ATTR_NAME: "Humidity",
        # ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_HUMIDITY,
        ATTR_ICON: None,
    },
    "pressure": {
        ATTR_ID: 3,
        ATTR_NAME: "Pressure",
        # ATTR_UNIT_OF_MEASUREMENT: PRESSURE_HPA,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_PRESSURE,
        ATTR_ICON: None,
    },
    "wind_speed": {
        ATTR_ID: 4,
        ATTR_NAME: "Wind speed",
        # ATTR_UNIT_OF_MEASUREMENT: ,
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-windy",
    },
    "wind_bearing": {
        ATTR_ID: 5,
        ATTR_NAME: "Wind bearing",
        ATTR_UNIT_OF_MEASUREMENT: DEGREE,
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-windy",
    },
    "precipitation": {
        ATTR_ID: 9,
        ATTR_NAME: "Precipitation",
        # ATTR_UNIT_OF_MEASUREMENT: ,
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-pouring",
    },
    "illuminance": {
        ATTR_ID: 11,
        ATTR_NAME: "Illuminance",
        ATTR_UNIT_OF_MEASUREMENT: LIGHT_LUX,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_ILLUMINANCE,
        ATTR_ICON: None,
    },
    "radiation": {
        ATTR_ID: 12,
        ATTR_NAME: "Radiation",
        # ATTR_UNIT_OF_MEASUREMENT: ,
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:radioactive",
    },
    "uv": {
        ATTR_ID: 20,
        ATTR_NAME: "UV radiation",
        # ATTR_UNIT_OF_MEASUREMENT: ,
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:weather-sunny",
    },
    "pm": {
        ATTR_ID: 22,
        ATTR_NAME: "Particulate matter",
        ATTR_UNIT_OF_MEASUREMENT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:air-filter",
    },
}
