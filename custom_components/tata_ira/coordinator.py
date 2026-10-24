"""Poll battery, charging, air conditioning, and lock state for one Tata EV."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import replace
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IraAuthError, IraClient, IraConnectionError, IraError, transient_api_error
from .parser import VehicleStatus
from .const import (
    CONF_REFRESH_TOKEN,
    DOMAIN,
    KEEP_CONNECTED_INTERVAL,
    POLL_INTERVAL,
    RECONNECT_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class IraCoordinator(DataUpdateCoordinator[VehicleStatus]):
    """Battery percentage, charging, air conditioning, and lock state."""

    def __init__(
        self, hass: HomeAssistant, client: IraClient, entry: ConfigEntry
    ) -> None:
        """Poll the car every 30 seconds."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=POLL_INTERVAL,
        )
        self.client = client
        self.entry = entry
        self.ac_minutes = 10
        self.connected: bool | None = None
        self._connect_task: asyncio.Task[None] | None = None
        self._connect_stop = asyncio.Event()
        self._state_lock = asyncio.Lock()

    async def async_set_air_conditioning(self, on: bool) -> None:
        """Start the air conditioner for the saved duration, or stop it."""
        await self._async_run_command(
            lambda: self.client.async_set_air_conditioning(on, self.ac_minutes),
            "ac_on",
            on,
        )

    async def async_set_approach_lights(self, on: bool) -> None:
        """Turn the approach lights on or off."""
        await self._async_set_switch(
            on,
            "RemoteApproachOnCommand",
            "RemoteApproachOffCommand",
            "approach_lights",
        )

    async def async_set_headlights(self, on: bool) -> None:
        """Turn the headlights on or off."""
        await self._async_set_switch(
            on,
            "RemotePositionCommandLampOn",
            "RemotePositionCommandLampOff",
            "headlights",
        )

    async def async_set_hazard_lights(self, on: bool) -> None:
        """Turn the hazard lights on or off."""
        await self._async_set_switch(
            on,
            "RemoteHazardCommandLampOn",
            "RemoteHazardCommandLampOff",
            "hazard_lights",
        )

    async def async_honk(self) -> None:
        """Sound the horn."""
        await self._async_run_command(self.client.async_honk, None, None)

    async def _async_set_switch(
        self, on: bool, on_command: str, off_command: str, field: str
    ) -> None:
        await self._async_run_command(
            lambda: self.client.async_set_switch(on, on_command, off_command, field),
            field,
            on,
        )

    async def async_set_locked(self, locked: bool) -> None:
        """Lock or unlock the car."""
        await self._async_run_command(
            lambda: self.client.async_set_locked(locked),
            "locked",
            locked,
        )

    async def _async_run_command(
        self,
        action: Callable[[], Any],
        field: str | None,
        expected: bool | None,
    ) -> None:
        """Run a command, then keep the controls unchanged until the car reports it."""
        async with self._state_lock:
            try:
                rotated = await action()
            except (IraAuthError, IraConnectionError, IraError) as err:
                raise UpdateFailed(str(err) or err.__class__.__name__) from err
            self._store_refresh_token(rotated)
            self._adopt_link_state()
            if field is None or expected is None or self.data is None:
                return
            self.async_set_updated_data(replace(self.data, **{field: expected}))

    def async_start_connection(self) -> None:
        """Open the command link now and keep it awake."""
        if self._connect_task is not None:
            return
        self._connect_stop.clear()
        self._connect_task = self.hass.async_create_task(self._async_connection_loop())

    def async_stop_connection(self) -> None:
        """Stop keeping the command link awake."""
        self._connect_stop.set()
        if self._connect_task is not None:
            self._connect_task.cancel()
            self._connect_task = None

    async def _async_connection_loop(self) -> None:
        """Connect at startup, then keep retrying for as long as this runs."""
        failures = 0
        while not self._connect_stop.is_set():
            delay = RECONNECT_INTERVAL.total_seconds()
            try:
                _connected, rotated = await self.client.async_keep_connected()
            except asyncio.CancelledError:
                raise
            except IraAuthError:
                self._set_connected(False)
                self._request_reauth()
                return
            except Exception as err:
                failures += 1
                if isinstance(err, IraError) and not transient_api_error(err):
                    self._set_connected(False)
                _LOGGER.debug("Command link check failed: %s", err)
                delay = min(60, RECONNECT_INTERVAL.total_seconds() * failures)
            else:
                failures = 0
                self._store_refresh_token(rotated)
                self._set_connected(self.client.link_connected)
                if self.connected is True:
                    delay = KEEP_CONNECTED_INTERVAL.total_seconds()
            self.async_update_listeners()
            try:
                await asyncio.wait_for(self._connect_stop.wait(), timeout=delay)
            except TimeoutError:
                continue
            return

    def _set_connected(self, connected: bool | None) -> None:
        if connected is self.connected:
            return
        self.connected = connected
        if connected is True:
            _LOGGER.info("Car command link is connected")
        elif connected is False:
            _LOGGER.warning("Car command link is not connected; retrying")

    def _adopt_link_state(self) -> None:
        if self.client.link_connected is not None:
            self._set_connected(self.client.link_connected)

    async def _async_update_data(self) -> VehicleStatus:
        async with self._state_lock:
            return await self._async_fetch_status()

    async def _async_fetch_status(self) -> VehicleStatus:
        try:
            status, rotated = await self.client.async_vehicle_status()
        except IraAuthError as err:
            self._request_reauth()
            raise UpdateFailed(str(err) or err.__class__.__name__) from err
        except (IraConnectionError, IraError) as err:
            if self.data is not None and transient_api_error(err):
                _LOGGER.debug("Keeping the last car reading after %s", err)
                return self.data
            raise UpdateFailed(str(err) or err.__class__.__name__) from err
        self._store_refresh_token(rotated)
        return status

    def _request_reauth(self) -> None:
        entry_id = self.entry.entry_id
        for flow in self.hass.config_entries.flow.async_progress():
            context = flow.get("context") or {}
            if context.get("source") == "reauth" and context.get("entry_id") == entry_id:
                return
        self.entry.async_start_reauth(self.hass)

    def _store_refresh_token(self, rotated: str | None) -> None:
        if rotated and self.entry.data.get(CONF_REFRESH_TOKEN) != rotated:
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={**self.entry.data, CONF_REFRESH_TOKEN: rotated},
            )
