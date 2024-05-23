"""Platform for RGBW light integration."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import python_rako
from python_rako.exceptions import RakoBridgeError

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    LightEntity,
)
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
    """Set up the RGBW light platform from a config entry."""
    rako_domain_entry_data: RakoDomainEntryData = hass.data[DOMAIN][entry.unique_id]
    bridge = rako_domain_entry_data["rako_bridge_client"]

    hass_rgbws: list[Entity] = []
    session = async_get_clientsession(hass)

    async for rgbw in bridge.discover_rgbws(session):
        hass_rgbw = RakoRGBWLight(bridge, rgbw)
        hass_rgbws.append(hass_rgbw)

    async_add_entities(hass_rgbws, True)


class RakoRGBWLight(LightEntity):
    """Representation of a Rako RGBW Light."""

    def __init__(self, bridge: RakoBridge, rgbw: python_rako.RGBWLight) -> None:
        """Initialize a RakoRGBWLight."""
        self.bridge = bridge
        self._rgbw = rgbw
        self._brightness = self._init_get_brightness_from_cache()
        self._hs_color = self._init_get_color_from_cache()
        self._available = True

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._rgbw.name

    @property
    def unique_id(self) -> str:
        """Light's unique ID."""
        return create_unique_id(
            self.bridge.mac, self._rgbw.room_id, self._rgbw.channel_id
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def brightness(self) -> int:
        """Return the brightness of the light."""
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        """Set the brightness. Used when state is updated outside Home Assistant."""
        self._brightness = value
        self.async_write_ha_state()

    @property
    def hs_color(self) -> tuple[float, float]:
        """Return the color of the light."""
        return self._hs_color

    @hs_color.setter
    def hs_color(self, value: tuple[float, float]) -> None:
        """Set the color. Used when state is updated outside Home Assistant."""
        self._hs_color = value
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self.brightness > 0

    @property
    def should_poll(self) -> bool:
        """Entity pushes its state to HA."""
        return False

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        hs_color = kwargs.get(ATTR_HS_COLOR, self._hs_color)

        try:
            await self._rgbw.set_brightness_and_color(brightness, hs_color)
        except (RakoBridgeError, asyncio.TimeoutError):
            if self._available:
                _LOGGER.error("An error occurred while updating the Rako RGBW Light")
            self._available = False

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self.async_turn_on(brightness=0)

    def _init_get_brightness_from_cache(self) -> int:
        return self._rgbw.cached_brightness

    def _init_get_color_from_cache(self) -> tuple[float, float]:
        return self._rgbw.cached_color

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Rako RGBW Light."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Rako",
            "via_device": (DOMAIN, self.bridge.mac),
        }
