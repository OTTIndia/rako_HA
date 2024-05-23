"""Platform for switch integration."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import python_rako
from python_rako.exceptions import RakoBridgeError

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo, Entity
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
    """Set up the switch platform from a config entry."""
    rako_domain_entry_data: RakoDomainEntryData = hass.data[DOMAIN][entry.unique_id]
    bridge = rako_domain_entry_data["rako_bridge_client"]

    hass_switches: list[Entity] = []
    session = async_get_clientsession(hass)

    async for switch in bridge.discover_switches(session):
        hass_switch = RakoSwitch(bridge, switch)
        hass_switches.append(hass_switch)

    async_add_entities(hass_switches, True)


class RakoSwitch(SwitchEntity):
    """Representation of a Rako Switch."""

    def __init__(self, bridge: RakoBridge, switch: python_rako.Switch) -> None:
        """Initialize a RakoSwitch."""
        self.bridge = bridge
        self._switch = switch
        self._available = True

    @property
    def name(self) -> str:
        """Return the display name of this switch."""
        return self._switch.name

    @property
    def unique_id(self) -> str:
        """Switch's unique ID."""
        return create_unique_id(self.bridge.mac, self._switch.room_id, self._switch.channel_id)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._switch.state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        try:
            await self._switch.turn_on()
        except (RakoBridgeError, asyncio.TimeoutError):
            if self._available:
                _LOGGER.error("An error occurred while turning on the Rako Switch")
            self._available = False

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        try:
            await self._switch.turn_off()
        except (RakoBridgeError, asyncio.TimeoutError):
            if self._available:
                _LOGGER.error("An error occurred while turning off the Rako Switch")
            self._available = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Rako Switch."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Rako",
            "via_device": (DOMAIN, self.bridge.mac),
        }
