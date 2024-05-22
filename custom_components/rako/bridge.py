from __future__ import annotations

import asyncio
from asyncio import Task
import logging

from python_rako.bridge import Bridge
from python_rako.helpers import convert_to_brightness, get_dg_listener
from python_rako.model import ChannelStatusMessage, SceneStatusMessage, StatusMessage

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .light import RakoLight
from .switch import RakoSwitch
from .cover import RakoCover
from .rgbw import RakoRGBW
from .model import RakoDomainEntryData

_LOGGER = logging.getLogger(__name__)

class RakoBridge(Bridge):
    """Represents a Rako Bridge."""

    def __init__(
        self,
        host: str,
        port: int,
        name: str,
        mac: str,
        entry_id: str,
        hass: HomeAssistant,
    ) -> None:
        """Init subclass of python_rako Bridge."""
        super().__init__(host, port, name, mac)
        self.entry_id = entry_id
        self.hass = hass

    @property
    def _light_map(self) -> dict[str, RakoLight]:
        rako_domain_entry_data: RakoDomainEntryData = self.hass.data[DOMAIN][self.mac]
        return rako_domain_entry_data["rako_light_map"]

    @property
    def _switch_map(self) -> dict[str, RakoSwitch]:
        rako_domain_entry_data: RakoDomainEntryData = self.hass.data[DOMAIN][self.mac]
        return rako_domain_entry_data["rako_switch_map"]

    @property
    def _cover_map(self) -> dict[str, RakoCover]:
        rako_domain_entry_data: RakoDomainEntryData = self.hass.data[DOMAIN][self.mac]
        return rako_domain_entry_data["rako_cover_map"]

    @property
    def _rgbw_map(self) -> dict[str, RakoRGBW]:
        rako_domain_entry_data: RakoDomainEntryData = self.hass.data[DOMAIN][self.mac]
        return rako_domain_entry_data["rako_rgbw_map"]

    @property
    def _listener_task(self) -> Task | None:
        rako_domain_entry_data: RakoDomainEntryData = self.hass.data[DOMAIN][self.mac]
        return rako_domain_entry_data["rako_listener_task"]

    @_listener_task.setter
    def _listener_task(self, task: Task) -> None:
        rako_domain_entry_data: RakoDomainEntryData = self.hass.data[DOMAIN][self.mac]
        rako_domain_entry_data["rako_listener_task"] = task

    def get_listening_light(self, light_unique_id: str) -> RakoLight | None:
        """Return the Light, if listening."""
        light_map = self._light_map
        return light_map.get(light_unique_id)

    def get_listening_switch(self, switch_unique_id: str) -> RakoSwitch | None:
        """Return the Switch, if listening."""
        switch_map = self._switch_map
        return switch_map.get(switch_unique_id)

    def get_listening_cover(self, cover_unique_id: str) -> RakoCover | None:
        """Return the Cover, if listening."""
        cover_map = self._cover_map
        return cover_map.get(cover_unique_id)

    def get_listening_rgbw(self, rgbw_unique_id: str) -> RakoRGBW | None:
        """Return the RGBW light, if listening."""
        rgbw_map = self._rgbw_map
        return rgbw_map.get(rgbw_unique_id)

    def _add_listening_light(self, light: RakoLight) -> None:
        light_map = self._light_map
        light_map[light.unique_id] = light

    def _add_listening_switch(self, switch: RakoSwitch) -> None:
        switch_map = self._switch_map
        switch_map[switch.unique_id] = switch

    def _add_listening_cover(self, cover: RakoCover) -> None:
        cover_map = self._cover_map
        cover_map[cover.unique_id] = cover

    def _add_listening_rgbw(self, rgbw: RakoRGBW) -> None:
        rgbw_map = self._rgbw_map
        rgbw_map[rgbw.unique_id] = rgbw

    def _remove_listening_light(self, light: RakoLight) -> None:
        light_map = self._light_map
        if light.unique_id in light_map:
            del light_map[light.unique_id]

    def _remove_listening_switch(self, switch: RakoSwitch) -> None:
        switch_map = self._switch_map
        if switch.unique_id in switch_map:
            del switch_map[switch.unique_id]

    def _remove_listening_cover(self, cover: RakoCover) -> None:
        cover_map = self._cover_map
        if cover.unique_id in cover_map:
            del cover_map[cover.unique_id]

    def _remove_listening_rgbw(self, rgbw: RakoRGBW) -> None:
        rgbw_map = self._rgbw_map
        if rgbw.unique_id in rgbw_map:
            del rgbw_map[rgbw.unique_id]

    async def listen_for_state_updates(self) -> None:
        """Background task to listen for state updates."""
        self._listener_task: Task = asyncio.create_task(
            listen_for_state_updates(self), name=f"rako_{self.mac}_listener_task"
        )

    async def stop_listening_for_state_updates(self) -> None:
        """Background task to stop listening for state updates."""
        if listener_task := self._listener_task:
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

    async def register_for_state_updates(self, entity: RakoLight | RakoSwitch | RakoCover | RakoRGBW) -> None:
        """Register a light, switch, cover, or RGBW light to listen for state updates."""
        if isinstance(entity, RakoLight):
            self._add_listening_light(entity)
        elif isinstance(entity, RakoSwitch):
            self._add_listening_switch(entity)
        elif isinstance(entity, RakoCover):
            self._add_listening_cover(entity)
        elif isinstance(entity, RakoRGBW):
            self._add_listening_rgbw(entity)

        if len(self._light_map) == 1 and len(self._switch_map) == 0 and len(self._cover_map) == 0 and len(self._rgbw_map) == 0:
            await self.listen_for_state_updates()

    async def deregister_for_state_updates(self, entity: RakoLight | RakoSwitch | RakoCover | RakoRGBW) -> None:
        """Deregister a light, switch, cover, or RGBW light to listen for state updates."""
        if isinstance(entity, RakoLight):
            self._remove_listening_light(entity)
        elif isinstance(entity, RakoSwitch):
            self._remove_listening_switch(entity)
        elif isinstance(entity, RakoCover):
            self._remove_listening_cover(entity)
        elif isinstance(entity, RakoRGBW):
            self._remove_listening_rgbw(entity)

        if not self._light_map and not self._switch_map and not self._cover_map and not self._rgbw_map:
            await self.stop_listening_for_state_updates()

    async def discover_lights(self, session):
        # Your existing implementation for discovering lights
        lights = []  # This should be a list of RakoLight objects
        return lights

    async def discover_switches(self):
        # Placeholder implementation. Replace with actual logic.
        switches = []  # This should be a list of switch objects
        return switches

    async def discover_covers(self):
        # Placeholder implementation. Replace with actual logic.
        covers = []  # This should be a list of cover objects
        return covers

    async def discover_rgbw_lights(self):
        # Placeholder implementation. Replace with actual logic.
        rgbw_lights = []  # This should be a list of RGBW light objects
        return rgbw_lights

    async def turn_on_light(self, light_id):
        # Implement logic to turn on light
        pass

    async def turn_off_light(self, light_id):
        # Implement logic to turn off light
        pass

    async def turn_on_switch(self, switch_id):
        # Implement logic to turn on switch
        pass

    async def turn_off_switch(self, switch_id):
        # Implement logic to turn off switch
        pass

    async def open_cover(self, cover_id):
        # Implement logic to open cover
        pass

    async def close_cover(self, cover_id):
        # Implement logic to close cover
        pass

    async def set_rgbw(self, rgbw_id, red, green, blue, white):
        # Implement logic to set RGBW light
        pass


def _state_update(bridge: RakoBridge, status_message: StatusMessage) -> None:
    light_unique_id = create_unique_id(
        bridge.mac, status_message.room, status_message.channel
    )
    brightness = 0
    if isinstance(status_message, ChannelStatusMessage):
        brightness = status_message.brightness
    elif isinstance(status_message, SceneStatusMessage):
        for _channel, _brightness in bridge.level_cache.get_channel_levels(
            status_message.room, status_message.scene
        ):
            _msg = ChannelStatusMessage(status_message.room, _channel, _brightness)
            _state_update(bridge, _msg)
        brightness = convert_to_brightness(status_message.scene)

    listening_light = bridge.get_listening_light(light_unique_id)
    if listening_light:
        listening_light.brightness = brightness
    else:
        _LOGGER.debug("Light not listening: %s", status_message)

    switch_unique_id = create_unique_id(
        bridge.mac, status_message.room, status_message.channel
    )
    listening_switch = bridge.get_listening_switch(switch_unique_id)
    if listening_switch:
        listening_switch.is_on = brightness > 0
    else:
        _LOGGER.debug("Switch not listening: %s", status_message)

    cover_unique_id = create_unique_id(
        bridge.mac, status_message.room, status_message.channel
    )
    listening_cover = bridge.get_listening_cover(cover_unique_id)
    if listening_cover:
        listening_cover.is_open = brightness > 0
    else:
        _LOGGER.debug("Cover not listening: %s", status_message)

    rgbw_unique_id = create_unique_id(
        bridge.mac, status_message.room, status_message.channel
    )
    listening_rgbw = bridge.get_listening_rgbw(rgbw_unique_id)
    if listening_rgbw:
        listening_rgbw.set_brightness(brightness)
    else:
        _LOGGER.debug("RGBW light not listening: %s", status_message)


async def listen_for_state_updates(bridge: RakoBridge) -> None:
    """Listen for state updates worker method."""
    async with get_dg_listener(bridge.port) as listener:
        while True:
            message = await bridge.next_pushed_message(listener)
            if message and isinstance(message, StatusMessage):
                _state_update(bridge, message)
