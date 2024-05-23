"""The Rako integration."""
import logging
from typing import Any

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_PORT,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .bridge import RakoBridge
from .const import DOMAIN
from .model import RakoDomainEntryData
from .switch import RakoSwitch  # Import RakoSwitch class

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Set up Rako from a config entry."""
    rako_bridge = RakoBridge(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        name=entry.data[CONF_NAME],
        mac=entry.data[CONF_MAC],
        entry_id=entry.entry_id,
        hass=hass,
    )

    device_registry = await dr.async_get_registry(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, entry.data[CONF_MAC])},
        identifiers={(DOMAIN, entry.data[CONF_MAC])},
        manufacturer="Rako",
        name=entry.data[CONF_NAME],
    )

    hass.data.setdefault(DOMAIN, {})
    rako_domain_entry_data: RakoDomainEntryData = {
        "rako_bridge_client": rako_bridge,
        "rako_light_map": {},
        "rako_listener_task": None,
    }
    hass.data[DOMAIN][rako_bridge.mac] = rako_domain_entry_data

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, LIGHT_DOMAIN)
    )

    async_add_entities(await async_create_switch_entities(rako_bridge), update_before_add=True)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, LIGHT_DOMAIN)

    del hass.data[DOMAIN][entry.unique_id]
    if not hass.data[DOMAIN]:
        del hass.data[DOMAIN]

    return True


async def async_create_switch_entities(bridge: RakoBridge):
    """Create switch entities for the Rako bridge."""
    switches = []

    for room in bridge.rooms:
        for channel in room.channels:
            switches.append(RakoChannelSwitch(bridge, room, channel))

    return switches


class RakoChannelSwitch(RakoSwitch):
    """Representation of a Rako Channel Switch."""

    def __init__(self, bridge: RakoBridge, room, channel) -> None:
        """Initialize a Rako Channel Switch."""
        super().__init__(bridge, room, channel)

    @property
    def name(self) -> str:
        """Return the display name of this switch."""
        return f"{self._room.name} - Channel {self._channel.number}"

    @property
    def unique_id(self) -> str:
        """Switch's unique ID."""
        return f"rako_switch_{self._room.id}_{self._channel.number}"

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

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Rako Switch."""
        return {
            "identifiers": {(DOMAIN, self._room.id)},
            "name": self.name,
            "manufacturer": "Rako",
            "via_device": (DOMAIN, self._bridge.mac),
        }
