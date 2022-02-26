"""Constants for tests."""
from typing import Final

from homeassistant.const import CONF_DEVICES, CONF_NAME, CONF_SENSORS

from custom_components.narodmon.const import DOMAIN

# Mock config data to be used across multiple tests
MOCK_YAML_CONFIG: Final = {
    DOMAIN: {
        CONF_DEVICES: [
            {
                CONF_NAME: "Test",
                CONF_SENSORS: [
                    "humidity",
                    "pressure",
                ],
            }
        ],
    },
}
