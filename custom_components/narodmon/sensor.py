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
import json
import logging
import random
import re
from datetime import timedelta
from typing import Any, Dict, Optional

import httpx
import voluptuous as vol
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.storage import STORAGE_DIR

from .const import (
    CONF_APIKEY,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    ISSUE_URL,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=3)


def cv_apikey(value: Any) -> str:
    """Validate and coerce a NarodMon.ru API key value."""
    if isinstance(value, str) and re.match("^[0-9a-z]+$", value, re.IGNORECASE):
        return value
    raise vol.Invalid(f"Invalid API Key {value}")


def cv_device_id(value: Any) -> int:
    """Validate and coerce a NarodMon.ru Device ID value."""
    if isinstance(value, str) and re.match("^D[0-9]+$", value):
        return int(value[1:])
    raise vol.Invalid(f"Invalid Device ID {value}")


PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Required(CONF_APIKEY): cv_apikey,
            vol.Required(CONF_DEVICE_ID): cv_device_id,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                cv.time_period, lambda value: int(value.total_seconds())
            ),
            vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
            vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        }
    ),
)


# pylint: disable=unused-argument
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up platform."""
    # Print startup message
    _LOGGER.info("Version %s", VERSION)
    _LOGGER.info(
        "If you have ANY issues with this, please report them here: %s", ISSUE_URL
    )

    name = config.get(CONF_NAME)
    apikey = config.get(CONF_APIKEY)
    dev_id = config.get(CONF_DEVICE_ID)
    scan_interval = config.get(CONF_SCAN_INTERVAL)
    verify_ssl = config.get(CONF_VERIFY_SSL)
    timeout = config.get(CONF_TIMEOUT)

    uuid_fpath = hass.config.path(STORAGE_DIR, DOMAIN + ".uuid")
    try:
        with open(uuid_fpath) as file:
            uuid = file.read()
        _LOGGER.debug("NarodMon.ru client UUID: %s", uuid)
    except FileNotFoundError:
        uuid = ("%032x" % random.getrandbits(128)).upper()
        _LOGGER.debug("NarodMon.ru client UUID not found. Created new one: %s", uuid)
        with open(uuid_fpath, "w") as file:
            file.write(uuid)

    _LOGGER.debug("%s (%s)", name, uuid)

    async_add_entities(
        [
            NarodmonSensor(
                hass, name, apikey, uuid, dev_id, scan_interval, verify_ssl, timeout
            )
        ],
        update_before_add=True,
    )


# pylint: disable=r0902
class NarodmonSensor(Entity):
    """Implementation of an NarodMon.ru sensor."""

    # pylint: disable=r0913
    def __init__(
        self,
        hass,
        name: str,
        apikey: str,
        uuid: str,
        dev_id: int,
        scan_interval: int,
        verify_ssl: bool,
        timeout: int,
    ):
        """Initialize the sensor."""
        self._hass = hass
        self._name = name
        self._apikey = apikey
        self._uuid = uuid
        self._dev_id = dev_id
        self._scan_interval = scan_interval
        self._verify_ssl = verify_ssl
        self._timeout = timeout

        self._device_class = None
        self._unit_of_measurement = None
        self._icon = None

        self._async_client = None
        self._data = None
        self._state = None
        self._attributes = None

    @property
    def name(self) -> Optional[str]:
        """Return the name of the sensor."""
        return self._name

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self._device_class

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state."""
        return True

    @property
    def available(self):
        """Return the availability of this sensor."""
        return self._data is not None

    @property
    def state(self):
        """Return the state of the sensor."""
        return "Ok"

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement of this entity."""
        return self._unit_of_measurement

    @property
    def icon(self) -> Optional[str]:
        """Return the icon to use in the frontend."""
        return self._icon

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return the state attributes."""
        return self._attributes

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        _LOGGER.debug("Added")
        self._update()

    async def async_update(self):
        """Get the latest data from cloud and update the state."""
        _LOGGER.debug("Update")
        if not self._async_client:
            self._async_client = get_async_client(
                self._hass, verify_ssl=self._verify_ssl
            )

        url = "https://narodmon.ru/api/sensorsOnDevice?id=%d&uuid=%s&api_key=%s" % (
            self._dev_id,
            self._uuid,
            self._apikey,
        )
        _LOGGER.debug("Updating from %s", url)
        try:
            response = await self._async_client.request(
                "GET",
                url,
                headers={
                    "User-Agent": "Home Assistant Component (%s)" % ISSUE_URL,
                },
                timeout=self._timeout,
            )
            self._data = response.text
        except httpx.RequestError as ex:
            _LOGGER.error("Error fetching data: %s failed with %s", url, ex)
            self._data = None

        _LOGGER.debug(self._data)

        self._update()

    def _update(self):
        """Update state from cloud."""
        try:
            json_dict = json.loads(self._data)
            attrs = {k: json_dict[k] for k in ["location", "sensors"] if k in json_dict}
            self._attributes = attrs
        except ValueError:
            _LOGGER.warning("REST result could not be parsed as JSON")
            _LOGGER.debug("Erroneous JSON: %s", self._data)

        self._state = self._data
