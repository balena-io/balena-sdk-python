import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

from balena.exceptions import RequestError
from balena.pine import PineClient
from balena.settings import Settings


class TestSettings(unittest.TestCase):
    def test_set_preserves_booleans(self):
        with tempfile.TemporaryDirectory() as directory:
            for data_directory in (False, directory):
                with self.subTest(data_directory=data_directory):
                    settings = Settings({"data_directory": data_directory})
                    for value in (True, False):
                        settings.set("retry_rate_limited_request", value)
                        self.assertIs(settings.get("retry_rate_limited_request"), value)
                        self.assertIs(settings.get_all()["retry_rate_limited_request"], value)
                        if data_directory:
                            reloaded = Settings({"data_directory": data_directory})
                            self.assertIs(reloaded.get("retry_rate_limited_request"), value)

    def test_set_preserves_string_values(self):
        with tempfile.TemporaryDirectory() as directory:
            for data_directory in (False, directory):
                with self.subTest(data_directory=data_directory):
                    settings = Settings({"data_directory": data_directory})
                    settings.set("timeout", "1234")
                    self.assertEqual(settings.get("timeout"), "1234")

    def test_enable_rate_limit_retries_with_set(self):
        with tempfile.TemporaryDirectory() as directory:
            for data_directory in (False, directory):
                with self.subTest(data_directory=data_directory):
                    settings = Settings({"data_directory": data_directory})
                    settings.set("retry_rate_limited_request", True)
                    client = PineClient(settings, "test")
                    limited = Mock(spec=requests.Response, ok=False, status_code=429)
                    limited.headers = {"retry-after": "2"}
                    limited.content = b"rate limited"
                    success = Mock(spec=requests.Response, ok=True)
                    success.json.return_value = {"devices": []}
                    with patch("balena.pine.get_token", return_value=None), patch("balena.pine.sleep") as sleep:
                        with patch("balena.pine.requests.request", side_effect=[limited, success]) as request:
                            self.assertEqual(client._request("GET", "https://example.com/v7/device"), {"devices": []})
                            self.assertEqual(request.call_count, 2)
                            sleep.assert_called_once_with(2)

    def test_disable_rate_limit_retries_with_set(self):
        with tempfile.TemporaryDirectory() as directory:
            for data_directory in (False, directory):
                with self.subTest(data_directory=data_directory):
                    settings = Settings({"data_directory": data_directory})
                    settings.set("retry_rate_limited_request", True)
                    settings.set("retry_rate_limited_request", False)
                    client = PineClient(settings, "test")
                    limited = Mock(spec=requests.Response, ok=False, status_code=429)
                    limited.headers = {"retry-after": "2"}
                    limited.content = b"rate limited"
                    with patch("balena.pine.get_token", return_value=None), patch("balena.pine.sleep") as sleep:
                        with patch("balena.pine.requests.request", return_value=limited) as request:
                            with self.assertRaises(RequestError):
                                client._request("GET", "https://example.com/v7/device")
                            self.assertEqual(request.call_count, 1)
                            sleep.assert_not_called()
