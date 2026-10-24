"""Tata iRA.ev battery and charging status for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IraClient
from .const import CONF_API_KEY, CONF_REFRESH_TOKEN, CONF_VEHICLE_ID, DOMAIN
from .coordinator import IraCoordinator

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.LOCK,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Connect to the car and expose battery and charging sensors."""
    client = IraClient(
        async_get_clientsession(hass),
        entry.data[CONF_REFRESH_TOKEN],
        entry.data[CONF_VEHICLE_ID],
        entry.data[CONF_API_KEY],
    )
    coordinator = IraCoordinator(hass, client, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    coordinator.async_start_connection()
    try:
        await coordinator.async_config_entry_first_refresh()
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        coordinator.async_stop_connection()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove the car sensors."""
    coordinator: IraCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is not None:
        coordinator.async_stop_connection()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
