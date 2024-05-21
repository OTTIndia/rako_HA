"""Rako switch platform."""

from homeassistant.components.switch import SwitchEntity
from .bridge import RakoBridge
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Rako switch entities from a config entry."""
    bridge = hass.data[DOMAIN][config_entry.data["mac"]]["rako_bridge_client"]
    switches = await bridge.discover_switches()
    async_add_entities(RakoSwitch(switch) for switch in switches)

class RakoSwitch(SwitchEntity):
    """Representation of a Rako switch."""

    def __init__(self, switch):
        self._switch = switch
        self._attr_name = switch.name
        self._attr_is_on = switch.is_on

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._switch.turn_on()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._switch.turn_off()
