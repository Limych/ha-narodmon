#  Copyright (c) 2021-2022, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
"""
The NarodMon Cloud Integration Component.

For more details about this sensor, please refer to the documentation at
https://github.com/Limych/ha-narodmon/
"""
import logging
import time
from typing import Final

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import YAML_DOMAIN
from .const import (
    ATTR_DEVICE_NAME,
    ATTR_DISTANCE,
    ATTR_SENSOR_ID,
    ATTR_SENSOR_NAME,
    ATTRIBUTION,
    DOMAIN,
    FRESHNESS_TIME,
    NAME,
    SENSOR_TYPES,
    VERSION,
)

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_devices):
    """Set up sensor platform."""
    if entry.source == SOURCE_IMPORT:
        config = hass.data[YAML_DOMAIN]
        for index, device_config in enumerate(config.get(CONF_DEVICES)):
            vdev_id = "-".join([entry.entry_id, str(index)])
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
                        vdev_id,
                        entity_name,
                    )
                )
            if sensors:
                async_add_devices(sensors)

    else:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        # async_add_devices([NarodmonSensor(coordinator, entry)])


# pylint: disable=too-many-instance-attributes
class NarodmonSensor(CoordinatorEntity, SensorEntity):
    """Implementation of an NarodMon sensor."""

    def __init__(self, coordinator, sensor_type: str, vdev_id: str, name: str):
        """Class initialization."""
        super().__init__(coordinator)

        self._sensor_type_id = SENSOR_TYPES[sensor_type].get(ATTR_ID)
        self._sensor_id = None

        self._attr_unique_id = f"{vdev_id}-{sensor_type}"
        self._attr_name = name
        self._attr_icon = SENSOR_TYPES[sensor_type].get(ATTR_ICON)
        self._attr_native_value = None
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type].get(
            ATTR_UNIT_OF_MEASUREMENT
        )
        self._attr_device_class = SENSOR_TYPES[sensor_type].get(ATTR_DEVICE_CLASS)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vdev_id)},
            "name": NAME,
            "model": VERSION,
        }

    def _update_state(self):
        """Update entity state."""
        fresh = int(time.time() - FRESHNESS_TIME)
        for sensor in self.coordinator.data:
            if sensor["type"] == self._sensor_type_id and sensor["time"] >= fresh:
                if self._attr_native_value == sensor["value"]:
                    return

                device = sensor["device"]

                self._attr_native_value = sensor["value"]

                if self._sensor_id != int(sensor["id"]):
                    self._sensor_id = int(sensor["id"])
                    self._attr_extra_state_attributes = {
                        ATTR_ATTRIBUTION: ATTRIBUTION,
                    }

                self._attr_extra_state_attributes[ATTR_SENSOR_ID] = "S" + str(
                    self._sensor_id
                )
                self._attr_extra_state_attributes[ATTR_SENSOR_NAME] = sensor["name"]
                self._attr_extra_state_attributes[ATTR_DEVICE_ID] = "D" + str(
                    device["id"]
                )
                self._attr_extra_state_attributes[ATTR_DEVICE_NAME] = device["name"]
                self._attr_extra_state_attributes[ATTR_DISTANCE] = device["distance"]
                if "location" in device:
                    self._attr_extra_state_attributes[ATTR_LOCATION] = device[
                        "location"
                    ]
                if "lat" in device and "lon" in device:
                    self._attr_extra_state_attributes[ATTR_LATITUDE] = device["lat"]
                    self._attr_extra_state_attributes[ATTR_LONGITUDE] = device["lon"]

                _LOGGER.debug(
                    "Set sensor '%s' state to %s %s",
                    self._attr_name,
                    self._attr_native_value,
                    self._attr_native_unit_of_measurement,
                )
                return

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_state()
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        self._update_state()
        return super().native_value

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        fresh = int(time.time() - FRESHNESS_TIME)
        for sensor in self.coordinator.data:
            if sensor["type"] == self._sensor_type_id and sensor["time"] >= fresh:
                return True

        return False
