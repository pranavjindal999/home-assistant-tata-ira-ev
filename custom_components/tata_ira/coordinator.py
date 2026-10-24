"""Poll battery, charging, air conditioning, and lock state for one Tata EV."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IraAuthError, IraClient, IraConnectionError, IraError
from .parser import VehicleStatus
from .const import CONF_REFRESH_TOKEN, DOMAIN, KEEP_CONNECTED_INTERVAL, POLL_INTERVAL

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
        self._connect_unsub: Callable[[], None] | None = None

    async def async_set_air_conditioning(self, on: bool) -> None:
        """Start the air conditioner for the saved duration, or stop it."""
        try:
            rotated = await self.client.async_set_air_conditioning(on, self.ac_minutes)
        except (IraAuthError, IraConnectionError, IraError) as err:
            raise UpdateFailed(str(err) or err.__class__.__name__) from err
        self._store_refresh_token(rotated)
        if self.data is not None:
            self.async_set_updated_data(replace(self.data, ac_on=on))

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

    async def async_set_engine(self, on: bool) -> None:
        """Start the car for the saved duration, or stop it."""
        try:
            rotated = await self.client.async_set_engine(on, self.ac_minutes)
        except (IraAuthError, IraConnectionError, IraError) as err:
            raise UpdateFailed(str(err) or err.__class__.__name__) from err
        self._store_refresh_token(rotated)
        if self.data is not None:
            self.async_set_updated_data(replace(self.data, engine_on=on))

    async def async_honk(self) -> None:
        """Sound the horn."""
        try:
            rotated = await self.client.async_honk()
        except (IraAuthError, IraConnectionError, IraError) as err:
            raise UpdateFailed(str(err) or err.__class__.__name__) from err
        self._store_refresh_token(rotated)

    async def _async_set_switch(
        self, on: bool, on_command: str, off_command: str, field: str
    ) -> None:
        try:
            rotated = await self.client.async_set_switch(
                on, on_command, off_command, field
            )
        except (IraAuthError, IraConnectionError, IraError) as err:
            raise UpdateFailed(str(err) or err.__class__.__name__) from err
        self._store_refresh_token(rotated)
        if self.data is not None:
            self.async_set_updated_data(replace(self.data, **{field: on}))

    async def async_set_locked(self, locked: bool) -> None:
        """Lock or unlock the car."""
        try:
            rotated = await self.client.async_set_locked(locked)
        except (IraAuthError, IraConnectionError, IraError) as err:
            raise UpdateFailed(str(err) or err.__class__.__name__) from err
        self._store_refresh_token(rotated)
        if self.data is not None:
            self.async_set_updated_data(replace(self.data, locked=locked))

    def async_start_connection(self) -> None:
        """Keep the car's command link awake while Home Assistant is running."""
        if self._connect_unsub is not None:
            return
        self._connect_unsub = async_track_time_interval(
            self.hass, self._async_keep_connected, KEEP_CONNECTED_INTERVAL
        )
        self.hass.async_create_task(self._async_keep_connected(datetime.now()))

    def async_stop_connection(self) -> None:
        """Stop keeping the command link awake."""
        if self._connect_unsub is not None:
            self._connect_unsub()
            self._connect_unsub = None

    async def _async_keep_connected(self, _now: datetime) -> None:
        try:
            connected, rotated = await self.client.async_keep_connected()
        except IraAuthError:
            self.connected = False
            self._request_reauth()
        except (IraConnectionError, IraError) as err:
            self.connected = False
            _LOGGER.debug("The car command link is not awake: %s", err)
        else:
            self.connected = connected
            self._store_refresh_token(rotated)
        self.async_update_listeners()

    async def _async_update_data(self) -> VehicleStatus:
        try:
            status, rotated = await self.client.async_vehicle_status()
        except IraAuthError as err:
            self._request_reauth()
            raise UpdateFailed(str(err) or err.__class__.__name__) from err
        except (IraConnectionError, IraError) as err:
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
