import unittest
from typing import List, Any

from balena.balena_auth import request
from tests.helper import TestHelper
import time


def send_log_messages(uuid: str, device_api_key: str, messages: List[Any]):
    request(
        method="POST",
        path=f"/device/v2/{uuid}/logs",
        token=device_api_key,
        body=messages
    )


class TestAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.helper.wipe_application()
        cls.app = cls.balena.models.application.create(
            "FooBarLogs",
            "raspberry-pi2",
            cls.helper.default_organization["id"]
        )

    @classmethod
    def tearDownClass(cls):

        print("unsubscribes all")
        cls.balena.logs.unsubscribe_all()
        print("stop")
        cls.balena.logs.stop()

        cls.balena.pine.delete({
            "resource": "device",
            "options": {
                "$filter": {"1": 1}
            }
        })
        cls.helper.wipe_organization()

    def setUp(self):
        self.uuid = self.balena.models.device.generate_uuid()
        registration_info = self.balena.models.device.register(self.app["id"], self.uuid)
        self.device_api_key = registration_info["api_key"]

    def __collect_logs(self, timeout: int = 5, count=None):
        results = []

        def cb(data):
            results.append(data)

        self.balena.logs.subscribe(self.uuid, cb, count=count)

        time.sleep(timeout)
        self.balena.logs.unsubscribe(self.uuid)

        return results

    def test_01_should_load_historical_logs_and_limit_by_count(self):
        send_log_messages(self.uuid, self.device_api_key, [
            {
                "message": 'First message',
                "timestamp": int(time.time() * 1000)
            },
            {
                "message": 'Second message',
                "timestamp": int(time.time() * 1000)
            },
        ])

        time.sleep(2)
        messages = [log["message"] for log in self.balena.logs.history(self.uuid)]
        self.assertEqual(messages, ["First message", "Second message"])

        messages = [log["message"] for log in self.balena.logs.history(self.uuid, count=1)]
        self.assertEqual(messages, ["Second message"])

    def test_02_subscribe_should_not_fetch_historical_by_default(self):
        send_log_messages(self.uuid, self.device_api_key, [
            {
                "message": 'First message',
                "timestamp": int(time.time() * 1000)
            },
            {
                "message": 'Second message',
                "timestamp": int(time.time() * 1000)
            },
        ])
        time.sleep(2)

        logs = self.__collect_logs()
        self.assertEqual(logs, [])

    def test_03_subscribe_should_fetch_historical_data_if_requested(self):
        send_log_messages(self.uuid, self.device_api_key, [
            {
                "message": 'First message',
                "timestamp": int(time.time() * 1000)
            },
            {
                "message": 'Second message',
                "timestamp": int(time.time() * 1000)
            },
        ])
        time.sleep(2)

        log_messages = [log["message"] for log in self.__collect_logs(count="all")]
        self.assertEqual(log_messages, ["First message", "Second message"])

    def test_04_subscribe_should_limit_historical_data_if_requested(self):
        send_log_messages(self.uuid, self.device_api_key, [
            {
                "message": 'First message',
                "timestamp": int(time.time() * 1000)
            },
            {
                "message": 'Second message',
                "timestamp": int(time.time() * 1000)
            },
        ])
        time.sleep(2)

        log_messages = [log["message"] for log in self.__collect_logs(count=1)]
        self.assertEqual(log_messages, ["Second message"])

    def test_05_subscribe_should_stream_new_logs(self):
        results = []

        def cb(data):
            results.append(data["message"])

        self.balena.logs.subscribe(self.uuid, cb)

        time.sleep(0.1)
        send_log_messages(self.uuid, self.device_api_key, [
            {
                "message": 'First message',
                "timestamp": int(time.time() * 1000)
            },
            {
                "message": 'Second message',
                "timestamp": int(time.time() * 1000)
            },
        ])

        time.sleep(2)
        self.assertEqual(results, ["First message", "Second message"])

        self.balena.logs.unsubscribe(self.uuid)

    def test_06_should_allow_to_unsubiscribe(self):

        results = []

        def cb(data):
            results.append(data["message"])

        self.balena.logs.subscribe(self.uuid, cb)
        time.sleep(1)
        self.balena.logs.unsubscribe(self.uuid)

        send_log_messages(self.uuid, self.device_api_key, [
            {
                "message": 'First message',
                "timestamp": int(time.time() * 1000)
            },
            {
                "message": 'Second message',
                "timestamp": int(time.time() * 1000)
            },
        ])

        time.sleep(2)
        self.assertEqual(results, [])
