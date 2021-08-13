"""Switch platform for the Flipr's hub"""
import logging

# Conditional import for switch device
try:
    from homeassistant.components.switch import SwitchEntity
except ImportError:
    from homeassistant.components.switch import SwitchDevice as SwitchEntity

from homeassistant.const import STATE_OFF, STATE_ON, ATTR_ATTRIBUTION

from . import FliprEntity
from .const import ATTRIBUTION, DOMAIN, MANUFACTURER, NAME, FliprType

import logging
_LOGGER = logging.getLogger(__name__)

SWITCHS = {"hub_status": {"unit": None, "icon": None, "name": "Hub Status"}}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up hub in flipr account"""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    switchs_list = []

    flipr_hubs = [device.id for device in coordinator.data
                  if device.type == FliprType.hub]

    for flipr_hub in flipr_hubs:
        for switch in SWITCHS:
            switchs_list.append(FliprSwitch(coordinator, flipr_hub, switch))

    async_add_entities(switchs_list, True)


class FliprSwitch(FliprEntity, SwitchEntity):
    """Representation of a Flipr hub switch."""

    @property
    def device_info(self):
        """Define device information global to entities."""
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.flipr_id)
            },
            "name": NAME,
            "manufacturer": MANUFACTURER,
        }

    @property
    def name(self):
        """Return the name of the particular component."""
        return f"Hub {self.flipr_id} "

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state == STATE_ON

    @property
    def icon(self):
        """Return the icon."""
        return SWITCHS[self.info_type]["icon"]

    @property
    def available(self):
        """If hub is available."""
        return self._state is not None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn hub on."""
        result = await self.coordinator.async_set_hub_state(self.flipr_id, True)

        if result is not True:
            _LOGGER.error("Error turning on the hub id %s", self.flipr_id)
        else:
            self._state = STATE_ON
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn hub off."""
        result = await self.coordinator.async_set_hub_state(self.flipr_id, False)

        if result is not False:
            _LOGGER.error("Error turning off the hub id %s", self.flipr_id)
        else:
            self._state = STATE_OFF
            self.async_write_ha_state()

    async def async_update(self):
        """Retrieve latest state."""
        self._refresh()

    def _refresh(self):
        """Update the state of the switch."""
        state = self.coordinator.device(
            self.flipr_id).data["state"]

        if state == True:
            self._state = STATE_ON
        elif state == False:
            self._state = STATE_OFF
        else:
            self._state = None
