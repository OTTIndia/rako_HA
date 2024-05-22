import logging

from homeassistant.components.light import LightEntity
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Rako light based on a config entry."""
    bridge = hass.data[DOMAIN][config_entry.entry_id].rako_bridge_client
    session = None  # Create your session if needed
    lights = await bridge.discover_lights(session)

    async_add_entities(RakoLight(light) for light in lights)

class RakoLight(LightEntity):
    def __init__(self, light):
        self._light = light
        self._brightness = light.brightness

    @property
    def unique_id(self):
        return self._light.unique_id

    @property
    def name(self):
        return self._light.name

    @property
    def brightness(self):
        return self._brightness

    @property
    def is_on(self):
        return self._brightness > 0

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        await self.hass.data[DOMAIN][self._light.mac].rako_bridge_client.turn_on_light(self.unique_id)
        self._brightness = 255
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self.hass.data[DOMAIN][self._light.mac].rako_bridge_client.turn_off_light(self.unique_id)
        self._brightness = 0
        self.async_write_ha_state()
