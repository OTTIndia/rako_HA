"""Rako curtain platform."""

from homeassistant.components.cover import CoverEntity
from .bridge import RakoBridge
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Rako curtain entities from a config entry."""
    bridge = hass.data[DOMAIN][config_entry.data["mac"]]["rako_bridge_client"]
    curtains = await bridge.discover_curtains()
    async_add_entities(RakoCurtain(curtain) for curtain in curtains)

class RakoCurtain(CoverEntity):
    """Representation of a Rako curtain."""

    def __init__(self, curtain):
        self._curtain = curtain
        self._attr_name = curtain.name

    async def async_open_cover(self, **kwargs):
        """Open the curtain."""
        await self._curtain.open()

    async def async_close_cover(self, **kwargs):
        """Close the curtain."""
        await self._curtain.close()

    async def async_stop_cover(self, **kwargs):
        """Stop the curtain."""
        await self._curtain.stop()
