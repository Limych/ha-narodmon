"""Tests for Narodmon API."""

#  Copyright (c) 2025, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)

import asyncio
import time
from http import HTTPStatus
from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
import yaml
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import load_fixture

from custom_components.narodmon.api import (
    DATA_LAST_INIT_TS,
    ENDPOINT_URL,
    NARODMON_IDS,
    NarodmonApiClient,
    NarodmonApiError,
    NarodmonUnauthorizedError,
)
from custom_components.narodmon.const import DEFAULT_TIMEOUT, DEFAULT_VERIFY_SSL

ROOT = Path(f"{__file__}/..").resolve().parent

TEST_DEVICE1_RESULT = {
    "id": 123,
    "some": "data",
    "distance": 34,
    "sensors": [
        {
            "id": "1",
            "type": 2,
        },
        {
            "id": 2,
            "type": 3,
            "some": "another data",
        },
    ],
}
TEST_DEVICE2_RESULT = {
    "id": 234,
    "distance": 45,
    "sensors": [
        {
            "id": "1",
            "type": 4,
        },
        {
            "id": 2,
            "type": 5,
            "some": "data",
        },
    ],
}


@pytest.fixture(name="khash")
def khash_fixture() -> str | None:
    """Return API key."""
    try:
        with Path(f"{ROOT}/secrets.yaml").open(encoding="utf8") as fp:
            return yaml.safe_load(fp).get("api_key")
    except (FileNotFoundError, KeyError):
        return None


# pylint: disable=protected-access
async def test_khash(hass: HomeAssistant, khash):
    """Test calculation khash."""
    if khash is None:
        return

    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(hass, DEFAULT_VERIFY_SSL, DEFAULT_TIMEOUT)

    assert khash == api._khash


# pylint: disable=protected-access
async def test_devices(hass: HomeAssistant):
    """Test devices property."""
    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(hass, DEFAULT_VERIFY_SSL, DEFAULT_TIMEOUT)

    assert api.devices == set()
    assert api._devices4update == set()

    api.devices = [1, 2, 3]
    assert api.devices == {1, 2, 3}
    assert api._devices4update == {1}
    #
    api._limit = 2
    assert api._devices4update == {1, 2}

    api._devices = {1: 3, 2: 2, 3: 1}
    assert api.devices == {1, 2, 3}
    #
    api._limit = 1
    assert api._devices4update == {3}
    #
    api._limit = 2
    assert api._devices4update == {2, 3}


# pylint: disable=protected-access
async def test_async_set_nearby_listener(hass: HomeAssistant):
    """Test setting nearby listener."""
    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(hass, DEFAULT_VERIFY_SSL, DEFAULT_TIMEOUT)

    def mock_listener(data: NARODMON_IDS) -> None:
        """Mock listener."""

    await api.async_set_nearby_listener(
        mock_listener, hass.config.latitude, hass.config.longitude, 10, {1, 2, 3}
    )

    assert api._nearby_latitude == hass.config.latitude
    assert api._nearby_longitude == hass.config.longitude
    assert api._nearby_sensor_types == {1, 2, 3}

    # pylint: disable=comparison-with-callable
    assert api._nearby_listener == mock_listener


async def test_convert2dict(hass: HomeAssistant):
    """Test converting data."""
    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(hass, DEFAULT_VERIFY_SSL, DEFAULT_TIMEOUT)

    dev = TEST_DEVICE1_RESULT.copy()
    expected_device = {
        "id": 123,
        "some": "data",
        "distance": 34,
    }
    expected = {
        1: {
            "id": "1",
            "type": 2,
            "device": expected_device,
        },
        2: {
            "id": 2,
            "type": 3,
            "some": "another data",
            "device": expected_device,
        },
    }

    assert api._convert2dict(TEST_DEVICE1_RESULT) == expected
    assert dev == TEST_DEVICE1_RESULT


# pylint: disable=unexpected-keyword-arg
async def test_async_update_data(hass: HomeAssistant):
    """Test data updater."""
    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(hass, DEFAULT_VERIFY_SSL, DEFAULT_TIMEOUT)

    with (
        patch.object(api, "async_init", new_callable=AsyncMock) as init,
        patch.object(
            api, "_async_search_nearby_sensors", new_callable=AsyncMock
        ) as nearby,
        patch.object(api, "_async_update_sensors", new_callable=AsyncMock) as device,
    ):
        await api.async_update_data(no_throttle=True)
        #
        init.assert_called_once()
        nearby.assert_not_called()
        device.assert_not_called()

        init.reset_mock()
        nearby.reset_mock()
        device.reset_mock()

        api._nearby_listener = 1
        #
        await api.async_update_data(no_throttle=True)
        #
        init.assert_called_once()
        nearby.assert_called_once()
        device.assert_not_called()
        #
        api._nearby_listener = None

        init.reset_mock()
        nearby.reset_mock()
        device.reset_mock()

        api.devices = {123}
        #
        await api.async_update_data(no_throttle=True)
        #
        init.assert_called_once()
        nearby.assert_not_called()
        device.assert_called_once()
        #
        api.devices = {}


async def test_async_init(hass: HomeAssistant):
    """Test API initialization."""
    now_ts = int(time.time())

    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(hass, DEFAULT_VERIFY_SSL, DEFAULT_TIMEOUT)

    with (
        patch(
            "homeassistant.helpers.storage.Store.async_load",
            new_callable=AsyncMock,
            return_value={},
        ) as store_loader,
        patch(
            "homeassistant.helpers.storage.Store.async_save", new_callable=AsyncMock
        ) as store_saver,
        patch.object(api, "_async_api_wrapper", new_callable=AsyncMock) as wrapper,
    ):
        await api.async_init()

        store_loader.assert_called_once()
        store_saver.assert_called_once()
        wrapper.assert_called_once()

    with (
        patch(
            "homeassistant.helpers.storage.Store.async_load",
            new_callable=AsyncMock,
            return_value={
                DATA_LAST_INIT_TS: now_ts - 86400,
            },
        ) as store_loader,
        patch(
            "homeassistant.helpers.storage.Store.async_save", new_callable=AsyncMock
        ) as store_saver,
        patch.object(api, "_async_api_wrapper", side_effect=AsyncMock()) as wrapper,
    ):
        await api.async_init()

        store_loader.assert_called_once()
        store_saver.assert_called_once()
        wrapper.assert_called_once()

    with (
        patch(
            "homeassistant.helpers.storage.Store.async_load",
            new_callable=AsyncMock,
            return_value={
                DATA_LAST_INIT_TS: now_ts,
            },
        ) as store_loader,
        patch(
            "homeassistant.helpers.storage.Store.async_save", new_callable=AsyncMock
        ) as store_saver,
        patch.object(api, "_async_api_wrapper", new_callable=AsyncMock) as wrapper,
    ):
        await api.async_init()

        store_loader.assert_called_once()
        store_saver.assert_not_called()
        wrapper.assert_not_called()


async def test__async_reset_init(hass: HomeAssistant):
    """Test resetting of API initialization."""
    now_ts = int(time.time())

    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(hass, DEFAULT_VERIFY_SSL, DEFAULT_TIMEOUT)

    with (
        patch(
            "homeassistant.helpers.storage.Store.async_load",
            new_callable=AsyncMock,
            return_value={},
        ) as store_loader,
        patch(
            "homeassistant.helpers.storage.Store.async_save", new_callable=AsyncMock
        ) as store_saver,
    ):
        await api._async_reset_init()

        store_loader.assert_called_once()
        store_saver.assert_called_once_with(
            {
                DATA_LAST_INIT_TS: 0,
            }
        )

    with (
        patch(
            "homeassistant.helpers.storage.Store.async_load",
            new_callable=AsyncMock,
            return_value={
                DATA_LAST_INIT_TS: now_ts - 86400,
            },
        ) as store_loader,
        patch(
            "homeassistant.helpers.storage.Store.async_save", new_callable=AsyncMock
        ) as store_saver,
    ):
        await api._async_reset_init()

        store_loader.assert_called_once()
        store_saver.assert_called_once_with(
            {
                DATA_LAST_INIT_TS: 0,
            }
        )


async def test__async_search_nearby_sensors(hass: HomeAssistant):
    """Test getting nearby sensors."""
    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(hass, DEFAULT_VERIFY_SSL, DEFAULT_TIMEOUT)

    assert api.devices == set()
    assert api._sensors_last_updated is False
    assert api._limit == 1

    now_ts = int(time.time())

    with patch.object(
        api,
        "_async_api_wrapper",
        new_callable=AsyncMock,
        return_value={
            "devices": [
                TEST_DEVICE1_RESULT,
                TEST_DEVICE2_RESULT,
            ],
        },
    ):
        api._nearby_sensor_types = {2}
        api._nearby_listener = listener = AsyncMock()

        await api._async_search_nearby_sensors()

        assert api._sensors_last_updated is True
        assert api._limit == 2
        assert 123 not in api._devices
        listener.assert_called_once()

        api._nearby_listener = listener
        api._nearby_max_distance = 111

        await api._async_search_nearby_sensors()

        assert api._sensors_last_updated is True
        assert api._limit == 2
        assert api._devices[123] == pytest.approx(now_ts, 1)
        assert listener.call_count == 2


# pylint: disable=protected-access
async def test__async_update_sensors(hass: HomeAssistant):
    """Test getting sensors on device."""
    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(hass, DEFAULT_VERIFY_SSL, DEFAULT_TIMEOUT)

    assert api.devices == set()
    assert api._sensors_last_updated is False
    assert api._limit == 1

    now_ts = int(time.time())

    with patch.object(
        api,
        "_async_api_wrapper",
        new_callable=AsyncMock,
        return_value={
            "devices": [
                TEST_DEVICE1_RESULT,
                TEST_DEVICE2_RESULT,
            ],
        },
    ):
        await api._async_update_sensors()

        assert api._sensors_last_updated is True
        assert api._limit == 2
        for i in [123, 234]:
            assert api._devices[i] == now_ts


# In order to get 100% coverage, we also want to simulate raising the exceptions
# to ensure that the function handles them as expected.
# The caplog fixture allows access to log messages in tests. This is particularly
# useful during exception handling testing since often the only action as part of
# exception handling is a logging statement
# pylint: disable=protected-access
async def test__async_api_wrapper(hass: HomeAssistant, aioclient_mock):
    """Test getting nearby sensors."""
    # To test the api submodule, we first create an instance of our API client
    api = NarodmonApiClient(hass, DEFAULT_VERIFY_SSL, DEFAULT_TIMEOUT)

    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, text='{"data": "test response"}')
    with (
        patch.object(api, "_async_reset_init", new_callable=AsyncMock) as reset_init,
    ):
        assert await api._async_api_wrapper({}) == {
            "data": "test response",
        }

    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, status=HTTPStatus.NOT_FOUND)
    with pytest.raises(NarodmonApiError) as exception:
        await api._async_api_wrapper({})

    assert exception.value.status == "Invalid response from Narodmon API: 404"

    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, text=load_fixture("error_400.json"))
    with (
        patch.object(api, "_async_reset_init", new_callable=AsyncMock) as reset_init,
        pytest.raises(NarodmonApiError) as exception,
    ):
        await api._async_api_wrapper({})

    assert exception.value.status == "Отсутствует ключ приложения: api_key"
    reset_init.assert_not_called()

    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, text=load_fixture("error_401.json"))
    with (
        patch.object(api, "_async_reset_init", new_callable=AsyncMock) as reset_init,
        pytest.raises(NarodmonUnauthorizedError) as exception,
    ):
        await api._async_api_wrapper({})

    assert exception.value.status == "Требуется авторизация"
    reset_init.assert_called_once()

    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, exc=asyncio.TimeoutError)
    with pytest.raises(asyncio.TimeoutError):
        await api._async_api_wrapper({})

    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, exc=TypeError)
    with pytest.raises(TypeError):
        await api._async_api_wrapper({})

    aioclient_mock.clear_requests()
    #
    aioclient_mock.post(ENDPOINT_URL, exc=aiohttp.ClientError)
    with pytest.raises(aiohttp.ClientError):
        await api._async_api_wrapper({})
