"""Tests for Narodmon.ru Cloud Integration component."""
import json
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import load_fixture

from custom_components.narodmon import DOMAIN
from custom_components.narodmon.api import NarodmonApiClient

from .const import MOCK_YAML_CONFIG


async def test_setup(hass: HomeAssistant):
    """Test setup from configuration.yaml."""
    with patch.object(
        NarodmonApiClient,
        "async_get_nearby_sensors",
        return_value=json.loads(load_fixture("sensorsNearby.json")),
    ):
        assert await async_setup_component(hass, DOMAIN, MOCK_YAML_CONFIG)
        await hass.async_block_till_done()
        assert len(hass.states.async_all()) == 2
