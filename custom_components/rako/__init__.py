from __future__ import annotations

from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.typing import StateType

class RakoSwitch(ToggleEntity):
    """Representation of a Rako Switch."""

    def __init__(self, bridge: RakoBridge, room, channel) -> None:
        """Initialize a Rako Switch."""
        self._bridge = bridge
        self._room = room
        self._channel = channel

    @property
    def name(self) -> str:
        """Return the display name of this switch."""
        return f"{self._room.name} - Channel {self._channel.number}"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._channel.state == STATE_ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self._channel.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self._channel.turn_off()

    async def async_toggle(self, **kwargs: Any) -> None:
        """Toggle the switch."""
        if self.is_on:
            await self.async_turn_off(**kwargs)
        else:
            await self.async_turn_on(**kwargs)

    @property
    def device_state_attributes(self) -> dict[str, StateType]:
        """Return the state attributes of the switch."""
        return {
            "room_id": self._room.id,
            "channel_number": self._channel.number,
        }
