import homeassistant.components.sensor as sensor
import respx
from homeassistant.const import CONF_DEVICE_ID, CONF_PLATFORM
from homeassistant.setup import async_setup_component

from custom_components.narodmon.const import CONF_APIKEY

BASE_URL = "https://narodmon.ru/api/sensorsOnDevice"


MOCK_CONFIG = {
    CONF_PLATFORM: "narodmon",
    CONF_APIKEY: "6532fadsjte246GRE",
    CONF_DEVICE_ID: "D6724",
}


@respx.mock
async def test_setup(hass):
    """Test setup with minimum configuration."""
    respx.get(BASE_URL) % 200
    assert await async_setup_component(
        hass,
        sensor.DOMAIN,
        {
            "sensor": MOCK_CONFIG,
        },
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 1
