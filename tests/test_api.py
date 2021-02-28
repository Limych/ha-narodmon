"""Tests for Narodmon.ru API."""
import asyncio

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest import raises
from pytest_homeassistant_custom_component.common import load_fixture

from custom_components.narodmon.api import ENDPOINT_URL, ApiError, NarodmonApiClient
from custom_components.narodmon.const import DEFAULT_TIMEOUT


async def test_get_nearby_sensors(hass: HomeAssistant, aioclient_mock):
    """Test getting nearby sensors."""

    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(
        async_get_clientsession(hass), "some_uuid", "some_api", DEFAULT_TIMEOUT
    )

    # Use aioclient_mock which is provided by `pytest_homeassistant_custom_component`
    # to mock responses to aiohttp requests. In this case we are telling the mock to
    # return {"test": "test"} when a `POST` call is made to the specified URL. We then
    # call `async_get_data` which will make that request.
    aioclient_mock.post(ENDPOINT_URL, json={"test": "test"})
    assert await api.async_get_nearby_sensors(
        hass.config.latitude, hass.config.longitude, ["humidity"]
    ) == {"test": "test"}


# In order to get 100% coverage, we also want to simulate raising the exceptions
# to ensure that the function handles them as expected.
# The caplog fixture allows access to log messages in tests. This is particularly
# useful during exception handling testing since often the only action as part of
# exception handling is a logging statement
# pylint: disable=protected-access
async def test_api_wrapper(hass: HomeAssistant, aioclient_mock, caplog):
    """Test getting nearby sensors."""

    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(
        async_get_clientsession(hass), "some_uuid", "some_api", DEFAULT_TIMEOUT
    )

    caplog.clear()
    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, status=404)
    with raises(ApiError):
        await api._api_wrapper({})
    assert (
        len(caplog.record_tuples) == 2
        and "[None] Invalid response from Narodmon API: 404"
        in caplog.record_tuples[1][2]
    )

    caplog.clear()
    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, text=load_fixture("error.json"))
    with raises(ApiError):
        await api._api_wrapper({})
    assert (
        len(caplog.record_tuples) == 3
        and "[400] Отсутствует ключ приложения: api_key" in caplog.record_tuples[2][2]
    )

    caplog.clear()
    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, exc=asyncio.TimeoutError)
    with raises(asyncio.TimeoutError):
        await api._api_wrapper({})
    assert (
        len(caplog.record_tuples) == 2
        and "Timeout error fetching information from" in caplog.record_tuples[1][2]
    )

    caplog.clear()
    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, exc=TypeError)
    with raises(TypeError):
        await api._api_wrapper({})
    assert (
        len(caplog.record_tuples) == 2
        and "Error parsing information from" in caplog.record_tuples[1][2]
    )

    caplog.clear()
    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, exc=aiohttp.ClientError)
    with raises(aiohttp.ClientError):
        await api._api_wrapper({})
    assert (
        len(caplog.record_tuples) == 2
        and "Error fetching information from" in caplog.record_tuples[1][2]
    )

    caplog.clear()
    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, exc=Exception)
    with raises(Exception):
        await api._api_wrapper({})
    assert (
        len(caplog.record_tuples) == 2
        and "Something really wrong happened!" in caplog.record_tuples[1][2]
    )
