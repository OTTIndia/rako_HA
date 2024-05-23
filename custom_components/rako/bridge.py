"""Module representing a Rako Bridge."""
from __future__ import annotations

import asyncio
from asyncio import Task
import logging

from python_rako.bridge import Bridge
from python_rako.helpers import convert_to_brightness, get_dg_listener
from python_rako.model import ChannelStatusMessage, SceneStatusMessage, StatusMessage

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .curtain import RakoCurtain
from .rgbw_switch import RakoRGBWSwitch
from .light import RakoLight
from .model import RakoDomainEntryData
from .util import create_unique_id

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
    def _curtain_map(self) -> dict[str, RakoCurtain]:
        rako_domain_entry_data: RakoDomainEntryData = self.hass.data[DOMAIN][self.mac]
        return rako_domain_entry_data["rako_curtain_map"]

    @property
    def _rgbw_switch_map(self) -> dict[str, RakoRGBWSwitch]:
        rako_domain_entry_data: RakoDomainEntryData = self.hass.data[DOMAIN][self.mac]
        return rako_domain_entry_data["rako_rgbw_switch_map"]

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

    def get_listening_curtain(self, curtain_unique_id: str) -> RakoCurtain | None:
        """Return the Curtain, if listening."""
        curtain_map = self._curtain_map
        return curtain_map.get(curtain_unique_id)

    def get_listening_rgbw_switch(self, switch_unique_id: str) -> RakoRGBWSwitch | None:
        """Return the RGBW Switch, if listening."""
        switch_map = self._rgbw_switch_map
        return switch_map.get(switch_unique_id)

    def _add_listening_light(self, light: RakoLight) -> None:
        light_map = self._light_map
        light_map[light.unique_id] = light

    def _add_listening_curtain(self, curtain: RakoCurtain) -> None:
        curtain_map = self._curtain_map
        curtain_map[curtain.unique_id] = curtain

    def _add_listening_rgbw_switch(self, switch: RakoRGBWSwitch) -> None:
        switch_map = self._rgbw_switch_map
        switch_map[switch.unique_id] = switch

    def _remove_listening_light(self, light: RakoLight) -> None:
        light_map = self._light_map
        if light.unique_id in light_map:
            del light_map[light.unique_id]

    def _remove_listening_curtain(self, curtain: RakoCurtain) -> None:
        curtain_map = self._curtain_map
        if curtain.unique_id in curtain_map:
            del curtain_map[curtain.unique_id]

    def _remove_listening_rgbw_switch(self, switch: RakoRGBWSwitch) -> None:
        switch_map = self._rgbw_switch_map
        if switch.unique_id in switch_map:
            del switch_map[switch.unique_id]

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

    async def register_for_state_updates(self, entity) -> None:
        """Register an entity (light, curtain, or switch) to listen for state updates."""
        if isinstance(entity, RakoLight):
            self._add_listening_light(entity)
        elif isinstance(entity, RakoCurtain):
            self._add_listening_curtain(entity)
        elif isinstance(entity, RakoRGBWSwitch):
            self._add_listening_rgbw_switch(entity)

        if len(self._light_map) == 1 or len(self._curtain_map) == 1 or len(self._rgbw_switch_map) == 1:
            await self.listen_for_state_updates()

    async def deregister_for_state_updates(self, entity) -> None:
        """Deregister an entity (light, curtain, or switch) to listen for state updates."""
        if isinstance(entity, RakoLight):
            self._remove_listening_light(entity)
        elif isinstance(entity, RakoCurtain):
            self._remove_listening_curtain(entity)
        elif isinstance(entity, RakoRGBWSwitch):
            self._remove_listening_rgbw_switch(entity)

        if not self._light_map and not self._curtain_map and not self._rgbw_switch_map:
            await self.stop_listening_for_state_updates()

    async def close_curtain(self):
        """Implement the logic to close the curtain."""
        _LOGGER.debug("Closing curtain")
        # Add your implementation to close the curtain

    async def open_curtain(self):
        """Implement the logic to open the curtain."""
        _LOGGER.debug("Opening curtain")
        # Add your implementation to open the curtain

    async def turn_on_rgbw(self):
        """Implement the logic to turn on the RGBW switch."""
        _LOGGER.debug("Turning on RGBW switch")
        # Add your implementation to turn on the RGBW switch

    async def turn_off_rgbw(self):
        """Implement the logic to turn off the RGBW switch."""
        _LOGGER.debug("Turning off RGBW switch")
        # Add your implementation to turn off the RGBW switch

    async def turn_on_light(self, brightness: int):
        """Implement the logic to turn on the light with a given brightness."""
        _LOGGER.debug("Turning on light with brightness: %s", brightness)
        # Add your implementation to turn on the light

    async def turn_off_light(self):
        """Implement the logic to turn off the light."""
        _LOGGER.debug("Turning off light")
        # Add your implementation to turn off the light


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


async def listen_for_state_updates(bridge: RakoBridge) -> None:
    """Listen for state updates worker method."""
    async with get_dg_listener(bridge.port) as listener:
        while True:
            message = await bridge.next_pushed_message(listener)
            if message and isinstance(message, StatusMessage):
                _state_update(bridge, message)
