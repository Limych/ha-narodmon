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
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_DEVICE_CLASS,
    ATTR_DEVICE_ID,
    ATTR_ICON,
    ATTR_ID,
    ATTR_LATITUDE,
    ATTR_LOCATION,
    ATTR_LONGITUDE,
    ATTR_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_DEVICES,
    CONF_NAME,
    CONF_SENSORS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.narodmon import YAML_DOMAIN

from .const import (
    ATTR_DEVICE_NAME,
    ATTR_DISTANCE,
    ATTR_SENSOR_NAME,
    ATTRIBUTION,
    DOMAIN,
    NAME,
    SENSOR_TYPES,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_devices):
    """Set up sensor platform."""
    if entry.source == "import":
        config = hass.data[YAML_DOMAIN]
        for index, device_config in enumerate(config.get(CONF_DEVICES)):
            device_id = "-".join([entry.entry_id, str(index)])
            coordinator = hass.data[DOMAIN][entry.entry_id][index]
            name = device_config.get(CONF_NAME, hass.config.location_name)
            types = device_config.get(CONF_SENSORS, SENSOR_TYPES.keys())

            sensors = []
            for stype in types:
                entity_name = " ".join([name, SENSOR_TYPES[stype][ATTR_NAME]])
                sensors.append(
                    NarodmonSensor(
                        coordinator,
                        stype,
                        device_id,
                        entity_name,
                    )
                )
            if sensors:
                async_add_devices(sensors)

    else:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        # async_add_devices([NarodmonSensor(coordinator, entry)])


# pylint: disable=r0902
class NarodmonSensor(CoordinatorEntity):
    """Implementation of an NarodMon.ru sensor."""

    def __init__(self, coordinator, sensor_type, device_id, name):
        """Class initialization."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._device_id = device_id
        self._name = name
        self._state = None
        self._unit = None
        self._attr = {}

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self._device_id}-{self._sensor_type}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return SENSOR_TYPES[self._sensor_type].get(ATTR_ICON)

    def _update_state(self):
        """Update entity state."""
        for device in sorted(
            self.coordinator.data["devices"], key=lambda x: x["distance"]
        ):
            for sensor in device["sensors"]:
                if sensor["type"] == SENSOR_TYPES[self._sensor_type][ATTR_ID]:
                    self._state = sensor["value"]
                    self._unit = sensor["unit"]
                    self._attr[ATTR_SENSOR_NAME] = sensor["name"]

                    self._attr[ATTR_DEVICE_ID] = "D" + str(device["id"])
                    self._attr[ATTR_DEVICE_NAME] = device["name"]
                    self._attr[ATTR_DISTANCE] = device["distance"]
                    self._attr[ATTR_LOCATION] = device["location"]
                    self._attr[ATTR_LATITUDE] = device["lat"]
                    self._attr[ATTR_LONGITUDE] = device["lon"]
                    return

    @property
    def state(self):
        """Return the state of the sensor."""
        self._update_state()
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity."""
        if ATTR_UNIT_OF_MEASUREMENT in SENSOR_TYPES[self._sensor_type]:
            return SENSOR_TYPES[self._sensor_type].get(ATTR_UNIT_OF_MEASUREMENT)

        self._update_state()
        return self._unit

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return SENSOR_TYPES[self._sensor_type].get(ATTR_DEVICE_CLASS)

    @property
    def device_info(self):
        """Return the device info."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": NAME,
            "model": VERSION,
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        self._update_state()
        attr = self._attr.copy()
        attr[ATTR_ATTRIBUTION] = ATTRIBUTION
        return attr
