"""The Rako integration."""
import logging

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .bridge import RakoBridge
from .const import DOMAIN
from .model import RakoDomainEntryData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Rako from a config entry."""
    rako_bridge = RakoBridge(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        name=entry.data[CONF_NAME],
        mac=entry.data[CONF_MAC],
        entry_id=entry.entry_id,
        hass=hass,
    )

    device_registry = await async_get_device_registry(hass)
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
        "rako_curtain_map": {},
        "rako_switch_map": {},
        "rako_rgbw_switch_map": {},
        "rako_listener_task": None,
    }
    hass.data[DOMAIN][entry.unique_id] = rako_domain_entry_data

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, LIGHT_DOMAIN)
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, COVER_DOMAIN)
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, SWITCH_DOMAIN)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, LIGHT_DOMAIN)
    await hass.config_entries.async_forward_entry_unload(entry, COVER_DOMAIN)
    await hass.config_entries.async_forward_entry_unload(entry, SWITCH_DOMAIN)

    del hass.data[DOMAIN][entry.unique_id]
    if not hass.data[DOMAIN]:
        del hass.data[DOMAIN]

    return True
