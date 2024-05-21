"""Platform for switch integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import python_rako
from python_rako.exceptions import RakoBridgeError

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .util import create_unique_id

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Rako switches from a config entry."""
    rako_domain_entry_data = hass.data[DOMAIN][entry.unique_id]
    bridge = rako_domain_entry_data["rako_bridge_client"]

    hass_switches: list[Entity] = []

    async for switch in bridge.discover_switches():
        hass_switch = RakoSwitch(bridge, switch)
        hass_switches.append(hass_switch)

    async_add_entities(hass_switches, True)

class RakoSwitch(SwitchEntity):
    """Representation of a Rako Switch."""

    def __init__(self, bridge: RakoBridge, switch: python_rako.Switch) -> None:
        """Initialize a RakoSwitch."""
        self.bridge = bridge
        self._switch = switch
        self._state = self._init_get_state_from_cache()
        self._available = True

    @property
    def name(self) -> str:
        """Return the display name of this switch."""
        return self._switch.name

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._state

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def should_poll(self) -> bool:
        """No need to poll. Entity pushes its state to HA."""
        return False

    def _init_get_state_from_cache(self) -> bool:
        # Implement cache retrieval logic here
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self.bridge.turn_on_switch(self._switch.id)
            self._state = True
            self.async_write_ha_state()
        except (RakoBridgeError, asyncio.TimeoutError):
            _LOGGER.error("An error occurred while turning on the Rako Switch")
            self._available = False

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self.bridge.turn_off_switch(self._switch.id)
            self._state = False
            self.async_write_ha_state()
        except (RakoBridgeError, asyncio.TimeoutError):
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
