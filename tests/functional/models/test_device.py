import unittest
from datetime import datetime
from unittest.mock import patch, Mock

from balena.models.device import LocationType
from tests.helper import TestHelper


class TestDevice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.helper.wipe_application()
        cls.app = cls.balena.models.application.create("FooBar", "raspberry-pi2", cls.helper.default_organization["id"])

    @classmethod
    def tearDownClass(cls):
        cls.helper.wipe_organization()

    def test_01_generate_uuid(self):
        uuid = self.balena.models.device.generate_uuid()
        self.assertEqual(len(uuid), 62)
        self.assertRegex(uuid, "^[a-z0-9]{62}$")

        self.assertNotEqual(
            self.balena.models.device.generate_uuid(),
            self.balena.models.device.generate_uuid(),
        )

    def test_02_get_all_empty(self):
        self.assertEqual(len(self.balena.models.device.get_all()), 0)

    def test_03_register(self):
        self.balena.models.device.register(self.app["id"], self.balena.models.device.generate_uuid())
        self.assertEqual(
            len(self.balena.models.device.get_all_by_application(self.app["id"])),
            1,
        )

        uuid = self.balena.models.device.generate_uuid()
        device = self.balena.models.device.register(self.app["id"], uuid)
        self.assertEqual(device["uuid"], uuid)
        TestDevice.device = device

        uuid = self.balena.models.device.generate_uuid()
        device = self.balena.models.device.register(self.app["id"], uuid, "raspberrypi2")

        self.assertEqual(device["uuid"], uuid)

        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.device.register("999999", self.balena.models.device.generate_uuid())

        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.device.register(
                self.app["id"],
                self.balena.models.device.generate_uuid(),
                "foobarbaz",
            )

        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.device.register(
                self.app["id"],
                self.balena.models.device.generate_uuid(),
                "intel-nuc",
            )

    def test_04_get_all_by_application_id(self):
        app = self.balena.models.application.create("FooBar2", "raspberry-pi2", self.helper.default_organization["id"])

        self.assertEqual(len(self.balena.models.device.get_all_by_application(app["id"])), 0)

        self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())
        self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())
        self.assertEqual(len(self.balena.models.device.get_all_by_application(app["id"])), 2)

    def test_05_get_all_by_application_slug(self):
        app = self.balena.models.application.create("FooBar3", "raspberry-pi2", self.helper.default_organization["id"])
        self.assertEqual(len(self.balena.models.device.get_all_by_application(app["slug"])), 0)

        self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())
        self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())
        self.assertEqual(len(self.balena.models.device.get_all_by_application(app["slug"])), 2)

    def test_06_get_all(self):
        self.assertEqual(len(self.balena.models.device.get_all()), 7)

    def test_07_get(self):
        self.assertEqual(
            self.balena.models.device.get(TestDevice.device["uuid"])["id"],
            TestDevice.device["id"],
        )

        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get("999999999999")

        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.device.get("")

    def test_08_rename(self):
        self.balena.models.device.rename(TestDevice.device["uuid"], "test-device")
        self.assertEqual(self.balena.models.device.get_name(TestDevice.device["uuid"]), "test-device")

    def test_09_get_by_name(self):
        self.assertEqual(
            self.balena.models.device.get_by_name("test-device")[0]["uuid"],
            TestDevice.device["uuid"],
        )

    def test_10_get_name(self):
        self.assertEqual(self.balena.models.device.get_name(TestDevice.device["uuid"]), "test-device")

        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get_name("9999999999999999")

    def test_11_get_status(self):
        self.assertEqual(self.balena.models.device.get_status(TestDevice.device["uuid"]), "inactive")

    def test_12_get_application_name(self):
        self.assertEqual(
            self.balena.models.device.get_application_name(TestDevice.device["uuid"]),
            self.app["app_name"],
        )

        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get_application_name("9999999999999999")

    def test_13_has(self):
        self.assertTrue(self.balena.models.device.has(TestDevice.device["uuid"]))
        self.assertTrue(self.balena.models.device.has(TestDevice.device["uuid"][0:10]))

        self.assertFalse(self.balena.models.device.has("999999999"))

    def test_14_is_online(self):
        self.assertFalse(self.balena.models.device.is_online(TestDevice.device["uuid"]))

        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.is_online("9999999999999999")

    def test_15_note(self):
        self.balena.models.device.set_note(TestDevice.device["uuid"], "Python SDK Test")
        self.assertEqual(
            self.balena.models.device.get(TestDevice.device["uuid"])["note"],
            "Python SDK Test",
        )

    def test_16_enable_device_url(self):
        self.balena.models.device.enable_device_url(TestDevice.device["uuid"])
        self.assertTrue(self.balena.models.device.has_device_url(TestDevice.device["uuid"]))

    def test_17_disable_device_url(self):
        self.balena.models.device.enable_device_url(TestDevice.device["uuid"])
        self.balena.models.device.disable_device_url(TestDevice.device["uuid"])
        self.assertFalse(self.balena.models.device.has_device_url(TestDevice.device["uuid"]))

    def test_18_move(self):
        device = self.balena.models.device.register(self.app["id"], self.balena.models.device.generate_uuid())
        app1 = self.balena.models.application.create(
            "FooBarBar", "raspberry-pi2", self.helper.default_organization["id"]
        )
        app2 = self.balena.models.application.create(
            "FooBarBar3", "raspberrypi3", self.helper.default_organization["id"]
        )

        self.balena.models.device.move(device["uuid"], app1["slug"])
        self.assertEqual(self.balena.models.device.get_application_name(device["uuid"]), app1["app_name"])

        self.balena.models.device.move(device["uuid"], app2["slug"])
        self.assertEqual(self.balena.models.device.get_application_name(device["uuid"]), app2["app_name"])

        app3 = self.balena.models.application.create(
            "FooBarBarBar", "intel-nuc", self.helper.default_organization["id"]
        )
        with self.assertRaises(self.helper.balena_exceptions.IncompatibleApplication):
            self.balena.models.device.move(device["uuid"], app3["slug"])

    def test_19_set_custom_location(self):
        location: LocationType = {"latitude": "41.383333", "longitude": "2.183333"}

        self.balena.models.device.set_custom_location(TestDevice.device["uuid"], location)
        device = self.balena.models.device.get(TestDevice.device["uuid"])
        self.assertEqual(device["custom_latitude"], "41.383333")
        self.assertEqual(device["custom_longitude"], "2.183333")

    def test_20_unset_custom_location(self):
        location: LocationType = {"latitude": "41.383333", "longitude": "2.183333"}
        self.balena.models.device.set_custom_location(TestDevice.device["uuid"], location)

        self.balena.models.device.unset_custom_location(TestDevice.device["uuid"])
        device = self.balena.models.device.get(TestDevice.device["uuid"])
        self.assertEqual(device["custom_latitude"], "")
        self.assertEqual(device["custom_longitude"], "")

    def test_21_grant_support_access(self):
        expiry_timestamp = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) - 10000)

        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.device.grant_support_access(TestDevice.device["uuid"], expiry_timestamp)

        expiry_time = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) + 3600 * 1000)
        self.balena.models.device.grant_support_access(TestDevice.device["uuid"], expiry_time)
        support_date = datetime.strptime(  # type: ignore
            self.balena.models.device.get(TestDevice.device["uuid"])["is_accessible_by_support_until__date"],
            "%Y-%m-%dT%H:%M:%S.%fZ",
        )
        self.assertEqual(self.helper.datetime_to_epoch_ms(support_date), expiry_time)

    def test_22_revoke_support_access(self):
        self.balena.models.device.revoke_support_access(TestDevice.device["uuid"])
        self.assertIsNone(
            self.balena.models.device.get(TestDevice.device["uuid"])["is_accessible_by_support_until__date"]
        )

    def test_23_is_tracking_application_release(self):
        self.assertTrue(self.balena.models.device.is_tracking_application_release(TestDevice.device["uuid"]))

    def test_24_track_application_release(self):
        app_info = self.helper.create_multicontainer_app(app_name="FooBarMC")

        self.balena.models.device.pin_to_release(app_info["device"]["uuid"], app_info["old_release"]["commit"])
        self.assertFalse(self.balena.models.device.is_tracking_application_release(app_info["device"]["uuid"]))
        self.balena.models.device.track_application_release(app_info["device"]["uuid"])
        self.assertTrue(self.balena.models.device.is_tracking_application_release(app_info["device"]["uuid"]))

    def test_25_has_lock_override(self):
        self.assertFalse(self.balena.models.device.has_lock_override(TestDevice.device["uuid"]))
        self.balena.models.device.enable_lock_override(TestDevice.device["uuid"])
        self.assertTrue(self.balena.models.device.has_lock_override(TestDevice.device["uuid"]))
        self.balena.models.device.disable_lock_override(TestDevice.device["uuid"])
        self.assertFalse(self.balena.models.device.has_lock_override(TestDevice.device["uuid"]))

    def test_26_get_supervisor_state(self):
        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get_supervisor_state("9999999")

        with self.assertRaises(Exception) as cm:
            self.balena.models.device.get_supervisor_state(TestDevice.device["uuid"])
        self.assertIn("No online device(s) found", str(cm.exception))

    def test_27_get_supervisor_target_state(self):
        supervisor_target_state = self.balena.models.device.get_supervisor_target_state(TestDevice.device["uuid"])
        self.assertEqual(
            int(list(supervisor_target_state["local"]["apps"].keys())[0]),
            self.app["id"],
        )
        self.assertEqual(
            supervisor_target_state["local"]["apps"]["{}".format(self.app["id"])]["name"],
            self.app["app_name"],
        )

        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get_supervisor_target_state("9999999")

    def test_28_get_supervisor_target_state_for_app(self):
        state = self.balena.models.device.get_supervisor_target_state_for_app(self.app["id"])

        self.assertEqual(state[self.app["uuid"]]["name"], self.app["app_name"])

        self.assertEqual(state[self.app["uuid"]]["config"]["RESIN_SUPERVISOR_NATIVE_LOGGER"], "true")

        self.assertEqual(state[self.app["uuid"]]["config"]["RESIN_SUPERVISOR_POLL_INTERVAL"], "900000")

    def __reset_mock(self, mock_request):
        mock_request.reset_mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response
        return mock_request

    @patch.dict(
        "os.environ",
        {
            "BALENA_SUPERVISOR_ADDRESS": "http://localhost:1337",
            "BALENA_SUPERVISOR_API_KEY": "key",
            "BALENA_APP_ID": "123",
        },
    )
    def test_29_sdk_on_device(self):
        other_helper = TestHelper()

        with patch("requests.request") as mock_request:
            self.__reset_mock(mock_request)
            other_helper.balena.models.device.ping()
            mock_request.assert_called_once_with(
                method="GET", url="http://localhost:1337/ping", json=None, params={"apikey": "key"}
            )

            self.__reset_mock(mock_request)
            other_helper.balena.models.device.identify()
            mock_request.assert_called_once_with(
                method="POST", url="http://localhost:1337/v1/blink", json=None, params={"apikey": "key"}
            )

            self.__reset_mock(mock_request)
            other_helper.balena.models.device.restart_application()
            mock_request.assert_called_once_with(
                method="POST", url="http://localhost:1337/v1/restart", json={"appId": "123"}, params={"apikey": "key"}
            )

            self.__reset_mock(mock_request)
            other_helper.balena.models.device.purge()
            mock_request.assert_called_once_with(
                method="POST", url="http://localhost:1337/v1/purge", json={"appId": "123"}, params={"apikey": "key"}
            )

            self.__reset_mock(mock_request)
            other_helper.balena.models.device.reboot()
            mock_request.assert_called_once_with(
                method="POST", url="http://localhost:1337/v1/reboot", json={}, params={"apikey": "key"}
            )

            self.__reset_mock(mock_request)
            other_helper.balena.models.device.shutdown()
            mock_request.assert_called_once_with(
                method="POST", url="http://localhost:1337/v1/shutdown", json={}, params={"apikey": "key"}
            )

            self.__reset_mock(mock_request)
            other_helper.balena.models.device.update()
            mock_request.assert_called_once_with(
                method="POST", url="http://localhost:1337/v1/update", json={}, params={"apikey": "key"}
            )

            self.__reset_mock(mock_request)
            other_helper.balena.models.device.start_service(None, 444)
            mock_request.assert_called_once_with(
                method="POST",
                url="http://localhost:1337/v2/applications/123/start-service",
                json={"imageId": 444},
                params={"apikey": "key"},
            )

            self.__reset_mock(mock_request)
            other_helper.balena.models.device.stop_service(None, 444)
            mock_request.assert_called_once_with(
                method="POST",
                url="http://localhost:1337/v2/applications/123/stop-service",
                json={"imageId": 444},
                params={"apikey": "key"},
            )

            self.__reset_mock(mock_request)
            other_helper.balena.models.device.restart_service(None, 444)
            mock_request.assert_called_once_with(
                method="POST",
                url="http://localhost:1337/v2/applications/123/restart-service",
                json={"imageId": 444},
                params={"apikey": "key"},
            )

            mock_request.reset_mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "api_port": "1337",
            }
            mock_request.return_value = mock_response
            res = other_helper.balena.models.device.get_supervisor_state()
            mock_request.assert_called_once_with(
                method="GET", url="http://localhost:1337/v1/device", json=None, params={"apikey": "key"}
            )
            self.assertEqual(res["api_port"], "1337")

    def test_30_remove(self):
        all_devices_len = len(self.balena.models.device.get_all())
        app_devices_len = len(self.balena.models.device.get_all_by_application(self.app["id"]))
        self.balena.models.device.remove(TestDevice.device["uuid"])
        self.assertEqual(len(self.balena.models.device.get_all()), all_devices_len - 1)
        self.assertEqual(
            len(self.balena.models.device.get_all_by_application(self.app["id"])),
            app_devices_len - 1,
        )

        uuid = self.balena.models.device.generate_uuid()
        self.balena.models.device.register(self.app["id"], uuid)
        uuid2 = uuid[:-2] + uuid[-1] + uuid[-2]

        self.balena.models.device.register(self.app["id"], uuid2)

        device_uuids = [device["uuid"] for device in self.balena.models.device.get_all()]
        self.assertIn(uuid, device_uuids)
        self.assertIn(uuid2, device_uuids)

        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get(TestDevice.device["uuid"])

        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.device.remove("")

        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.device.remove("abc")

        with self.assertRaises(self.helper.balena_exceptions.AmbiguousDevice):
            self.balena.models.device.remove(uuid[0:10])

        device_uuids = [device["uuid"] for device in self.balena.models.device.get_all()]
        self.assertIn(uuid, device_uuids)
        self.assertIn(uuid2, device_uuids)

        self.balena.models.device.remove(uuid)
        self.balena.models.device.remove(uuid2)

        device_uuids = [device["uuid"] for device in self.balena.models.device.get_all()]
        self.assertNotIn(uuid, device_uuids)
        self.assertNotIn(uuid2, device_uuids)


if __name__ == "__main__":
    unittest.main()
