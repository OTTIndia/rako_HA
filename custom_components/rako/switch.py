"""Platform for switch integration."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import python_rako
from python_rako.exceptions import RakoBridgeError

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_BRIGHTNESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .util import create_unique_id

if TYPE_CHECKING:
    from .bridge import RakoBridge
    from .model import RakoDomainEntryData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the config entry."""
    rako_domain_entry_data: RakoDomainEntryData = hass.data[DOMAIN][entry.unique_id]
    bridge = rako_domain_entry_data["rako_bridge_client"]

    hass_switches: list[SwitchEntity] = []
    session = async_get_clientsession(hass)

    async for switch in bridge.discover_switches(session):
        if isinstance(switch, python_rako.Switch):
            if isinstance(switch, python_rako.RoomSwitch):
                hass_switch = RakoRoomSwitch(bridge, switch)
            elif isinstance(switch, python_rako.ChannelSwitch):
                hass_switch = RakoChannelSwitch(bridge, switch)
            else:
                continue

            hass_switches.append(hass_switch)

    async_add_entities(hass_switches, True)


class RakoSwitch(SwitchEntity):
    """Representation of a Rako Switch."""

    def __init__(self, bridge: RakoBridge, switch: python_rako.Switch) -> None:
        """Initialize a Rako Switch."""
        self.bridge = bridge
        self._switch = switch
        self._available = True

    @property
    def name(self) -> str:
        """Return the display name of this switch."""
        return f"{self._switch.room_title} - {self._switch.channel_name}"

    @property
    def unique_id(self) -> str:
        """Switch's unique ID."""
        return create_unique_id(
            self.bridge.mac, self._switch.room_id, self._switch.channel_id
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await self.bridge.register_for_state_updates(self)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await self.bridge.deregister_for_state_updates(self)


class RakoRoomSwitch(RakoSwitch):
    """Representation of a Rako Room Switch."""

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._switch.state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        try:
            await self.bridge.set_room_scene(self._switch.room_id, 255)
        except (RakoBridgeError, asyncio.TimeoutError):
            self._available = False

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        try:
            await self.bridge.set_room_scene(self._switch.room_id, 0)
        except (RakoBridgeError, asyncio.TimeoutError):
            self._available = False


class RakoChannelSwitch(RakoSwitch):
    """Representation of a Rako Channel Switch."""

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._switch.state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        try:
            await self.bridge.set_channel_brightness(
                self._switch.room_id, self._switch.channel_id, 255
            )
        except (RakoBridgeError, asyncio.TimeoutError):
            self._available = False

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        try:
            await self.bridge.set_channel_brightness(
                self._switch.room_id, self._switch.channel_id, 0
            )
        except (RakoBridgeError, asyncio.TimeoutError):
            self._available = False
