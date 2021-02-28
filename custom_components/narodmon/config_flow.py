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
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_TIMEOUT, CONF_VERIFY_SSL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import cv_apikey, get_uuid
from .api import NarodmonApiClient
from .const import CONF_APIKEY, DOMAIN  # pylint: disable=unused-import


class NarodmonFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Narodmon."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_import(self, platform_config):
        """Import a config entry.

        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="configuration.yaml", data=platform_config)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        for entry in self._async_current_entries():
            if entry.source == "import":
                return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(user_input)
            if valid:
                return self.async_create_entry(
                    title=self.hass.config.location_name, data=user_input
                )

            self._errors["base"] = "auth"

        return await self._show_config_form(user_input)

    async def _test_credentials(self, config):
        """Return true if credentials is valid."""
        try:
            uuid = get_uuid(self.hass)

            apikey = config.get(CONF_APIKEY)
            verify_ssl = config.get(CONF_VERIFY_SSL)
            timeout = config.get(CONF_TIMEOUT)

            session = async_get_clientsession(self.hass, verify_ssl=verify_ssl)
            client = NarodmonApiClient(session, uuid, apikey, timeout)
            await client.async_get_nearby_sensors(
                self.hass.config.latitude, self.hass.config.longitude, ["humidity"]
            )
            return True

        except Exception:  # pylint: disable=broad-except
            return False

    async def _show_config_form(self, cfg):
        """Show the configuration form to edit location data."""
        if cfg is None:
            cfg = {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_APIKEY, default=cfg.get(CONF_APIKEY)): cv_apikey,
                }
            ),
            errors=self._errors,
        )


#
#     @staticmethod
#     @callback
#     def async_get_options_flow(config_entry):
#         """Get component options flow."""
#         return NarodmonOptionsFlowHandler(config_entry)
#
#
# class NarodmonOptionsFlowHandler(config_entries.OptionsFlow):
#     """Narodmon config flow options handler."""
#
#     def __init__(self, config_entry):
#         """Initialize HACS options flow."""
#         self.config_entry = config_entry
#         self.options = dict(config_entry.options)
#
#     async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
#         """Manage the options."""
#         return await self.async_step_user()
#
#     async def async_step_user(self, user_input=None):
#         """Handle a flow initialized by the user."""
#         if user_input is not None:
#             self.options.update(user_input)
#             return await self._update_options()
#
#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema(
#                 {
#                     vol.Required(x, default=self.options.get(x, True)): bool
#                     for x in sorted(PLATFORMS)
#                 }
#             ),
#         )
#
#     async def _update_options(self):
#         """Update config entry options."""
#         return self.async_create_entry(
#             title=self.config_entry.data.get(CONF_USERNAME), data=self.options
#         )
