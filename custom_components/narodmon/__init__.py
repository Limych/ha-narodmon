#  Copyright (c) 2021-2022, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
"""The NarodMon Cloud Integration Component.

For more details about this sensor, please refer to the documentation at
https://github.com/Limych/ha-narodmon/
"""
import asyncio
from datetime import timedelta
import logging
import os
import re
import time
from typing import Any, Dict, List

import voluptuous as vol

from homeassistant.components.sensor import DOMAIN as SENSOR
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    ATTR_ID,
    CONF_DEVICES,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NARODMON_IDS, NarodmonApiClient
from .const import (
    CONF_APIKEY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    FRESHNESS_TIME,
    SENSOR_TYPES,
    STARTUP_MESSAGE,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


def cv_apikey(value: Any) -> str:
    """Validate and coerce a NarodMon API key value."""
    if isinstance(value, str) and re.match("^[0-9a-z]+$", value, re.IGNORECASE):
        return value
    raise vol.Invalid(f"Invalid API Key {value}")


DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_SENSORS): vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            cv.time_period, lambda value: timedelta(seconds=value.total_seconds())
        ),
    }
)

CONFIG_SCHEMA_ROOT = vol.Schema(
    {
        vol.Optional(CONF_APIKEY): cv_apikey,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [DEVICE_SCHEMA]),
    }
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: CONFIG_SCHEMA_ROOT}, extra=vol.ALLOW_EXTRA)

YAML_DOMAIN = f"_yaml_{DOMAIN}"


async def async_setup(hass: HomeAssistant, config):
    """Set up this integration using YAML."""
    if DOMAIN not in config:
        return True  # pragma: no cover

    hass.data[YAML_DOMAIN] = config[DOMAIN]
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data={}
        )
    )

    # Remove legacy UUID file from the storage dir
    # Todo: Remove this block in version 3.0;   pylint: disable=fixme
    legacy_uuid_fpath = hass.config.path(STORAGE_DIR, DOMAIN + ".uuid")
    if os.path.exists(legacy_uuid_fpath):  # pragma: no cover
        await hass.async_add_executor_job(os.remove, legacy_uuid_fpath)
        _LOGGER.debug("Legacy UUID file removed (%s).", legacy_uuid_fpath)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    if entry.source == SOURCE_IMPORT:
        if YAML_DOMAIN not in hass.data:  # pragma: no cover
            await hass.config_entries.async_remove(entry.entry_id)
            raise ConfigEntryNotReady

        config = hass.data[YAML_DOMAIN]

        apikey = config.get(CONF_APIKEY)
        if apikey is not None:
            _LOGGER.warning(
                "Field '%s' is NOT recommended to use. If you don't have your own "
                "API key with special limits please remove it from your configs.",
                CONF_APIKEY,
            )

        client = NarodmonApiClient(
            hass,
            apikey=apikey,
            verify_ssl=config.get(CONF_VERIFY_SSL),
            timeout=config.get(CONF_TIMEOUT),
        )

        for index, device_config in enumerate(config.get(CONF_DEVICES)):
            latitude = device_config.get(CONF_LATITUDE, hass.config.latitude)
            longitude = device_config.get(CONF_LONGITUDE, hass.config.longitude)
            types = device_config.get(CONF_SENSORS, SENSOR_TYPES.keys())
            scan_interval = device_config.get(CONF_SCAN_INTERVAL)

            coordinator = NarodmonDataUpdateCoordinator(
                hass, client, scan_interval, latitude, longitude, types
            )
            await coordinator.async_refresh()

            if not coordinator.last_update_success:  # pragma: no cover
                raise ConfigEntryNotReady

            hass.data[DOMAIN].setdefault(entry.entry_id, {})
            hass.data[DOMAIN][entry.entry_id][index] = coordinator

        hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, SENSOR))

    else:
        config = entry.data.copy()

    entry.add_update_listener(async_reload_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unloaded = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, SENSOR)]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class NarodmonDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Narodmon Cloud."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: NarodmonApiClient,
        scan_interval: timedelta,
        latitude: float,
        longitude: float,
        types: List[str],
    ) -> None:
        """Initialize."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=scan_interval)

        self.api = client
        self.latitude = latitude
        self.longitude = longitude
        self.types = types
        self.devices: NARODMON_IDS = set()
        self.sensors: NARODMON_IDS = set()

        self._first_run = True

    async def _async_update_data(self):
        """Update data via library."""
        try:
            fresh = int(time.time() - FRESHNESS_TIME)
            sensors = []

            for _ in range(2):
                data = await self.api.async_update_data(no_throttle=self._first_run)

                if data is None:
                    raise UpdateFailed()

                tps: NARODMON_IDS = {SENSOR_TYPES[i].get(ATTR_ID) for i in self.types}
                for sensor in data.values():
                    if sensor["id"] in self.sensors and sensor["time"] >= fresh:
                        sensors.append(sensor)
                        tps.remove(sensor["type"])

                if tps:

                    async def async_nearby_listener(
                        new_sensors: Dict[int, int]
                    ) -> None:  # pragma: no cover
                        self.devices = self.devices.union(new_sensors.values())
                        self.sensors = self.sensors.union(new_sensors.keys())

                    await self.api.async_set_nearby_listener(
                        async_nearby_listener, self.latitude, self.longitude, tps
                    )

                if not self._first_run or self.api.devices:
                    break  # pragma: no cover

            self._first_run = False

            return sensors

        except Exception as exception:  # pylint: disable=broad-except
            raise UpdateFailed() from exception
