"""Read battery and charging status from the iRA.ev service."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any
from uuid import uuid4

import aiohttp

from .const import (
    ACCESS_TOKEN_PATH,
    API_HOST,
    APP_API_KEY,
    APP_VERSION,
    CHECK_PHONE_PATH,
    CLIENT_ID,
    CLIENT_SECRET,
    COMMAND_PATH,
    HEALTH_PATH,
    PROFILE_PATH,
    REFRESH_PATH,
    STATE_PATH,
    VERIFY_OTP_PATH,
)
from .parser import (
    VehicleStatus,
    ac_command_body,
    lock_command_body,
    otp_verify_body,
    parse_air_conditioning,
    parse_code_verifier,
    parse_login_tokens,
    parse_ref_id,
    parse_refresh_tokens,
    parse_vehicle_health,
    parse_vehicle_ids,
    service_error,
)

_LOGGER = logging.getLogger(__name__)


class IraError(Exception):
    """The iRA.ev service could not be read."""


class IraAuthError(IraError):
    """The saved session was rejected."""

    def __init__(self, message: str, code: str | None = None) -> None:
        """Store the service error code when one was returned."""
        super().__init__(message)
        self.code = code


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
            status = replace(status, ac_on=ac_on)
        return status, rotated

    async def async_set_air_conditioning(
        self, on: bool, minutes: int
    ) -> str | None:
        """Start the air conditioner for a number of minutes, or stop it."""
        command, body = ac_command_body(on, minutes, str(uuid4()))
        return await self._async_vehicle_command(command, body)

    async def async_set_locked(self, locked: bool) -> str | None:
        """Lock or unlock the car."""
        command, body = lock_command_body(locked, str(uuid4()))
        return await self._async_vehicle_command(command, body)

    async def _async_vehicle_command(
        self, command: str, body: dict[str, Any]
    ) -> str | None:
        access_token, rotated = await self._async_refresh()
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


def _login_headers(access_token: str | None = None) -> dict[str, str]:
    headers = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "App-Version": APP_VERSION,
        "x-api-key": APP_API_KEY,
        "Accept": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


async def async_send_otp(
    session: aiohttp.ClientSession, country_code: str, phone: str
) -> str:
    """Text a sign-in code and return the reference id for that code."""
    payload = await _async_login_request(
        session,
        "POST",
        CHECK_PHONE_PATH,
        json_body={"countryCode": country_code, "phone": phone, "sendOtp": True},
    )
    ref_id = parse_ref_id(payload)
    if not ref_id:
        raise IraAuthError("iRA.ev did not send a verification code")
    return ref_id


async def async_sign_in(
    session: aiohttp.ClientSession,
    country_code: str,
    phone: str,
    otp: str,
    ref_id: str,
) -> tuple[str, list[str]]:
    """Exchange the sign-in code for a refresh token and the account's cars."""
    verified = await _async_login_request(
        session,
        "POST",
        VERIFY_OTP_PATH,
        json_body=otp_verify_body(country_code, phone, otp, ref_id),
    )
    verifier = parse_code_verifier(verified)
    if not verifier:
        raise IraAuthError("That code was not accepted")
    tokens = await _async_login_request(
        session,
        "POST",
        ACCESS_TOKEN_PATH,
        json_body={"codeVerifier": verifier},
    )
    access_token, refresh_token = parse_login_tokens(tokens)
    if not access_token or not refresh_token:
        raise IraAuthError("iRA.ev did not return a session")
    profile = await _async_login_request(
        session,
        "GET",
        PROFILE_PATH,
        headers=_login_headers(access_token),
    )
    return refresh_token, parse_vehicle_ids(profile)


async def _async_login_request(
    session: aiohttp.ClientSession,
    method: str,
    path: str,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    try:
        async with session.request(
            method,
            f"{API_HOST}{path}",
            headers=headers or _login_headers(),
            json=json_body,
            timeout=aiohttp.ClientTimeout(total=20),
        ) as response:
            try:
                payload = await response.json(content_type=None)
            except (aiohttp.ContentTypeError, ValueError):
                payload = None
            if not isinstance(payload, dict):
                if response.status in (401, 403, 400):
                    raise IraAuthError(f"iRA.ev returned HTTP {response.status}")
                if response.status >= 400:
                    raise IraError(f"iRA.ev returned HTTP {response.status}")
                raise IraError("iRA.ev returned an unexpected response")
            message, code = service_error(payload)
            if response.status in (401, 403, 400) or message:
                raise IraAuthError(
                    message or f"iRA.ev returned HTTP {response.status}",
                    code=code,
                )
            if response.status >= 400:
                raise IraError(f"iRA.ev returned HTTP {response.status}")
            return payload
    except (IraError, IraAuthError):
        raise
    except (aiohttp.ClientError, TimeoutError) as err:
        raise IraConnectionError("Cannot reach the iRA.ev service") from err
