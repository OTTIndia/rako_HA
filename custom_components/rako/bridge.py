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
from .switch import RakoSwitch  # Import the RakoSwitch class
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
    def _switch_map(self) -> dict[str, RakoSwitch]:
        rako_domain_entry_data: RakoDomainEntryData = self.hass.data[DOMAIN][self.mac]
        return rako_domain_entry_data["rako_switch_map"]

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

    def _add_listening_light(self, light: RakoLight) -> None:
        light_map = self._light_map
        light_map[light.unique_id] = light

    def _add_listening_switch(self, switch: RakoSwitch) -> None:
        switch_map = self._switch_map
        switch_map[switch.unique_id] = switch

    def _remove_listening_light(self, light: RakoLight) -> None:
        light_map = self._light_map
        if light.unique_id in light_map:
            del light_map[light.unique_id]

    def _remove_listening_switch(self, switch: RakoSwitch) -> None:
        switch_map = self._switch_map
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
        """Register an entity to listen for state updates."""
        if isinstance(entity, RakoLight):
            self._add_listening_light(entity)
        elif isinstance(entity, RakoSwitch):
            self._add_listening_switch(entity)

        if len(self._light_map) + len(self._switch_map) == 1:
            await self.listen_for_state_updates()

    async def deregister_for_state_updates(self, entity) -> None:
        """Deregister an entity from listening for state updates."""
        if isinstance(entity, RakoLight):
            self._remove_listening_light(entity)
        elif isinstance(entity, RakoSwitch):
            self._remove_listening_switch(entity)

        if not self._light_map and not self._switch_map:
            await self.stop_listening_for_state_updates()
