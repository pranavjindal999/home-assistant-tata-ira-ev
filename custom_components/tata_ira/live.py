"""Subscribe to the same live vehicle channel the iRA.ev home screen uses."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import aiohttp

from .const import (
    API_HOST,
    APP_VERSION,
    CLIENT_ID,
    ECDH_PATH,
    LKS_ACTIVATE_PATH,
    LKS_TEMPLATE_PATH,
    NIO_CLIENT_ID,
)
from .live_protocol import (
    DEFAULT_AUTHORIZER,
    LKS_EXPIRY_SECONDS,
    MqttDecoder,
    b2c_api_key,
    connack_code,
    decrypt_secrets,
    ecdh_request,
    encode_connect,
    encode_ping,
    encode_pong,
    encode_subscribe,
    mqtt_websocket_url,
    publish_payload,
    select_templates,
)
from .parser import merge_live_payload

_LOGGER = logging.getLogger(__name__)
_RENEW_SECONDS = 12 * 60
_PING_SECONDS = 30

RefreshTokens = Callable[[], Awaitable[tuple[str, str | None]]]


class LiveUnavailable(Exception):
    """The live channel could not be opened. The caller keeps polling."""


async def stream_live(
    session: aiohttp.ClientSession,
    refresh: RefreshTokens,
    vehicle_id: str,
    mobile_api_key: str,
    key_cache: dict[str, str],
) -> AsyncIterator[tuple[dict[str, Any], str | None, bool]]:
    """Yield live snapshots until the socket closes.

    Each item is the snapshot, a rotated refresh token when the service issued
    one, and whether the broker has accepted the connection. Nothing in the
    logs includes the token, the topic, or the key.
    """
    access_token, rotated = await refresh()
    lks_key = key_cache.get("key")
    if not lks_key:
        lks_key = await _async_lks_key(session, access_token, mobile_api_key, vehicle_id)
        if not lks_key:
            raise LiveUnavailable("the account secrets did not include the live channel key")
        key_cache["key"] = lks_key
    templates = await _async_templates(session, access_token, lks_key, vehicle_id)
    chosen = select_templates(templates)
    if not chosen:
        key_cache.pop("key", None)
        raise LiveUnavailable("the car did not return a live template")
    accumulated: dict[str, Any] = {}
    for template in chosen:
        status, snapshot = await _async_activate(
            session, access_token, lks_key, vehicle_id, template
        )
        if status != 200:
            key_cache.pop("key", None)
            raise LiveUnavailable(f"the live channel returned HTTP {status}")
        if snapshot:
            accumulated = merge_live_payload(accumulated, snapshot)
    endpoint = str(chosen[0].get("endpointUrl") or "")
    authorizer = str(chosen[0].get("authorizerName") or DEFAULT_AUTHORIZER)
    topics = [str(item["mqttTopic"]) for item in chosen if item.get("mqttTopic")]
    if not endpoint or not topics:
        raise LiveUnavailable("the live template did not include a channel")
    if accumulated or rotated:
        yield accumulated, rotated, False
        rotated = None
    async for payload in _async_socket(
        session,
        refresh,
        access_token,
        rotated,
        vehicle_id,
        lks_key,
        endpoint,
        authorizer,
        topics,
        chosen,
    ):
        yield payload


async def _async_socket(
    session: aiohttp.ClientSession,
    refresh: RefreshTokens,
    access_token: str,
    rotated: str | None,
    vehicle_id: str,
    lks_key: str,
    endpoint: str,
    authorizer: str,
    topics: list[str],
    templates: list[dict[str, Any]],
) -> AsyncIterator[tuple[dict[str, Any], str | None, bool]]:
    url = mqtt_websocket_url(endpoint, authorizer)
    try:
        websocket = await session.ws_connect(
            url,
            protocols=("mqtt",),
            heartbeat=20,
            autoping=True,
            max_msg_size=1024 * 1024,
        )
    except (aiohttp.ClientError, TimeoutError) as err:
        raise LiveUnavailable("the live socket could not be opened") from err
    try:
        client_id = "ha" + uuid4().hex[:10]
        await websocket.send_bytes(encode_connect(client_id, "idToken", access_token))
        decoder = MqttDecoder()
        code = await _async_connack(websocket, decoder)
        if code != 0:
            raise LiveUnavailable(f"the live channel refused the connection ({code})")
        for index, topic in enumerate(topics, start=1):
            await websocket.send_bytes(encode_subscribe(index, topic))
        yield {}, rotated, True
        next_ping = asyncio.get_running_loop().time() + _PING_SECONDS
        next_renew = asyncio.get_running_loop().time() + _RENEW_SECONDS
        while True:
            now = asyncio.get_running_loop().time()
            if now >= next_renew:
                access_token, rotated = await refresh()
                for template in templates:
                    status, snapshot = await _async_activate(
                        session, access_token, lks_key, vehicle_id, template
                    )
                    if status != 200:
                        raise LiveUnavailable(f"the live channel returned HTTP {status}")
                    if snapshot or rotated:
                        yield snapshot or {}, rotated, True
                        rotated = None
                next_renew = asyncio.get_running_loop().time() + _RENEW_SECONDS
                continue
            if now >= next_ping:
                await websocket.send_bytes(encode_ping())
                next_ping = asyncio.get_running_loop().time() + _PING_SECONDS
                continue
            timeout = max(1.0, min(next_ping, next_renew) - now)
            try:
                message = await asyncio.wait_for(websocket.receive(), timeout)
            except TimeoutError:
                continue
            if message.type in (
                aiohttp.WSMsgType.CLOSE,
                aiohttp.WSMsgType.CLOSED,
                aiohttp.WSMsgType.CLOSING,
                aiohttp.WSMsgType.ERROR,
            ):
                raise LiveUnavailable("the live socket closed")
            if message.type != aiohttp.WSMsgType.BINARY:
                continue
            data = message.data if isinstance(message.data, (bytes, bytearray)) else b""
            for first, body in decoder.feed(bytes(data)):
                if first == 0xC0:
                    await websocket.send_bytes(encode_pong())
                    continue
                if (first & 0xF0) == 0x30:
                    if (first >> 1) & 0x03 == 1:
                        ack = _puback(body)
                        if ack:
                            await websocket.send_bytes(ack)
                    raw = publish_payload(first, body)
                    snapshot = _snapshot(raw)
                    if snapshot:
                        yield snapshot, None, True
    finally:
        await websocket.close()


async def _async_connack(websocket: aiohttp.ClientWebSocketResponse, decoder: MqttDecoder) -> int:
    deadline = asyncio.get_running_loop().time() + 20
    while asyncio.get_running_loop().time() < deadline:
        message = await asyncio.wait_for(websocket.receive(), 20)
        if message.type != aiohttp.WSMsgType.BINARY:
            raise LiveUnavailable("the live socket closed")
        data = message.data if isinstance(message.data, (bytes, bytearray)) else b""
        for first, body in decoder.feed(bytes(data)):
            code = connack_code(first, body)
            if code is not None:
                return code
    raise LiveUnavailable("the live channel did not accept the connection")


async def _async_lks_key(
    session: aiohttp.ClientSession,
    access_token: str,
    mobile_api_key: str,
    vehicle_id: str,
) -> str | None:
    device_id = "ha-" + hashlib.sha256(vehicle_id.encode()).hexdigest()[:16]
    body, ephemeral = ecdh_request(device_id)
    status, payload = await _async_json(
        session,
        "POST",
        ECDH_PATH,
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "client_id": CLIENT_ID,
            "App-Version": APP_VERSION,
            "x-api-key": mobile_api_key,
            "Authorization": f"Bearer {access_token}",
        },
        body,
    )
    if status != 200:
        raise LiveUnavailable(f"the live channel returned HTTP {status}")
    results = payload.get("results")
    if not isinstance(results, dict):
        return None
    public = results.get("serverEphemeralPublicKey")
    encrypted = results.get("encryptedSecrets")
    if not isinstance(public, str) or not isinstance(encrypted, str):
        return None
    try:
        secrets = decrypt_secrets(ephemeral, public, encrypted)
    except (ValueError, json.JSONDecodeError, TypeError):
        raise LiveUnavailable("the live channel key could not be read") from None
    key = b2c_api_key(secrets)
    if key is None:
        _LOGGER.debug("Live channel key names: %s", ",".join(sorted(secrets)))
    return key


async def _async_templates(
    session: aiohttp.ClientSession,
    access_token: str,
    lks_key: str,
    vehicle_id: str,
) -> list[Any]:
    path = LKS_TEMPLATE_PATH.format(vehicle_id=quote(vehicle_id, safe=""))
    status, payload = await _async_lks(session, "GET", path, access_token, lks_key, None)
    if status != 200:
        raise LiveUnavailable(f"the live channel returned HTTP {status}")
    results = payload.get("results")
    if isinstance(results, dict):
        templates = results.get("templates")
        if isinstance(templates, list):
            return templates
    if isinstance(results, list):
        return results
    return []


async def _async_activate(
    session: aiohttp.ClientSession,
    access_token: str,
    lks_key: str,
    vehicle_id: str,
    template: dict[str, Any],
) -> tuple[int, dict[str, Any] | None]:
    path = LKS_ACTIVATE_PATH.format(vehicle_id=quote(vehicle_id, safe=""))
    body = _activate_body(vehicle_id, template)
    status, payload = await _async_lks(session, "POST", path, access_token, lks_key, body)
    if status == 400 and "templateName" in body:
        status, payload = await _async_lks(
            session,
            "POST",
            path,
            access_token,
            lks_key,
            _activate_body(vehicle_id, {}),
        )
    results = payload.get("results")
    snapshot = results if isinstance(results, dict) and _is_snapshot(results) else None
    return status, snapshot


def _activate_body(vehicle_id: str, template: dict[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "virtualId": vehicle_id,
        "expiryTimeInSeconds": LKS_EXPIRY_SECONDS,
    }
    name = template.get("name")
    if isinstance(name, str) and name:
        body["templateName"] = name
    return body


async def _async_lks(
    session: aiohttp.ClientSession,
    method: str,
    path: str,
    access_token: str,
    lks_key: str,
    body: dict[str, Any] | None,
) -> tuple[int, dict[str, Any]]:
    last = (0, {})
    for client_id in (NIO_CLIENT_ID, CLIENT_ID):
        status, payload = await _async_json(
            session,
            method,
            path,
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
                "x-api-key": lks_key,
                "client_id": client_id,
                "App-Version": APP_VERSION,
            },
            body,
        )
        last = (status, payload)
        if status != 403:
            return status, payload
    return last


async def _async_json(
    session: aiohttp.ClientSession,
    method: str,
    path: str,
    headers: dict[str, str],
    body: dict[str, Any] | None,
) -> tuple[int, dict[str, Any]]:
    try:
        async with session.request(
            method,
            f"{API_HOST}{path}",
            headers=headers,
            json=body,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            try:
                payload = await response.json(content_type=None)
            except (aiohttp.ContentTypeError, ValueError, json.JSONDecodeError):
                payload = None
            return response.status, payload if isinstance(payload, dict) else {}
    except (aiohttp.ClientError, TimeoutError) as err:
        raise LiveUnavailable("the live channel could not be reached") from err


def _puback(body: bytes) -> bytes:
    if len(body) < 2:
        return b""
    topic_len = int.from_bytes(body[:2], "big")
    packet_id = body[2 + topic_len : 4 + topic_len]
    if len(packet_id) != 2:
        return b""
    return bytes((0x40, 0x02)) + packet_id


def _snapshot(raw: bytes | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict) and isinstance(payload.get("results"), dict):
        nested = payload["results"]
        if _is_snapshot(nested):
            return nested
    if isinstance(payload, dict) and _is_snapshot(payload):
        return payload
    return None


def _is_snapshot(payload: dict[str, Any]) -> bool:
    return any(isinstance(key, str) and key.startswith("V_") for key in payload) or (
        "dynamicSignals" in payload
    )
