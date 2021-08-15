"""The Flipr integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from time import time
from typing import Dict

from async_timeout import timeout
from flipr_api import FliprAPIRestClient
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed
)

from .const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
    API_TIMEOUT,
    FliprResult,
    FliprType
)
from .crypt_util import decrypt_data

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_FLIPR = 3600
SCAN_INTERVAL_HUB = 300
SCAN_INTERVAL_GLOBAL = timedelta(minutes=1)

PLATFORMS = ["sensor", "binary_sensor", "switch", "select"]


async def async_setup(hass: HomeAssistant, config: Dict) -> bool:
    """Set up the Flipr component."""
    # Make sure coordinator is initialized.
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Flipr from a config entry."""
    _LOGGER.debug("async_setup_entry starting")

    coordinator = FliprDataUpdateCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(
                    entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class FliprDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to hold Flipr data retrieval."""

    def __init__(self, hass, entry):
        """Initialize."""
        username = entry.data[CONF_USERNAME]
        crypted_password = entry.data[CONF_PASSWORD]

        _LOGGER.debug("Config entry values : %s", username)

        # Decrypt stored password in config.
        password = decrypt_data(crypted_password, username)

        # Establishes the connection.
        self.client = FliprAPIRestClient(username, password)
        self.hass = hass
        self.entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name=f"Flipr device update",
            update_interval=SCAN_INTERVAL_GLOBAL,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        with timeout(API_TIMEOUT):
            try:
                _LOGGER.debug("Fetching Flipr devices")
                devices = await self.hass.async_add_executor_job(self.client.search_all_ids)
                results = await asyncio.gather(
                    *(self._fetch_flipr_data(device)
                        for device in devices['flipr']),
                    *(self._fetch_hub_data(device)
                      for device in devices['hub'])
                )
                return results
            except Exception as err:
                raise UpdateFailed(err) from err

    async def _fetch_flipr_data(self, id) -> FliprResult:
        """Fetch latest Flipr data."""
        if (self.device(id) is not None) and (self.device(id).last_read + SCAN_INTERVAL_FLIPR > time()):
            # Data fresh enough, skip reading
            return self.device(id)
        else:
            # Refresh Data
            flipr_data = await self.hass.async_add_executor_job(self.client.get_pool_measure_latest, id)
            return FliprResult(id=id, type=FliprType.flipr, last_read=time(), data=flipr_data)

    async def _fetch_hub_data(self, id: str) -> FliprResult:
        """Fetch latest Flipr hub data."""
        _LOGGER.debug(self.device(id))
        if (self.device(id) is not None) and (self.device(id).last_read + SCAN_INTERVAL_HUB > time()):
            # Data fresh enough, skip reading
            _LOGGER.debug("skip fetching hub data for %s", id)
            return self.device(id)
        else:
            # Refresh Data
            _LOGGER.debug("Fetching hub data for %s", id)
            flipr_data = await self.hass.async_add_executor_job(self.client.get_hub_state, id)
            return FliprResult(id=id, type=FliprType.hub, last_read=time(), data=flipr_data)

    async def async_set_hub_state(self, id: str, state: bool) -> bool:
        """Set Flipr hub state."""
        _LOGGER.debug("Set hub %s state to %s", id, state)
        result = await self.hass.async_add_executor_job(self.client.set_hub_state, id, state)
        if result is not None:
            # refresh data state
            self.device(id).data["state"] = result["state"]
            self.device(id).data["mode"] = result["mode"]
            self.device(id).data["last_read"] = time()
        return result["state"]

    async def async_set_hub_mode(self, id: str, mode: str) -> str:
        """Set Flipr hub mode."""
        _LOGGER.debug("Set hub %s mode to %s", id, mode)
        result = await self.hass.async_add_executor_job(self.client.set_hub_mode, id, mode)
        if result is not None:
            # refresh data state
            self.device(id).data["state"] = result["state"]
            self.device(id).data["mode"] = result["mode"]
            self.device(id).data["last_read"] = time()
        return result["mode"]

    def device(self, id: str) -> FliprResult:
        if self.data is None:
            return None

        for device in self.data:
            if device.id == id:
                return device
        else:
            return None


class FliprEntity(CoordinatorEntity):
    """Implements a common class elements representing the Flipr component."""

    def __init__(self, coordinator, flipr_id, info_type):
        """Initialize Flipr sensor."""
        super().__init__(coordinator)
        self._unique_id = f"{flipr_id}-{info_type}"
        self.info_type = info_type
        self.flipr_id = flipr_id

    @ property
    def unique_id(self):
        """Return a unique id."""
        return self._unique_id
