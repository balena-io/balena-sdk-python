import unittest
from typing import List, Any

from balena.balena_auth import request
from tests.helper import TestHelper
import time


# Logs may sometimes take time to appear in the logs history.
#
# To handle this, the approach uses a more complex setup for detecting the initial burst of logs:
#
# We check for the first burst of logs every WAIT_FOR_FIRSTLOGS_TIMEOUT_S seconds
# repeating this process up to WAIT_FOR_FIRSTLOGS_ATTEMPTS times.
# Once the initial burst is received, the logging behavior becomes more stable, so we switch to fixed timeouts
# The fixed timeouts include:
#
# WAIT_FOR_LOGS_TIMEOUT_S: The duration spent waiting for logs after the initial burst
# WAIT_AFTER_SUBSCRIBE_TIMEOUT_S: Time after subscribing, ensuring the client has time to start or stop receiving logs


WAIT_FOR_FIRSTLOGS_TIMEOUT_S = 5
WAIT_FOR_FIRSTLOGS_ATTEMPTS = 20
WAIT_FOR_LOGS_TIMEOUT_S = 20
WAIT_AFTER_SUBSCRIBE_TIMEOUT_S = 10


def send_log_messages(uuid: str, device_api_key: str, messages: List[Any], settings):
    request(method="POST", settings=settings, path=f"/device/v2/{uuid}/logs", token=device_api_key, body=messages)


class TestAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.helper.wipe_application()
        cls.app = cls.balena.models.application.create(
            "FooBarLogs", "raspberry-pi2", cls.helper.default_organization["id"]
        )

        cls.uuid = cls.balena.models.device.generate_uuid()
        registration_info = cls.balena.models.device.register(cls.app["id"], cls.uuid)
        cls.device_api_key = registration_info["api_key"]

    @classmethod
    def tearDownClass(cls):
        print("unsubscribes all")
        cls.balena.logs.unsubscribe_all()
        print("stop")
        cls.balena.logs.stop()

        # cls.balena.pine.delete({"resource": "device", "options": {"$filter": {"1": 1}}})
        # cls.helper.wipe_organization()

    def __collect_logs(self, timeout: int = WAIT_FOR_LOGS_TIMEOUT_S, count=None):
        results = []

        def cb(data):
            results.append(data)

        self.balena.logs.subscribe(self.uuid, cb, count=count)
        time.sleep(WAIT_AFTER_SUBSCRIBE_TIMEOUT_S)

        time.sleep(timeout)

        self.balena.logs.unsubscribe(self.uuid)
        time.sleep(WAIT_AFTER_SUBSCRIBE_TIMEOUT_S)

        return results

    def test_01_should_load_historical_logs_and_limit_by_count(self):
        send_log_messages(
            self.uuid,
            self.device_api_key,
            [
                {"message": "1 message", "timestamp": int(time.time() * 1000)},
                {"message": "2 message", "timestamp": int((time.time() * 1000))},
            ],
            self.balena.settings,
        )

        timeout = time.time() + WAIT_FOR_FIRSTLOGS_TIMEOUT_S * WAIT_FOR_FIRSTLOGS_ATTEMPTS
        expected_messages = ["1 message", "2 message"]

        while time.time() < timeout:
            messages = [log["message"] for log in self.balena.logs.history(self.uuid)]
            if messages == expected_messages:
                break
            time.sleep(WAIT_FOR_FIRSTLOGS_TIMEOUT_S)

        self.assertEqual(messages, expected_messages)

        messages = [log["message"] for log in self.balena.logs.history(self.uuid, count=1)]
        self.assertEqual(messages, ["2 message"])

    def test_02_subscribe_should_not_fetch_historical_by_default(self):
        send_log_messages(
            self.uuid,
            self.device_api_key,
            [
                {"message": "3 message", "timestamp": int(time.time() * 1000)},
                {"message": "4 message", "timestamp": int(time.time() * 1000)},
            ],
            self.balena.settings,
        )

        logs = self.__collect_logs()
        self.assertEqual(logs, [])

    def test_03_subscribe_should_fetch_historical_data_if_requested(self):
        send_log_messages(
            self.uuid,
            self.device_api_key,
            [
                {"message": "5 message", "timestamp": int(time.time() * 1000)},
                {"message": "6 message", "timestamp": int(time.time() * 1000)},
            ],
            self.balena.settings,
        )

        log_messages = [log["message"] for log in self.__collect_logs(count="all")]
        print('log messages are', log_messages)
        self.assertTrue(all(msg in log_messages for msg in ["1 message", "2 message", "3 message", "4 message"]))

    def test_04_subscribe_should_limit_historical_data_if_requested(self):
        log_messages = [log["message"] for log in self.__collect_logs(count=1)]
        self.assertEqual(log_messages, ["6 message"])

    def test_05_subscribe_should_stream_new_logs(self):
        results = []

        def cb(data):
            results.append(data["message"])

        self.balena.logs.subscribe(self.uuid, cb)
        time.sleep(WAIT_AFTER_SUBSCRIBE_TIMEOUT_S)

        send_log_messages(
            self.uuid,
            self.device_api_key,
            [
                {"message": "7 message", "timestamp": int(time.time() * 1000)},
                {"message": "8 message", "timestamp": int(time.time() * 1000)},
            ],
            self.balena.settings,
        )

        time.sleep(WAIT_FOR_LOGS_TIMEOUT_S)
        self.assertEqual(results, ["7 message", "8 message"])

        self.balena.logs.unsubscribe(self.uuid)

    def test_06_should_allow_to_unsubscribe(self):
        results = []

        def cb(data):
            results.append(data["message"])

        self.balena.logs.subscribe(self.uuid, cb)
        time.sleep(WAIT_AFTER_SUBSCRIBE_TIMEOUT_S)
        self.balena.logs.unsubscribe(self.uuid)
        time.sleep(WAIT_AFTER_SUBSCRIBE_TIMEOUT_S)

        send_log_messages(
            self.uuid,
            self.device_api_key,
            [
                {"message": "9 message", "timestamp": int(time.time() * 1000)},
                {"message": "10 message", "timestamp": int(time.time() * 1000)},
            ],
            self.balena.settings,
        )

        self.assertEqual(results, [])
