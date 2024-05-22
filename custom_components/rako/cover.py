import logging

from homeassistant.components.cover import CoverEntity
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Rako cover based on a config entry."""
    bridge = hass.data[DOMAIN][config_entry.entry_id].rako_bridge_client
    covers = await bridge.discover_covers()

    async_add_entities(RakoCover(cover) for cover in covers)

class RakoCover(CoverEntity):
    def __init__(self, cover):
        self._cover = cover
        self._is_open = cover.is_open

    @property
    def unique_id(self):
        return self._cover.unique_id

    @property
    def name(self):
        return self._cover.name

    @property
    def is_open(self):
        return self._is_open

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self.hass.data[DOMAIN][self._cover.mac].rako_bridge_client.open_cover(self.unique_id)
        self._is_open = True
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        await self.hass.data[DOMAIN][self._cover.mac].rako_bridge_client.close_cover(self.unique_id)
        self._is_open = False
        self.async_write_ha_state()
