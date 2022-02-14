#  Copyright (c) 2021-2022, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
"""
The NarodMon.ru Cloud Integration Component.

For more details about this sensor, please refer to the documentation at
https://github.com/Limych/ha-narodmon/
"""
import asyncio
import glob
import hashlib
import logging
import os
import socket
import time
from http import HTTPStatus
from typing import Any, Dict, List, Optional

import aiohttp
import async_timeout
from homeassistant.const import ATTR_ID
from homeassistant.const import __short_version__ as HASS_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.helpers import instance_id, storage
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_TIMEOUT, DEFAULT_VERIFY_SSL, DOMAIN, SENSOR_TYPES, VERSION

_LOGGER: logging.Logger = logging.getLogger(__package__)

ENDPOINT_URL = "https://narodmon.ru/api"
HEADERS = {
    "User-Agent": f"ha-narodmon/{VERSION} (https://github.com/Limych/ha-narodmon/)",
    "Content-type": "application/json; charset=UTF-8",
}

DATA_VERSION = 1

DATA_LAST_INIT_TS = "last_init"


def dir_hash(path: str) -> str:
    """Calculate cumulative hash of all Python files in directory."""
    dhash = hashlib.md5()

    for file in glob.iglob(f"{path}/**.py", recursive=True):
        with open(file, "rb") as fp:
            _LOGGER.debug("Hashing file %s", file)
            dhash.update(fp.read())

    _LOGGER.debug("Cumulative hash of all files: %s", dhash.hexdigest())
    return dhash.hexdigest()


cdir = os.path.dirname(f"{__file__}")
with open(f"{cdir}/checksum.bin", "rb") as fpt:
    KHASH = "".join(chr(ord(a) ^ b) for a, b in zip(dir_hash(cdir), fpt.read()))


class ApiError(Exception):
    """Raised when Narodmon.ru API request ended in error."""

    def __init__(self, status: str, errno: Optional[int] = None):
        """Initialize."""
        super().__init__(status)
        self.errno = errno
        self.status = status


class NarodmonApiClient:
    """Narodmon.ru API client class."""

    def __init__(
        self,
        hass: HomeAssistant,
        verify_ssl: bool = DEFAULT_VERIFY_SSL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Narodmon.ru API Client."""
        self.hass = hass

        self._session = async_get_clientsession(hass, verify_ssl=verify_ssl)
        self._timeout = timeout

    async def async_init(self):
        """Initialize API."""
        store = storage.Store(self.hass, DATA_VERSION, DOMAIN, True)
        data: Dict[str, Any] = await store.async_load() or {
            DATA_LAST_INIT_TS: 0,
        }

        now_ts = int(time.time())
        if data[DATA_LAST_INIT_TS] > int(now_ts - 86400):
            return

        await self._api_wrapper(
            {
                "cmd": "appInit",
                "version": VERSION,
                "platform": HASS_VERSION,
            }
        )

        data[DATA_LAST_INIT_TS] = now_ts

        await store.async_save(data)

    # @singleton.singleton(DOMAIN)
    async def async_get_nearby_sensors(
        self, latitude: float, longitude: float, types: List[str]
    ) -> dict:
        """Get list of nearby sensors."""
        await self.async_init()

        return await self._api_wrapper(
            {
                "cmd": "sensorsNearby",
                "lat": latitude,
                "lon": longitude,
                "types": ",".join([str(SENSOR_TYPES[i][ATTR_ID]) for i in types]),
                "limit": 50,
            }
        )

    async def _api_wrapper(self, data: dict) -> dict:
        """Get information from the API."""

        # Add required arguments
        data["api_key"] = KHASH
        data["uuid"] = await instance_id.async_get(self.hass)
        data["lang"] = "en"

        _LOGGER.debug("Request: '%s'", data)
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
