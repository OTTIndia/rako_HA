"""Rako RGBW light platform."""

from homeassistant.components.light import LightEntity
from .bridge import RakoBridge
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Rako RGBW light entities from a config entry."""
    bridge = hass.data[DOMAIN][config_entry.data["mac"]]["rako_bridge_client"]
    lights = await bridge.discover_rgbw_lights()
    async_add_entities(RakoRGBW(light) for light in lights)

class RakoRGBW(LightEntity):
    """Representation of a Rako RGBW light."""

    def __init__(self, light):
        self._light = light
        self._attr_name = light.name
        self._attr_brightness = light.brightness
        self._attr_rgb_color = light.rgb_color
        self._attr_is_on = light.is_on

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        await self._light.turn_on()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._light.turn_off()
