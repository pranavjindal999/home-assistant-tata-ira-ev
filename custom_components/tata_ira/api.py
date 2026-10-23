"""Read battery and charging status from the iRA.ev service."""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

import aiohttp

from .const import (
    API_HOST,
    APP_VERSION,
    CLIENT_ID,
    CLIENT_SECRET,
    COMMAND_PATH,
    HEALTH_PATH,
    REFRESH_PATH,
    STATE_PATH,
)
from .parser import (
    VehicleStatus,
    ac_command_body,
    parse_air_conditioning,
    parse_refresh_tokens,
    parse_vehicle_health,
)

_LOGGER = logging.getLogger(__name__)


class IraError(Exception):
    """The iRA.ev service could not be read."""


class IraAuthError(IraError):
    """The saved session was rejected."""


class IraConnectionError(IraError):
    """The iRA.ev service could not be reached."""


class IraClient:
    """Session client for one Tata vehicle."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        refresh_token: str,
        vehicle_id: str,
        api_key: str,
    ) -> None:
        """Store the session values Home Assistant collected."""
        self._session = session
        self.refresh_token = refresh_token
        self._vehicle_id = vehicle_id
        self._api_key = api_key

    async def async_vehicle_status(self) -> tuple[VehicleStatus, str | None]:
        """Refresh the session and return battery and charging status.

        The second value is a replacement refresh token when the service rotates it.
        """
        access_token, rotated = await self._async_refresh()
        status = await self._async_health(access_token)
        try:
            ac_on = await self._async_air_conditioning(access_token)
        except IraError as err:
            _LOGGER.debug("Air conditioning state was not available: %s", err)
        else:
            status = VehicleStatus(
                status.battery_percent,
                status.charging,
                status.charge_minutes_remaining,
                ac_on,
            )
        return status, rotated

    async def async_set_air_conditioning(
        self, on: bool, minutes: int
    ) -> str | None:
        """Start the air conditioner for a number of minutes, or stop it."""
        access_token, rotated = await self._async_refresh()
        command, body = ac_command_body(on, minutes, str(uuid4()))
        await self._async_request(
            "POST",
            COMMAND_PATH,
            json_body=body,
            headers={
                **self._vehicle_headers(access_token),
                "command-name": command,
                "X-Request-ID": str(uuid4()),
                "Accept": "application/json",
                "Cache-Control": "no-cache, no-store",
            },
        )
        return rotated

    async def _async_refresh(self) -> tuple[str, str | None]:
        body = {"refreshToken": self.refresh_token}
        payload = await self._async_request(
            "POST",
            REFRESH_PATH,
            json_body=body,
            headers={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "App-Version": APP_VERSION,
                "x-api-key": self._api_key,
            },
        )
        access_token, rotated = parse_refresh_tokens(payload)
        if not access_token:
            raise IraAuthError("The session refresh did not return an access token")
        if rotated and rotated != self.refresh_token:
            self.refresh_token = rotated
            return access_token, rotated
        return access_token, None

    async def _async_health(self, access_token: str) -> VehicleStatus:
        payload = await self._async_request(
            "GET",
            HEALTH_PATH,
            headers=self._vehicle_headers(access_token),
        )
        return parse_vehicle_health(payload)

    async def _async_air_conditioning(self, access_token: str) -> bool | None:
        payload = await self._async_request(
            "GET",
            STATE_PATH,
            headers=self._vehicle_headers(access_token),
        )
        return parse_air_conditioning(payload)

    def _vehicle_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "client_id": CLIENT_ID,
            "vehicleId": self._vehicle_id,
            "x-api-key": self._api_key,
            "App-Version": APP_VERSION,
        }

    async def _async_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            async with self._session.request(
                method,
                f"{API_HOST}{path}",
                headers=headers,
                json=json_body,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status in (401, 403):
                    raise IraAuthError("iRA.ev rejected this session")
                if response.status >= 400:
                    raise IraError(f"iRA.ev returned HTTP {response.status}")
                payload = await response.json(content_type=None)
        except (IraError, IraAuthError):
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise IraConnectionError("Cannot reach the iRA.ev service") from err
        if not isinstance(payload, dict):
            raise IraError("iRA.ev returned an unexpected response")
        return payload
