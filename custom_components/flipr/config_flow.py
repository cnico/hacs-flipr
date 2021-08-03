"""Config flow for Flipr integration."""
from typing import List

from flipr_api import FliprAPIRestClient
from requests.exceptions import HTTPError
import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN
)
from .crypt_util import encrypt_data


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Flipr."""

    VERSION = 1
    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize Flipr config flow."""
        self._username = None
        self._password = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        await self.async_set_unique_id(DOMAIN)

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self._show_setup_form()

        self._username = user_input[CONF_USERNAME]
        self._password = user_input[CONF_PASSWORD]

        # Encrypt password before storing it in the config json file.
        crypted_password = encrypt_data(self._password, self._flipr_id)

        return self.async_create_entry(
            title="Flipr device(s)" ,
            data={
                CONF_USERNAME: self._username,
                CONF_PASSWORD: crypted_password
            },
        )

    def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=errors,
        )

    #TODO: not used, to remove
    async def _authenticate_and_search_flipr(self) -> List[str]:
        """Validate the username and password provided and searches for a flipr id."""
        client = await self.hass.async_add_executor_job(
            FliprAPIRestClient, self._username, self._password
        )

        flipr_ids = await self.hass.async_add_executor_job(client.search_all_ids)

        return flipr_ids

    async def async_step_import(self, user_input):
        """Import a config entry."""
        return await self.async_step_user(user_input)
