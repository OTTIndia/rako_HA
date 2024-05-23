from homeassistant.components.switch import SwitchEntity
from homeassistant.const import ATTR_BRIGHTNESS

class RakoSwitch(SwitchEntity):
    """Representation of a Rako Switch."""

    def __init__(self, bridge, switch):
        """Initialize a Rako Switch."""
        self.bridge = bridge
        self._switch = switch
        self._available = True

    @property
    def name(self):
        """Return the display name of this switch."""
        return self._switch.name

    @property
    def unique_id(self):
        """Switch's unique ID."""
        return self._switch.unique_id

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        await self.bridge.register_for_state_updates(self)

    async def async_will_remove_from_hass(self):
        """Run when entity about to be removed from hass."""
        await self.bridge.deregister_for_state_updates(self)

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._switch.is_on

    async def async_turn_on(self, **kwargs):
        """Turn on the switch."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            await self._switch.turn_on(brightness=brightness)
        else:
            await self._switch.turn_on()

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        await self._switch.turn_off()
