"""Tests for Narodmon Cloud Integration component."""
import logging
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from voluptuous import Invalid

from custom_components.narodmon import (
    CONF_APIKEY,
    DOMAIN,
    YAML_DOMAIN,
    NarodmonDataUpdateCoordinator,
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
    cv_apikey,
)
from custom_components.narodmon.api import NarodmonApiClient

from .const import MOCK_YAML_CONFIG


async def test_cv_apikey():
    """Test API keys verification."""
    # Valid keys
    for apikey in [
        "B46CD5A6B1BC28E3D",
        "d41d8cd98f00b204e9800998ecf8427e",
        "iTkToPPq6SFMOvM7kkcBxmHRcHsOVpVN",
        "e852o0eK4DSEoImMsWoLDIpyB4g02iC486P9pY9b8WqJhmiwJBJqEUUgpRLB0z",
        "MujSTK",
    ]:
        assert cv_apikey(apikey)

    # Invalid keys
    for apikey in [
        "B46CD5A6B1BC28E3D+",
        "=0b204e9800998ecf",
        '2Q*j>*Q%ppgOK"~W',
        123,
        b"B46CD5A6B1BC28E3D",
    ]:
        with pytest.raises(Invalid):
            cv_apikey(apikey)


async def test_setup(hass: HomeAssistant, caplog):
    """Test setup from configuration.yaml."""
    with patch.object(
        NarodmonApiClient,
        "async_init",
        new_callable=AsyncMock,
    ), patch.object(
        NarodmonApiClient, "async_update_data", new_callable=AsyncMock, return_value={}
    ), caplog.at_level(
        logging.WARNING
    ):
        assert await async_setup_component(hass, DOMAIN, MOCK_YAML_CONFIG)
        await hass.async_block_till_done()
        assert len(hass.states.async_all()) == 2
        assert len(caplog.records) == 1


async def test_setup_apikey(hass: HomeAssistant, caplog):
    """Test setup from configuration.yaml."""
    with patch.object(
        NarodmonApiClient,
        "async_init",
        new_callable=AsyncMock,
    ), patch.object(
        NarodmonApiClient, "async_update_data", new_callable=AsyncMock, return_value={}
    ), caplog.at_level(
        logging.WARNING
    ):
        cfg = MOCK_YAML_CONFIG
        cfg[DOMAIN][CONF_APIKEY] = "testapikey"
        assert await async_setup_component(hass, DOMAIN, MOCK_YAML_CONFIG)
        await hass.async_block_till_done()
        assert len(hass.states.async_all()) == 2
        assert len(caplog.records) == 2


# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.
async def test_setup_unload_and_reload_entry(hass: HomeAssistant, bypass_get_data):
    """Test entry setup and unload."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, entry_id="test", source=config_entries.SOURCE_IMPORT
    )
    #
    hass.data.setdefault(YAML_DOMAIN, {})
    hass.data[YAML_DOMAIN] = MOCK_YAML_CONFIG[DOMAIN]

    # Set up the entry and assert that the values set during setup are where we expect
    # them to be. Because we have patched the BlueprintDataUpdateCoordinator.async_get_data
    # call, no code from custom_components/integration_blueprint/api.py actually runs.
    assert await async_setup_entry(hass, config_entry)
    assert (
        DOMAIN in hass.data
        and config_entry.entry_id in hass.data[DOMAIN]
        and isinstance(hass.data[DOMAIN][config_entry.entry_id], dict)
    )
    for item in hass.data[DOMAIN][config_entry.entry_id].values():
        assert isinstance(item, NarodmonDataUpdateCoordinator)

    # Reload the entry and assert that the data from above is still there
    assert await async_reload_entry(hass, config_entry) is None
    assert (
        DOMAIN in hass.data
        and config_entry.entry_id in hass.data[DOMAIN]
        and isinstance(hass.data[DOMAIN][config_entry.entry_id], dict)
    )
    for item in hass.data[DOMAIN][config_entry.entry_id].values():
        assert isinstance(item, NarodmonDataUpdateCoordinator)

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.entry_id not in hass.data[DOMAIN]


async def test_setup_entry_exception(hass: HomeAssistant, error_on_get_data):
    """Test ConfigEntryNotReady when API raises an exception during entry setup."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(
        domain=DOMAIN, entry_id="test", source=config_entries.SOURCE_IMPORT
    )
    #
    hass.data.setdefault(YAML_DOMAIN, {})
    hass.data[YAML_DOMAIN] = MOCK_YAML_CONFIG[DOMAIN]

    # In this case we are testing the condition where async_setup_entry raises
    # ConfigEntryNotReady using the `error_on_get_data` fixture which simulates
    # an error.
    with pytest.raises(ConfigEntryNotReady):
        assert await async_setup_entry(hass, config_entry)
