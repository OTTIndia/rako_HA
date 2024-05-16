"""The Rako integration."""
import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Rako component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Rako from a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "light")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    await asyncio.wait([
        hass.config_entries.async_forward_entry_unload(entry, "light")
    ])
    return True
