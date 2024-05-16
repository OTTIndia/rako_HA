"""Light platform for Rako."""
from homeassistant.components.light import LightEntity
from .const import DOMAIN

class RakoLight(LightEntity):
    """Representation of a Rako light."""

    def __init__(self, name):
        """Initialize the light."""
        self._name = name
        self._state = False

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        self._state = True

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        self._state = False
