#  Copyright (c) 2021-2022, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
"""
The NarodMon Cloud Integration Component.

For more details about this sensor, please refer to the documentation at
https://github.com/Limych/ha-narodmon/
"""
import asyncio
import logging
import socket
import time
from datetime import timedelta
from http import HTTPStatus
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Final,
    Generic,
    List,
    Optional,
    Set,
    TypeVar,
    Union,
)

import aiohttp
import async_timeout
from homeassistant.const import __short_version__ as HASS_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.helpers import instance_id, storage
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

from .const import (
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    ISSUE_URL,
    KHASH,
    VERSION,
)

_LOGGER: Final = logging.getLogger(__package__)

T = TypeVar("T")

ENDPOINT_URL: Final = "https://narodmon.com/api"
HEADERS: Final = {
    "User-Agent": f"ha-narodmon/{VERSION} (https://github.com/Limych/ha-narodmon/)",
    "Content-type": "application/json; charset=UTF-8",
}

DATA_VERSION: Final = 1

DATA_LAST_INIT_TS: Final = "last_init"

NARODMON_IDS: Final = Set[int]
NARODMON_NEARBY_LISTENER: Final = Callable[[Dict[int, int]], Awaitable[None]]
NARODMON_SENSORS_LIST: Final = List[Dict[str, Any]]
NARODMON_SENSORS_DICT: Final = Dict[int, Dict[str, Any]]


class ApiError(Exception):
    """Raised when Narodmon API request ended in error."""

    def __init__(self, status: str, errno: Optional[int] = None):
        """Initialize."""
        super().__init__(status)
        self.errno = errno
        self.status = status


class NarodmonApiClient(Generic[T]):
    """Narodmon API client class."""

    def __init__(
        self,
        hass: HomeAssistant,
        apikey: str = None,
        verify_ssl: bool = DEFAULT_VERIFY_SSL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize coordinator."""
        self.hass = hass
        self.sensors: NARODMON_SENSORS_DICT = {}

        self._apikey = apikey or self._khash
        self._session = async_get_clientsession(hass, verify_ssl=verify_ssl)
        self._timeout = timeout
        self._devices: Dict[int, float] = {}
        self._sensors_last_updated = False
        self._nearby_listener: Optional[NARODMON_NEARBY_LISTENER] = None
        self._nearby_latitude: Optional[float] = None
        self._nearby_longitude: Optional[float] = None
        self._nearby_sensor_types: NARODMON_IDS = set()
        self._limit: int = 1

    @property
    def devices(self) -> NARODMON_IDS:
        """Return list of active devices."""
        return set(self._devices.keys())

    @devices.setter
    def devices(self, value: NARODMON_IDS) -> None:
        """Set list of active devices."""
        self._devices = {i: self._devices.get(i, 0) for i in value}

    @property
    def _devices4update(self) -> NARODMON_IDS:
        result = set(
            sorted(self._devices.keys(), key=lambda x: self._devices[x])[: self._limit]
        )
        return result

    async def async_set_nearby_listener(
        self,
        target: NARODMON_NEARBY_LISTENER,
        latitude: float,
        longitude: float,
        sensor_types: NARODMON_IDS,
    ) -> None:
        """Set listener for nearby sensors async search request."""
        _LOGGER.debug(
            "Set new nearby sensors listener: %s @[%f, %f].",
            sensor_types,
            latitude,
            longitude,
        )
        self._nearby_latitude = latitude
        self._nearby_longitude = longitude
        self._nearby_sensor_types = sensor_types

        self._nearby_listener = target

    @property
    def _khash(self) -> str:
        """Calculate khash."""

        def data_hash(data: str, hash_len: int) -> List[int]:
            """Calculate hash of given data."""
            i = 0
            khash = [0] * hash_len

            for char in data:
                khash[i] = (khash[i] + ord(char)) % 256
                i = (i + 1) % hash_len

            return khash

        khash = "".join(
            chr(a ^ ord(b)) for a, b in zip(data_hash(ISSUE_URL, len(KHASH)), KHASH)
        )

        return khash

    @staticmethod
    def _convert2dict(device: Dict[str, Any]) -> NARODMON_SENSORS_DICT:
        """Convert device sensors list to dict and set device ID for each sensor."""
        result = {}
        dev = device.copy()
        sensors = dev["sensors"]
        dev.pop("sensors", None)

        for item in sensors:
            item["device"] = dev
            result[int(item["id"])] = item

        return result

    @Throttle(timedelta(minutes=1))
    async def async_update_data(self) -> NARODMON_SENSORS_DICT:
        """Update data iterator."""
        await self.async_init()

        if self._nearby_listener and (not self.devices or self._sensors_last_updated):
            await self._async_search_nearby_sensors()

        elif self.devices:
            await self._async_update_sensors()

        else:
            _LOGGER.debug("Nothing to update. :-/")

        return self.sensors

    async def async_init(self) -> None:
        """Initialize API."""
        store = storage.Store(self.hass, DATA_VERSION, DOMAIN, True)
        data: Dict[str, Any] = await store.async_load() or {
            DATA_LAST_INIT_TS: 0,
        }

        now_ts = int(time.time())
        if data[DATA_LAST_INIT_TS] > int(now_ts - 86400):
            return

        await self._async_api_wrapper(
            {
                "cmd": "appInit",
                "version": VERSION,
                "platform": HASS_VERSION,
            }
        )

        data[DATA_LAST_INIT_TS] = now_ts

        await store.async_save(data)

    async def _async_search_nearby_sensors(self) -> None:
        """Search for nearby sensors of defined types."""
        now_ts = int(time.time())

        data = await self._async_api_wrapper(
            {
                "cmd": "sensorsNearby",
                "lat": self._nearby_latitude,
                "lon": self._nearby_longitude,
                "types": ",".join([str(i) for i in self._nearby_sensor_types]),
            }
        )
        self._sensors_last_updated = not self._devices
        devices = data.get("devices", {})

        if len(devices) > self._limit:
            self._limit = len(devices)
            _LOGGER.debug("PubsLimit set to %d", self._limit)

        sensors: Dict[int, int] = {}
        for device in sorted(data["devices"], key=lambda x: x["distance"]):
            for sensor in device["sensors"]:
                if sensor["type"] in self._nearby_sensor_types:
                    self._nearby_sensor_types.remove(sensor["type"])
                    sensors[sensor["id"]] = device["id"]
                    if device["id"] not in self._devices:
                        self._devices[int(device["id"])] = now_ts
                        self.sensors.update(self._convert2dict(device))

        _LOGGER.debug("New sensors found: %s", ", ".join([f"S{i}" for i in sensors]))
        if self._nearby_listener:
            await self._nearby_listener(sensors)
        self._nearby_listener = None

    async def _async_update_sensors(self) -> None:
        """Update known sensors."""
        now_ts = int(time.time())

        data = await self._async_api_wrapper(
            {
                "cmd": "sensorsOnDevice",
                "devices": ",".join([str(i) for i in self._devices4update]),
            }
        )
        self._sensors_last_updated = True
        devices = data.get("devices", {})

        if len(devices) > self._limit:
            self._limit = len(devices)
            _LOGGER.debug("PubsLimit set to %d", self._limit)

        for device in devices:
            self._devices[int(device["id"])] = now_ts
            self.sensors.update(self._convert2dict(device))

    async def _async_api_wrapper(
        self, data: Dict[str, Union[str, int, float]]
    ) -> Dict[str, Any]:
        """Get information from the API."""

        data["uuid"] = await instance_id.async_get(self.hass)

        _LOGGER.debug("Request: '%s'", data)

        data["api_key"] = self._apikey
        data["lang"] = "en"

        try:
            async with async_timeout.timeout(self._timeout):
                async with self._session.post(
                    ENDPOINT_URL, headers=HEADERS, json=data
                ) as resp:
                    if resp.status != HTTPStatus.OK:
                        raise ApiError(
                            f"Invalid response from Narodmon API: {resp.status}"
                        )
                    _LOGGER.debug("Response: '%s'", await resp.text())
                    result = await resp.json()

                if "error" in result:
                    raise ApiError(result["error"], errno=result["errno"])

                return result

        except ApiError as exception:
            _LOGGER.error("[%s] %s", exception.errno, exception.status)
            raise exception

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                ENDPOINT_URL,
                exception,
            )
            raise exception

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                ENDPOINT_URL,
                exception,
            )
            raise exception

        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                ENDPOINT_URL,
                exception,
            )
            raise exception

        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
            raise exception
