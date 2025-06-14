#  Copyright (c) 2021-2025, Andrey "Limych" Khrolenok <andrey@khrolenok.ru>
#  Creative Commons BY-NC-SA 4.0 International Public License
#  (see LICENSE.md or https://creativecommons.org/licenses/by-nc-sa/4.0/)
"""
The narodmon Cloud Integration Component.

For more details about this sensor, please refer to the documentation at
https://github.com/Limych/ha-narodmon/
"""

from copy import deepcopy

import voluptuous as vol
from homeassistant.config_entries import (
    CONN_CLASS_CLOUD_POLL,
    SOURCE_IMPORT,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_SHOW_ON_MAP, CONF_TIMEOUT, CONF_VERIFY_SSL
from homeassistant.core import callback
from homeassistant.helpers.typing import ConfigType

from .api import NarodmonApiClient
from .const import DOMAIN  # pylint: disable=unused-import


class NarodmonFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Narodmon."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize."""
        self._errors = {}

    async def async_step_import(self, config: ConfigType) -> ConfigFlowResult:
        """
        Import a config entry.

        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="configuration.yaml", data=config)

    async def async_step_user(self, user_input: ConfigType = None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        self._errors = {}

        for entry in self._async_current_entries():
            if entry.source == SOURCE_IMPORT:
                return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(user_input)
            if valid:
                return self.async_create_entry(
                    title=self.hass.config.location_name, data=user_input
                )

            self._errors["base"] = "auth"

        return await self._show_config_form(user_input)

    async def _test_credentials(self, config: ConfigType) -> bool:
        """Return true if credentials is valid."""
        try:
            verify_ssl = config.get(CONF_VERIFY_SSL)
            timeout = config.get(CONF_TIMEOUT)

            client = NarodmonApiClient(
                self.hass, verify_ssl=verify_ssl, timeout=timeout
            )
            await client.async_init()

        except Exception:  # pylint: disable=broad-except;  #noqa: BLE001
            return False
        else:
            return True

    async def _show_config_form(self, cfg: ConfigType) -> ConfigFlowResult:
        """Show the configuration form to edit location data."""
        if cfg is None:
            cfg = {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            errors=self._errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get component options flow."""
        return NarodmonOptionsFlowHandler(config_entry)


class NarodmonOptionsFlowHandler(OptionsFlow):
    """Narodmon config flow options handler."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize HACS options flow."""
        self._options = deepcopy(dict(config_entry.options))

    async def async_step_init(
        self,
        user_input: ConfigType = None,  # noqa: ARG002
    ) -> ConfigFlowResult:  # pylint: disable=unused-argument
        """Manage the options."""
        if self._config_entry.source == SOURCE_IMPORT:
            return self.async_abort(reason="no_options_available")

        return await self.async_step_user()

    async def async_step_user(self, user_input: ConfigType = None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SHOW_ON_MAP,
                        default=self._options.get(CONF_SHOW_ON_MAP, False),
                    ): bool,
                }
            ),
        )

    async def _update_options(self) -> ConfigFlowResult:
        """Update config entry options."""
        return self.async_create_entry(
            title=self.hass.config.location_name, data=self._options
        )
