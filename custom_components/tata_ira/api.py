"""Read battery and charging status from the iRA.ev service."""

from __future__ import annotations

from typing import Any

import aiohttp

from .const import (
    API_HOST,
    APP_VERSION,
    CLIENT_ID,
    CLIENT_SECRET,
    HEALTH_PATH,
    REFRESH_PATH,
)
from .parser import VehicleStatus, parse_vehicle_health


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
        return status, rotated

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
        results = payload.get("results") or {}
        access_token = results.get("accessToken")
        if not access_token:
            raise IraAuthError("The session refresh did not return an access token")
        rotated = results.get("refreshToken")
        if isinstance(rotated, str) and rotated and rotated != self.refresh_token:
            self.refresh_token = rotated
            return access_token, rotated
        return access_token, None

    async def _async_health(self, access_token: str) -> VehicleStatus:
        payload = await self._async_request(
            "GET",
            HEALTH_PATH,
            headers={
                "Authorization": f"Bearer {access_token}",
                "client_id": CLIENT_ID,
                "vehicleId": self._vehicle_id,
                "x-api-key": self._api_key,
                "App-Version": APP_VERSION,
            },
        )
        return parse_vehicle_health(payload)

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
