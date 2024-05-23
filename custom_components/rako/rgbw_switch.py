"""Platform for RGBW switch integration."""
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
    """Set up the RGBW switch platform from a config entry."""
    rako_domain_entry_data: RakoDomainEntryData = hass.data[DOMAIN][entry.unique_id]
    bridge = rako_domain_entry_data["rako_bridge_client"]

    hass_rgbw_switches: list[Entity] = []
    session = async_get_clientsession(hass)

    async for rgbw_switch in bridge.discover_rgbw_switches(session):
        hass_rgbw_switch = RakoRGBWSwitch(bridge, rgbw_switch)
        hass_rgbw_switches.append(hass_rgbw_switch)

    async_add_entities(hass_rgbw_switches, True)


class RakoRGBWSwitch(SwitchEntity):
    """Representation of a Rako RGBW Switch."""

    def __init__(self, bridge: RakoBridge, rgbw_switch: python_rako.RGBWSwitch) -> None:
        """Initialize a RakoRGBWSwitch."""
        self.bridge = bridge
        self._rgbw_switch = rgbw_switch
        self._is_on = self._init_get_state_from_cache()
        self._available = True

    @property
    def name(self) -> str:
        """Return the display name of this switch."""
        return self._rgbw_switch.name

    @property
    def unique_id(self) -> str:
        """Switch's unique ID."""
        return create_unique_id(
            self.bridge.mac, self._rgbw_switch.room_id, self._rgbw_switch.channel_id
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        try:
            await self.bridge.turn_on_rgbw()
            self._is_on = True
            self.async_write_ha_state()
        except (RakoBridgeError, asyncio.TimeoutError):
            if self._available:
                _LOGGER.error("An error occurred while turning on the Rako RGBW switch")
            self._available = False

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        try:
            await self.bridge.turn_off_rgbw()
            self._is_on = False
            self.async_write_ha_state()
        except (RakoBridgeError, asyncio.TimeoutError):
            if self._available:
                _LOGGER.error("An error occurred while turning off the Rako RGBW switch")
            self._available = False

    def _init_get_state_from_cache(self) -> bool:
        return self._rgbw_switch.cached_state

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Rako RGBW Switch."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Rako",
            "via_device": (DOMAIN, self.bridge.mac),
        }
