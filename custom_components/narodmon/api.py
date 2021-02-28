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
import asyncio
import logging
import socket
from typing import List, Optional

import aiohttp
import async_timeout
from homeassistant.const import ATTR_ID, HTTP_OK

from .const import SENSOR_TYPES, VERSION

_LOGGER: logging.Logger = logging.getLogger(__package__)

ENDPOINT_URL = "https://narodmon.ru/api"
HEADERS = {
    "User-Agent": f"ha-narodmon/{VERSION} (https://github.com/Limych/ha-narodmon/)",
    "Content-type": "application/json; charset=UTF-8",
}


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
        self, session: aiohttp.ClientSession, uuid: str, apikey: str, timeout: int
    ) -> None:
        """Narodmon.ru API Client."""
        self._session = session
        self._uuid = uuid
        self._apikey = apikey
        self._timeout = timeout

    async def async_get_nearby_sensors(
        self, latitude: float, longitude: float, types: List[str]
    ) -> dict:
        """Get list of nearby sensors."""
        return await self._api_wrapper(
            {
                "cmd": "sensorsNearby",
                "uuid": self._uuid,
                "api_key": self._apikey,
                "lat": latitude,
                "lon": longitude,
                "types": ",".join([str(SENSOR_TYPES[i][ATTR_ID]) for i in types]),
                "limit": 50,
                "lang": "en",
            }
        )

    async def _api_wrapper(self, data: dict) -> dict:
        """Get information from the API."""
        _LOGGER.debug("Request: '%s'", data)
        try:
            async with async_timeout.timeout(
                self._timeout, loop=asyncio.get_event_loop()
            ):
                async with self._session.post(
                    ENDPOINT_URL, headers=HEADERS, json=data
                ) as resp:
                    if resp.status != HTTP_OK:
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
