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

from homeassistant.components.sensor import SensorEntity
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
class NarodmonSensor(CoordinatorEntity, SensorEntity):
    """Implementation of an NarodMon.ru sensor."""

    def __init__(self, coordinator, sensor_type, device_id, name):
        """Class initialization."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._device_attr = {}

        self._attr_unique_id = f"{device_id}-{sensor_type}"
        self._attr_name = name
        self._attr_icon = SENSOR_TYPES[sensor_type].get(ATTR_ICON)
        self._attr_native_value = None
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type].get(
            ATTR_UNIT_OF_MEASUREMENT
        )
        self._attr_device_class = SENSOR_TYPES[sensor_type].get(ATTR_DEVICE_CLASS)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": NAME,
            "model": VERSION,
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attr = self._device_attr.copy()
        attr[ATTR_ATTRIBUTION] = ATTRIBUTION
        return attr

    async def async_update(self):
        """Update entity state."""
        await super().async_update()

        for device in sorted(
            self.coordinator.data["devices"], key=lambda x: x["distance"]
        ):
            for sensor in device["sensors"]:
                if sensor["type"] == SENSOR_TYPES[self._sensor_type][ATTR_ID]:
                    self._attr_state = sensor["value"]
                    self._attr_native_unit_of_measurement = sensor["unit"]
                    self._device_attr[ATTR_SENSOR_NAME] = sensor["name"]

                    self._device_attr[ATTR_DEVICE_ID] = "D" + str(device["id"])
                    self._device_attr[ATTR_DEVICE_NAME] = device["name"]
                    self._device_attr[ATTR_DISTANCE] = device["distance"]
                    self._device_attr[ATTR_LOCATION] = device["location"]
                    self._device_attr[ATTR_LATITUDE] = device["lat"]
                    self._device_attr[ATTR_LONGITUDE] = device["lon"]
                    return
