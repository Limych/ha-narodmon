"""Tests for Narodmon.ru Cloud Integration component."""
import glob
import json
import os
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest import raises
from pytest_homeassistant_custom_component.common import load_fixture
from voluptuous import Invalid

from custom_components.narodmon import DOMAIN, cv_apikey, get_uuid
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
        "g]6Um84dud5_ja+q",
        "Y{*]N.n7#&N_4p&[",
    ]:
        with raises(Invalid):
            cv_apikey(apikey)


async def test_get_uuid(hass: HomeAssistant, tmpdir):
    """Test generating and storing UUID."""
    hass.config.config_dir = tmpdir
    storage_dir = tmpdir + "/.storage"
    os.makedirs(storage_dir, exist_ok=True)

    # Generate and store UUID
    uuid = get_uuid(hass)

    # Read UUID
    assert get_uuid(hass) == uuid

    # Cleanup storage directory
    files = glob.glob(f"{storage_dir}/*")
    for fp in files:
        os.remove(fp)

    # Generate new UUID
    assert get_uuid(hass) != uuid


async def test_setup(hass: HomeAssistant):
    """Test setup from configuration.yaml."""
    with patch(
        "custom_components.narodmon.get_uuid", return_value="B46CD5A6B1BC28E3D"
    ), patch.object(
        NarodmonApiClient,
        "async_get_nearby_sensors",
        return_value=json.loads(load_fixture("sensorsNearby.json")),
    ):
        assert await async_setup_component(hass, DOMAIN, MOCK_YAML_CONFIG)
        await hass.async_block_till_done()
        assert len(hass.states.async_all()) == 2
