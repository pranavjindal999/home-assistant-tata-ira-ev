"""Poll battery, charging, air conditioning, and lock state for one Tata EV."""

from __future__ import annotations

import logging
from dataclasses import replace

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IraAuthError, IraClient, IraConnectionError, IraError
from .parser import VehicleStatus
from .const import CONF_REFRESH_TOKEN, DOMAIN, POLL_INTERVAL

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

    async def async_set_air_conditioning(self, on: bool) -> None:
        """Start the air conditioner for the saved duration, or stop it."""
        try:
            rotated = await self.client.async_set_air_conditioning(on, self.ac_minutes)
        except (IraAuthError, IraConnectionError, IraError) as err:
            raise UpdateFailed(str(err) or err.__class__.__name__) from err
        self._store_refresh_token(rotated)
        if self.data is not None:
            self.async_set_updated_data(replace(self.data, ac_on=on))

    async def async_set_locked(self, locked: bool) -> None:
        """Lock or unlock the car."""
        try:
            rotated = await self.client.async_set_locked(locked)
        except (IraAuthError, IraConnectionError, IraError) as err:
            raise UpdateFailed(str(err) or err.__class__.__name__) from err
        self._store_refresh_token(rotated)
        if self.data is not None:
            self.async_set_updated_data(replace(self.data, locked=locked))

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
