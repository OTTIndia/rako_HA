import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Rako switch based on a config entry."""
    bridge = hass.data[DOMAIN][config_entry.entry_id].rako_bridge_client
    switches = await bridge.discover_switches()

    async_add_entities(RakoSwitch(switch) for switch in switches)

class RakoSwitch(SwitchEntity):
    def __init__(self, switch):
        self._switch = switch
        self._is_on = switch.is_on

    @property
    def unique_id(self):
        return self._switch.unique_id

    @property
    def name(self):
        return self._switch.name

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self.hass.data[DOMAIN][self._switch.mac].rako_bridge_client.turn_on_switch(self.unique_id)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self.hass.data[DOMAIN][self._switch.mac].rako_bridge_client.turn_off_switch(self.unique_id)
        self._is_on = False
        self.async_write_ha_state()
