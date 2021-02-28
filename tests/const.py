"""Constants for tests."""
from homeassistant.const import CONF_DEVICES, CONF_SENSORS

from custom_components.narodmon.const import CONF_APIKEY, DOMAIN

# Mock config data to be used across multiple tests
MOCK_YAML_CONFIG = {
    DOMAIN: {
        CONF_APIKEY: "654FJG34816345qdlkjmlkJHGBnbh",
        CONF_DEVICES: [
            {
                CONF_SENSORS: [
                    "humidity",
                    "pressure",
                ],
            }
        ],
    },
}
