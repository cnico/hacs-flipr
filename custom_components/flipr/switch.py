"""Switch platform for the Flipr's hub"""
import logging

from homeassistant.components.switch import SwitchEntity

from homeassistant.const import (
    STATE_OFF,
    STATE_ON
)

from . import FliprEntity
from .const import ATTRIBUTION, CONF_FLIPR_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up hub in flipr account"""
    async def get_hubs():
            """Retrieve flipr hub ids."""
            hubs = []

    entities = []
    om_switches = []

    switch_type = get_key_for_word(OPENMOTICS_OUTPUT_TYPE_TO_NAME, 'outlet')
    for module in gateway.get_om_output_modules():
        if module['type'] == switch_type:
            om_switches.append(module)

    if not om_switches:
        _LOGGER.debug("No switches/outlets found.")
        return False

    for entity in om_switches:
        _LOGGER.debug("Adding switch %s", entity)
        entities.append(OpenMoticsSwitch(hass, gateway, entity))

    if not entities:
        _LOGGER.warning("No OpenMotics Switch added")
        return False

    async_add_entities(entities)


class FliprSwitch(FliprEntity, SwitchEntity):
    """Representation of a Flipr hub switch."""

    def __init__(self, hass, gateway, switch):
        """Initialize the switch."""
        self._hass = hass
        self.gateway = gateway
        self._id = switch['id']
        self._name = switch['name']
        self._floor = switch['floor']
        self._room = switch['room']
        self._timer = None
        self._dimmer = None
        self._state = None

        self._refresh()

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def floor(self):
        """Return the floor of the switch."""
        return self._floor

    @property
    def room(self):
        """Return the room of the switch."""
        return self._room

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state == STATE_ON

    @property
    def device_info(self):
        """Return information about the device."""
        info = {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "id": self.unique_id,
            "floor": self.floor,
            "room": self.room,
            "manufacturer": "Flipr",
        }
        return info

    @property
    def available(self):
        """If hub is available."""
        return self._state is not None

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        sop = self.gateway.api.set_output(self._id, True, self._dimmer, self._timer)
        if sop['success'] is True:
            self._state = STATE_ON
        else:
            _LOGGER.error("Error setting output id %s to True", self._id)
            self._state = STATE_OFF

    async def async_turn_off(self, **kwargs):
        """Turn devicee off."""
        sop = self.gateway.api.set_output(self._id, False, None, None)
        if sop['success'] is True:
            self._state = STATE_OFF
        else:
            _LOGGER.error("Error setting output id %s to False", self._id)
            self._state = STATE_ON

    async def async_update(self):
        """Retrieve latest state."""
        self._refresh()

    def _refresh(self):
        """Update the state of the switch."""
        if not self.gateway.update() and self._state is not None:
            return

        output_status = self.gateway.get_output_status(self._id)

        if not output_status:
            _LOGGER.error('Switch._refresh: No responce form the controller')
            return

        # var_dump(output_status)
        if output_status['dimmer'] is not None:
            self._dimmer = output_status['dimmer']

        if output_status['ctimer'] is not None:
            self._ctimer = output_status['ctimer']

        if output_status['status'] is not None:
            if output_status['status'] == 1:
                self._state = STATE_ON
            else:
                self._state = STATE_OFF
        else:
            self._state = None