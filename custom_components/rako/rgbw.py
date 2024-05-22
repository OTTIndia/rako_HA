import logging

from homeassistant.components.light import LightEntity
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Rako RGBW light based on a config entry."""
    bridge = hass.data[DOMAIN][config_entry.entry_id].rako_bridge_client
    rgbw_lights = await bridge.discover_rgbw_lights()

    async_add_entities(RakoRGBW(light) for light in rgbw_lights)

class RakoRGBW(LightEntity):
    def __init__(self, light):
        self._light = light
        self._brightness = light.brightness
        self._hs_color = light.hs_color

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
    def hs_color(self):
        return self._hs_color

    @property
    def is_on(self):
        return self._brightness > 0

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        self._brightness = kwargs.get("brightness", 255)
        hs_color = kwargs.get("hs_color", self._hs_color)
       await self.hass.data[DOMAIN][self._light.mac].rako_bridge_client.set_rgbw(self.unique_id, hs_color)
