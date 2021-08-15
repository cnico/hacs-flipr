"""Support for Flipr hub mode"""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.const import (
    ATTR_NAME,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER
)


from . import (
    FliprEntity,
    FliprDataUpdateCoordinator
)

from .const import (
    ATTRIBUTION,
    DOMAIN,
    MANUFACTURER,
    NAME,
    MODE_HUB_AUTO,
    MODE_HUB_MANUAL,
    MODE_HUB_PLANNING,
    HUB_MODES,
    FliprType,
    FliprResult
)

import logging
_LOGGER = logging.getLogger(__name__)

SELECTS = {"hub_mode": {"icon": "mdi-air-humidifier",
                        "name": "Hub mode", "modes": HUB_MODES}}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Flipr hub modes."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    select_list = []

    flipr_hubs = [device.id for device in coordinator.data
                  if device.type == FliprType.hub]

    for flipr_hub in flipr_hubs:
        for select in SELECTS:
            select_list.append(FliprModeSelect(coordinator, flipr_hub, select))

    async_add_entities(select_list, True)


class FliprModeSelect(FliprEntity, SelectEntity):
    """Representation of a flipr hub mode select entity."""
    @property
    def unique_id(self) -> str:
        """Define device unique_id."""
        return f"{self.flipr_id}-flipr-hub-mode-select"

    @property
    def device_info(self) -> dict:
        """Define device information global to entities."""
        return {
            ATTR_IDENTIFIERS: {
                (DOMAIN, self.flipr_id)
            },
            ATTR_NAME: NAME,
            ATTR_MANUFACTURER: MANUFACTURER,
        }

    @property
    def name(self) -> str:
        """Return the name of the particular component."""
        return f"Flipr {self.flipr_id} {SELECTS[self.info_type]['name']}"

    @property
    def current_option(self) -> str:
        """Return the curent mode."""
        return str(self.coordinator.device(self.flipr_id).data["mode"])

    @property
    def options(self) -> list:
        """Return the possible modes."""
        return SELECTS[self.info_type]['modes']

    async def async_select_option(self, option: str) -> None:
        """Change the hub mode."""
        if option in self.options:
            result = await self.coordinator.async_set_hub_mode(self.flipr_id, option)
            if result != option:
                _LOGGER.error("Error changing hub id %s to %s",
                              self.flipr_id, option)
            else:
                self._attr_current_option = result
                self.async_schedule_update_ha_state()
        else:
            raise ValueError(
                f"Can't set the hub mode to {option}. Allowed modes are: {self.options}"
            )
