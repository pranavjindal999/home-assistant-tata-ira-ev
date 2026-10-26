"""Tests for the live-channel crypto and MQTT packets."""

from __future__ import annotations

import base64
import importlib.util
import json
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_PATH = Path(__file__).parents[1] / "custom_components" / "tata_ira" / "live_protocol.py"
_SPEC = importlib.util.spec_from_file_location("tata_ira_live_protocol", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def _encrypt(ephemeral: ec.EllipticCurvePrivateKey, payload: dict) -> tuple[str, str]:
    server = ec.generate_private_key(ec.SECP256R1())
    secret = server.exchange(ec.ECDH(), ephemeral.public_key())
    plain = json.dumps(payload).encode()
    pad = 16 - (len(plain) % 16)
    plain += bytes([pad]) * pad
    encryptor = Cipher(algorithms.AES(secret[:32]), modes.CBC(secret[:16])).encryptor()
    encrypted = encryptor.update(plain) + encryptor.finalize()
    public = server.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return base64.b64encode(public).decode(), base64.b64encode(encrypted).decode()


class LiveProtocolTests(unittest.TestCase):
    def test_key_exchange_round_trip_reads_only_the_live_key_name(self) -> None:
        _body, ephemeral = _MODULE.ecdh_request("ha-test")
        public, encrypted = _encrypt(ephemeral, {"n_io_b2c_api_key": "live-key", "x_api_key": "other"})
        secrets = _MODULE.decrypt_secrets(ephemeral, public, encrypted)
        self.assertEqual(_MODULE.b2c_api_key(secrets), "live-key")

    def test_live_sign_in_reads_the_auth_key_and_tokens(self) -> None:
        body, _ephemeral = _MODULE.ecdh_request("ha-test", "beforeLogin")
        self.assertEqual(body["apiType"], "beforeLogin")
        self.assertEqual(
            _MODULE.nio_auth_material(
                {"nio_auth_x_api_key": "key", "client_secret_value": "secret"}
            ),
            ("key", "secret"),
        )
        self.assertEqual(
            _MODULE.parse_nio_refresh(
                {"results": {"accessToken": "live", "refreshToken": "next"}}
            ),
            ("live", "next"),
        )
        self.assertEqual(_MODULE.parse_nio_refresh({"message": "no"}), (None, None))

    def test_templates_prefer_the_home_screen_pair(self) -> None:
        chosen = _MODULE.select_templates(
            [
                {"name": "other", "mqttTopic": "a", "endpointUrl": "host"},
                {
                    "name": "prod-lks-periodic-telemetry-1",
                    "mqttTopic": "periodic",
                    "endpointUrl": "host",
                },
                {"name": "prod-lks-edgealert-onchange-1", "mqttTopic": "", "endpointUrl": "host"},
                {
                    "name": "prod-lks-edgealert-onchange-1",
                    "mqttTopic": "changes",
                    "endpointUrl": "host",
                },
            ]
        )
        self.assertEqual(
            [item["name"] for item in chosen],
            ["prod-lks-periodic-telemetry-1", "prod-lks-edgealert-onchange-1"],
        )

    def test_websocket_url_uses_the_template_authorizer(self) -> None:
        url = _MODULE.mqtt_websocket_url(
            "abc.iot.ap-south-1.amazonaws.com", "api-vid-lambda-authorizer"
        )
        self.assertEqual(
            url,
            "wss://abc.iot.ap-south-1.amazonaws.com/mqtt"
            "?x-amz-customauthorizer-name=api-vid-lambda-authorizer",
        )

    def test_mqtt_packets_round_trip(self) -> None:
        decoder = _MODULE.MqttDecoder()
        packets = decoder.feed(_MODULE.encode_connect("client", "idToken", "secret"))
        self.assertEqual(packets[0][0], 0x10)
        first, body = decoder.feed(bytes((0x20, 0x02, 0x00, 0x00)))[0]
        self.assertEqual(_MODULE.connack_code(first, body), 0)
        subscribed = decoder.feed(_MODULE.encode_subscribe(1, "vehicle/topic"))
        self.assertEqual(subscribed[0][0], 0x82)
        payload = b'{"ok":1}'
        body = b"\x00\x04live" + payload
        packet = bytes((0x30, len(body))) + body
        self.assertEqual(decoder.feed(packet[:3]), [])
        first, decoded_body = decoder.feed(packet[3:])[0]
        self.assertEqual(_MODULE.publish_payload(first, decoded_body), payload)


if __name__ == "__main__":
    unittest.main()
