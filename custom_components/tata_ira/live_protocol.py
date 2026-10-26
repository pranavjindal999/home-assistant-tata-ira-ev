"""Last-known-state crypto and MQTT packets, with no network calls."""

from __future__ import annotations

import base64
import json
import os
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

PREFERRED_TEMPLATES = (
    "prod-lks-edgealert-onchange-1",
    "prod-lks-periodic-telemetry-1",
    "uat-lks-edgealert-onchange-1",
    "uat-lks-periodic-telemetry-1",
)
DEFAULT_AUTHORIZER = "api-vid-lambda-authorizer"
LKS_EXPIRY_SECONDS = 900
_B2C_KEY_NAMES = ("n_io_b2c_api_key", "nio_b2c_api_key", "n_io_b2c_x_api_key")


def ecdh_request(
    device_id: str, api_type: str = "afterLogin"
) -> tuple[dict[str, str], ec.EllipticCurvePrivateKey]:
    """Build the key exchange the app sends."""
    identity = ec.generate_private_key(ec.SECP256R1())
    ephemeral = ec.generate_private_key(ec.SECP256R1())
    public = ephemeral.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    signature = identity.sign(public, ec.ECDSA(hashes.SHA256()))
    body = {
        "clientEphemeralPublicKey": base64.b64encode(public).decode(),
        "signature": base64.b64encode(signature).decode(),
        "deviceId": device_id,
        "clientNonce": base64.b64encode(os.urandom(32)).decode(),
        "apiType": api_type,
    }
    return body, ephemeral


def decrypt_secrets(
    ephemeral: ec.EllipticCurvePrivateKey,
    server_public_b64: str,
    encrypted_b64: str,
) -> dict[str, Any]:
    """Decrypt the key bundle with the app's AES wrapping of the ECDH secret."""
    server = serialization.load_der_public_key(base64.b64decode(server_public_b64))
    if not isinstance(server, ec.EllipticCurvePublicKey):
        raise ValueError("server key")
    secret = ephemeral.exchange(ec.ECDH(), server)
    decryptor = Cipher(algorithms.AES(secret[:32]), modes.CBC(secret[:16])).decryptor()
    plain = decryptor.update(base64.b64decode(encrypted_b64)) + decryptor.finalize()
    pad = plain[-1]
    if pad < 1 or pad > 16 or plain[-pad:] != bytes([pad]) * pad:
        raise ValueError("padding")
    payload = json.loads(plain[:-pad])
    if not isinstance(payload, dict):
        raise ValueError("secrets")
    return payload


def nio_auth_material(secrets: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return the live sign-in key and client secret from a decrypted bundle."""
    key = secrets.get("nio_auth_x_api_key")
    secret = secrets.get("client_secret_value")
    if not isinstance(key, str) or not key:
        key = None
    if not isinstance(secret, str) or not secret:
        secret = None
    return key, secret


def parse_nio_refresh(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return the live access token and a rotated refresh token."""
    results = payload.get("results")
    source = results if isinstance(results, dict) else payload
    details = source.get("accessTokenDetails") if isinstance(source, dict) else None
    if isinstance(details, dict):
        source = details
    if not isinstance(source, dict):
        return None, None
    access = source.get("accessToken")
    refreshed = source.get("refreshToken")
    if not isinstance(access, str) or not access:
        return None, None
    if not isinstance(refreshed, str) or not refreshed:
        refreshed = None
    return access, refreshed


def b2c_api_key(secrets: dict[str, Any]) -> str | None:
    """Return the live-channel API key from a decrypted key bundle."""
    for name in _B2C_KEY_NAMES:
        value = secrets.get(name)
        if isinstance(value, str) and value:
            return value
    return None


def select_templates(templates: list[Any]) -> list[dict[str, Any]]:
    """Pick the on-change and periodic templates the home screen subscribes to."""
    usable = [
        item
        for item in templates
        if isinstance(item, dict) and item.get("mqttTopic") and item.get("endpointUrl")
    ]
    chosen = [item for item in usable if item.get("name") in PREFERRED_TEMPLATES]
    return chosen or usable


def mqtt_websocket_url(endpoint: str, authorizer: str) -> str:
    """Turn a template endpoint into the AWS IoT websocket URL."""
    raw = endpoint.strip()
    if "://" not in raw:
        raw = f"wss://{raw}"
    parts = urlsplit(raw)
    scheme = "wss" if parts.scheme in ("https", "http", "ws", "wss", "") else parts.scheme
    path = parts.path if parts.path not in ("", "/") else "/mqtt"
    query = urlencode(
        {"x-amz-customauthorizer-name": authorizer or DEFAULT_AUTHORIZER}
    )
    return urlunsplit((scheme, parts.netloc, path, query, ""))


def encode_connect(client_id: str, username: str, password: str) -> bytes:
    """MQTT 3.1.1 CONNECT with a username and password."""
    payload = _utf8(client_id) + _utf8(username) + _utf8(password)
    variable = b"\x00\x04MQTT" + bytes((4, 0xC2)) + (60).to_bytes(2, "big") + payload
    return bytes((0x10,)) + _remaining(len(variable)) + variable


def encode_subscribe(packet_id: int, topic: str) -> bytes:
    """MQTT SUBSCRIBE for one topic at QoS 0."""
    variable = packet_id.to_bytes(2, "big") + _utf8(topic) + bytes((0,))
    return bytes((0x82,)) + _remaining(len(variable)) + variable


def encode_ping() -> bytes:
    """MQTT PINGREQ."""
    return b"\xc0\x00"


def encode_pong() -> bytes:
    """MQTT PINGRESP."""
    return b"\xd0\x00"


class MqttDecoder:
    """Split a TCP/websocket byte stream into MQTT packets."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[tuple[int, bytes]]:
        """Return complete packets as ``(first_byte, body)``."""
        self._buffer.extend(data)
        packets: list[tuple[int, bytes]] = []
        while True:
            packet = self._pop()
            if packet is None:
                return packets
            packets.append(packet)

    def _pop(self) -> tuple[int, bytes] | None:
        if len(self._buffer) < 2:
            return None
        remaining = 0
        multiplier = 1
        index = 1
        while True:
            if index >= len(self._buffer):
                return None
            digit = self._buffer[index]
            remaining += (digit & 0x7F) * multiplier
            index += 1
            if digit & 0x80 == 0:
                break
            multiplier *= 128
            if multiplier > 128**3:
                raise ValueError("remaining length")
        total = index + remaining
        if len(self._buffer) < total:
            return None
        first = self._buffer[0]
        body = bytes(self._buffer[index:total])
        del self._buffer[:total]
        return first, body


def publish_payload(first: int, body: bytes) -> bytes | None:
    """Return the body of a PUBLISH packet."""
    if (first & 0xF0) != 0x30 or len(body) < 2:
        return None
    topic_len = int.from_bytes(body[:2], "big")
    start = 2 + topic_len
    qos = (first >> 1) & 0x03
    if qos:
        start += 2
    if start > len(body):
        return None
    return body[start:]


def connack_code(first: int, body: bytes) -> int | None:
    """Return the MQTT 3.1.1 CONNACK code, when this packet is a CONNACK."""
    if first != 0x20 or len(body) < 2:
        return None
    return body[1]


def _utf8(value: str) -> bytes:
    raw = value.encode()
    return len(raw).to_bytes(2, "big") + raw


def _remaining(length: int) -> bytes:
    encoded = bytearray()
    while True:
        digit = length % 128
        length //= 128
        if length:
            digit |= 0x80
        encoded.append(digit)
        if not length:
            return bytes(encoded)
