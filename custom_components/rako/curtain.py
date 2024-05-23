"""Platform for curtain integration."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import python_rako
from python_rako.exceptions import RakoBridgeError

from homeassistant.components.cover import CoverEntity, SUPPORT_OPEN, SUPPORT_CLOSE, SUPPORT_STOP
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
    """Set up the curtain platform from a config entry."""
    rako_domain_entry_data: RakoDomainEntryData = hass.data[DOMAIN][entry.unique_id]
    bridge = rako_domain_entry_data["rako_bridge_client"]

    hass_curtains: list[Entity] = []
    session = async_get_clientsession(hass)

    async for curtain in bridge.discover_curtains(session):
        hass_curtain = RakoCurtain(bridge, curtain)
        hass_curtains.append(hass_curtain)

    async_add_entities(hass_curtains, True)


class RakoCurtain(CoverEntity):
    """Representation of a Rako Curtain."""

    def __init__(self, bridge: RakoBridge, curtain: python_rako.Curtain) -> None:
        """Initialize a RakoCurtain."""
        self.bridge = bridge
        self._curtain = curtain
        self._available = True

    @property
    def name(self) -> str:
        """Return the display name of this curtain."""
        return self._curtain.name

    @property
    def unique_id(self) -> str:
        """Curtain's unique ID."""
        return create_unique_id(self.bridge.mac, self._curtain.room_id, self._curtain.channel_id)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def is_opening(self) -> bool:
        """Return if the curtain is opening."""
        return self._curtain.is_opening

    @property
    def is_closing(self) -> bool:
        """Return if the curtain is closing."""
        return self._curtain.is_closing

    @property
    def is_closed(self) -> bool:
        """Return if the curtain is closed."""
        return self._curtain.is_closed

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the curtain."""
        try:
            await self._curtain.open()
        except (RakoBridgeError, asyncio.TimeoutError):
            if self._available:
                _LOGGER.error("An error occurred while opening the Rako Curtain")
            self._available = False

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the curtain."""
        try:
            await self._curtain.close()
        except (RakoBridgeError, asyncio.TimeoutError):
            if self._available:
                _LOGGER.error("An error occurred while closing the Rako Curtain")
            self._available = False

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the curtain."""
        try:
            await self._curtain.stop()
        except (RakoBridgeError, asyncio.TimeoutError):
            if self._available:
                _LOGGER.error("An error occurred while stopping the Rako Curtain")
            self._available = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Rako Curtain."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Rako",
            "via_device": (DOMAIN, self.bridge.mac),
        }
