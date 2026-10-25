"""Tata iRA.ev battery and charging status for Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path

from aiohttp import web
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later

from .api import IraClient
from .const import CONF_API_KEY, CONF_REFRESH_TOKEN, CONF_VEHICLE_ID, DOMAIN
from .coordinator import IraCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.LOCK,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]

CARD_PATH = "/tata_ira/tata-ira-card.js"
_CARD_FILE = Path(__file__).parent / "www" / "tata-ira-card.js"


class TataIraCardView(HomeAssistantView):
    """Serve the dashboard card without letting the browser keep an old copy."""

    url = CARD_PATH
    name = "api:tata_ira:card"
    requires_auth = False

    async def get(self, request: web.Request) -> web.FileResponse:
        """Return the card file that is currently on disk."""
        response = web.FileResponse(_CARD_FILE)
        response.headers["Cache-Control"] = "no-cache"
        return response


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Serve the dashboard card."""
    await _async_register_card(hass)
    return True


async def _async_register_card(hass: HomeAssistant) -> None:
    """Publish the card file and add it to Lovelace."""
    store = hass.data.setdefault(DOMAIN, {})
    if not store.get("card_path"):
        hass.http.register_view(TataIraCardView())
        add_extra_js_url(hass, CARD_PATH)
        store["card_path"] = True
    try:
        await _async_register_lovelace_resource(hass, CARD_PATH)
    except Exception:
        _LOGGER.exception("Could not register the Tata iRA.ev dashboard card")


async def _async_register_lovelace_resource(
    hass: HomeAssistant, url: str, attempt: int = 0
) -> None:
    """Add the card as a dashboard module so the editor can find it."""
    lovelace = hass.data.get("lovelace")
    if lovelace is None or getattr(lovelace, "mode", None) != "storage":
        return
    resources = lovelace.resources
    if not resources.loaded:
        if attempt >= 10:
            _LOGGER.warning("Dashboard resources were not ready for the Tata iRA.ev card")
            return

        async_call_later(
            hass,
            2,
            lambda _now: hass.async_create_task(
                _async_register_lovelace_resource(hass, url, attempt + 1)
            ),
        )
        return
    path = url.split("?", 1)[0]
    for item in resources.async_items():
        if str(item.get("url", "")).split("?", 1)[0] != path:
            continue
        if item.get("url") != url:
            await resources.async_update_item(
                item["id"], {"res_type": "module", "url": url}
            )
        return
    await resources.async_create_item({"res_type": "module", "url": url})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Connect to the car and expose battery and charging sensors."""
    await _async_register_card(hass)
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
