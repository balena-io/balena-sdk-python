import unittest
from datetime import datetime

from tests.helper import TestHelper


class TestDevice(unittest.TestCase):
    helper = None
    balena = None
    app = None
    device = None

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        # Wipe all apps before the tests run.
        cls.helper.wipe_application()
        cls.app = cls.balena.models.application.create("FooBar", "raspberry-pi2", cls.helper.default_organization["id"])

    @classmethod
    def tearDownClass(cls):
        # Wipe all apps after the tests run.
        cls.helper.wipe_organization()

    def test_01_generate_uuid(self):
        # should generate a valid uuid.
        uuid = self.balena.models.device.generate_uuid()
        self.assertEqual(len(uuid), 62)
        self.assertRegex(uuid, "^[a-z0-9]{62}$")

        # should generate different uuids.
        self.assertNotEqual(
            self.balena.models.device.generate_uuid(),
            self.balena.models.device.generate_uuid(),
        )

    def test_02_get_all_empty(self):
        # should return empty list.
        self.assertEqual(len(self.balena.models.device.get_all()), 0)

    def test_03_register(self):
        # should be able to register a device to a valid application id.
        self.balena.models.device.register(type(self).app["id"], self.balena.models.device.generate_uuid())
        self.assertEqual(
            len(self.balena.models.device.get_all_by_application(type(self).app["id"])),
            1,
        )

        # should become valid device registration info.
        uuid = self.balena.models.device.generate_uuid()
        device = self.balena.models.device.register(type(self).app["id"], uuid)
        self.assertEqual(device["uuid"], uuid)
        type(self).device = device

        # should be able to register a device with a valid device type.
        uuid = self.balena.models.device.generate_uuid()
        device = self.balena.models.device.register(type(self).app["id"], uuid, "raspberrypi2")

        self.assertEqual(device["uuid"], uuid)

        # should be rejected if the application id does not exist.
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.device.register("999999", self.balena.models.device.generate_uuid())

        # should be rejected if the provided device type does not exist.
        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.device.register(
                type(self).app["id"],
                self.balena.models.device.generate_uuid(),
                "foobarbaz",
            )

        # should be rejected when providing a device type incompatible with the application.
        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.device.register(
                type(self).app["id"],
                self.balena.models.device.generate_uuid(),
                "intel-nuc",
            )

    def test_04_get_all_by_application_id(self):
        app = self.balena.models.application.create("FooBar2", "raspberry-pi2", self.helper.default_organization["id"])
        # should return empty

        self.assertEqual(len(self.balena.models.device.get_all_by_application(app["id"])), 0)

        # should return correct number of device in an application.
        self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())
        self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())
        self.assertEqual(len(self.balena.models.device.get_all_by_application(app["id"])), 2)

    def test_05_get_all_by_application_slug(self):
        app = self.balena.models.application.create("FooBar3", "raspberry-pi2", self.helper.default_organization["id"])
        # should return empty
        self.assertEqual(len(self.balena.models.device.get_all_by_application(app["slug"])), 0)

        # should return correct number of device in an application.
        self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())
        self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())
        self.assertEqual(len(self.balena.models.device.get_all_by_application(app["slug"])), 2)

    def test_06_get_all(self):
        # should return correct total of device in all applications.
        self.assertEqual(len(self.balena.models.device.get_all()), 7)

    def test_07_get(self):
        # should be able to get the device by uuid.
        self.assertEqual(
            self.balena.models.device.get(type(self).device["uuid"])["id"],
            type(self).device["id"],
        )

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get("999999999999")

    def test_08_rename(self):
        # should be able to rename the device by uuid.
        self.balena.models.device.rename(type(self).device["uuid"], "test-device")
        self.assertEqual(self.balena.models.device.get_name(type(self).device["uuid"]), "test-device")

    def test_09_get_by_name(self):
        # should be able to get the device.
        self.assertEqual(
            self.balena.models.device.get_by_name("test-device")[0]["uuid"],
            type(self).device["uuid"],
        )

    def test_10_get_name(self):
        # should get the correct name by uuid.
        self.assertEqual(self.balena.models.device.get_name(type(self).device["uuid"]), "test-device")

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get_name("9999999999999999")

    def test_11_get_status(self):
        # should be able to get the device's status.
        self.assertEqual(self.balena.models.device.get_status(type(self).device["uuid"]), "inactive")

    def test_12_get_application_name(self):
        # should get the correct application name from a device uuid.
        self.assertEqual(
            self.balena.models.device.get_application_name(type(self).device["uuid"]),
            type(self).app["app_name"],
        )

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get_application_name("9999999999999999")

    def test_13_has(self):
        # should eventually be true if the device uuid exists.
        self.assertTrue(self.balena.models.device.has(type(self).device["uuid"]))
        self.assertTrue(self.balena.models.device.has(type(self).device["uuid"][0:10]))

        # should eventually be false if the device uuid does not exist.
        self.assertFalse(self.balena.models.device.has("999999999"))

    def test_14_is_online(self):
        # should eventually be false if the device uuid exists.
        self.assertFalse(self.balena.models.device.is_online(type(self).device["uuid"]))

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.is_online("9999999999999999")

    def test_15_note(self):
        # should be able to note a device by uuid.
        self.balena.models.device.note(type(self).device["uuid"], "Python SDK Test")
        self.assertEqual(
            self.balena.models.device.get(type(self).device["uuid"])["note"],
            "Python SDK Test",
        )

    def test_16_enable_device_url(self):
        # should be able to enable web access using a uuid.
        self.balena.models.device.enable_device_url(type(self).device["uuid"])
        self.assertTrue(self.balena.models.device.has_device_url(type(self).device["uuid"]))

    def test_17_disable_device_url(self):
        # should be able to disable web access using a uuid.
        self.balena.models.device.enable_device_url(type(self).device["uuid"])
        self.balena.models.device.disable_device_url(type(self).device["uuid"])
        self.assertFalse(self.balena.models.device.has_device_url(type(self).device["uuid"]))

    def test_18_move(self):
        device = self.balena.models.device.register(type(self).app["id"], self.balena.models.device.generate_uuid())
        app1 = self.balena.models.application.create(
            "FooBarBar", "raspberry-pi2", self.helper.default_organization["id"]
        )
        app2 = self.balena.models.application.create(
            "FooBarBar3", "raspberrypi3", self.helper.default_organization["id"]
        )

        # should be able to move a device by device uuid and application slug.
        self.balena.models.device.move(device["uuid"], app1["slug"])
        self.assertEqual(self.balena.models.device.get_application_name(device["uuid"]), app1["app_name"])

        # should be able to move a device to an application of the same architecture.
        self.balena.models.device.move(device["uuid"], app2["slug"])
        self.assertEqual(self.balena.models.device.get_application_name(device["uuid"]), app2["app_name"])

        # should be rejected with an incompatibility error.
        app3 = self.balena.models.application.create(
            "FooBarBarBar", "intel-nuc", self.helper.default_organization["id"]
        )
        with self.assertRaises(self.helper.balena_exceptions.IncompatibleApplication):
            self.balena.models.device.move(device["uuid"], app3["slug"])

    def test_19_set_custom_location(self):
        location = {"latitude": "41.383333", "longitude": "2.183333"}

        # should be able to set the location of a device by uuid.
        self.balena.models.device.set_custom_location(type(self).device["uuid"], location)
        device = self.balena.models.device.get(type(self).device["uuid"])
        self.assertEqual(device["custom_latitude"], "41.383333")
        self.assertEqual(device["custom_longitude"], "2.183333")

    def test_20_unset_custom_location(self):
        location = {"latitude": "41.383333", "longitude": "2.183333"}
        self.balena.models.device.set_custom_location(type(self).device["uuid"], location)

        # should be able to unset the location of a device by uuid.
        self.balena.models.device.unset_custom_location(type(self).device["uuid"])
        device = self.balena.models.device.get(type(self).device["uuid"])
        self.assertEqual(device["custom_latitude"], "")
        self.assertEqual(device["custom_longitude"], "")

    def test_21_grant_support_access(self):
        # should throw an error if the expiry timestamp is in the past.
        expiry_timestamp = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) - 10000)

        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.device.grant_support_access(type(self).device["uuid"], expiry_timestamp)

        # should grant support access for the correct amount of time.
        expiry_time = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) + 3600 * 1000)
        self.balena.models.device.grant_support_access(type(self).device["uuid"], expiry_time)
        support_date = datetime.strptime(
            self.balena.models.device.get(type(self).device["uuid"])["is_accessible_by_support_until__date"],
            "%Y-%m-%dT%H:%M:%S.%fZ",
        )
        self.assertEqual(self.helper.datetime_to_epoch_ms(support_date), expiry_time)

    def test_22_revoke_support_access(self):
        # should revoke support access
        self.balena.models.device.revoke_support_access(type(self).device["uuid"])
        self.assertIsNone(
            self.balena.models.device.get(type(self).device["uuid"])["is_accessible_by_support_until__date"]
        )

    def test_23_is_tracking_application_release(self):
        # should be tracking the latest release by default.
        self.assertTrue(self.balena.models.device.is_tracking_application_release(type(self).device["uuid"]))

    def test_24_track_application_release(self):
        app_info = self.helper.create_multicontainer_app(app_name="FooBarMC")

        # should set the device to track the current application release.
        self.balena.models.device.pin_to_release(app_info["device"]["uuid"], app_info["old_release"]["commit"])
        self.assertFalse(self.balena.models.device.is_tracking_application_release(app_info["device"]["uuid"]))
        self.balena.models.device.track_application_release(app_info["device"]["uuid"])
        self.assertTrue(self.balena.models.device.is_tracking_application_release(app_info["device"]["uuid"]))

    def test_25_has_lock_override(self):
        # should be false by default for a device.
        self.assertFalse(self.balena.models.device.has_lock_override(type(self).device["uuid"]))
        self.balena.models.device.enable_lock_override(type(self).device["uuid"])
        self.assertTrue(self.balena.models.device.has_lock_override(type(self).device["uuid"]))
        self.balena.models.device.disable_lock_override(type(self).device["uuid"])
        self.assertFalse(self.balena.models.device.has_lock_override(type(self).device["uuid"]))

    def test_26_get_supervisor_state(self):
        # should be rejected if the device doesn't exist.
        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get_supervisor_state("9999999")

        # should be rejected if the device is not online
        with self.assertRaises(Exception) as cm:
            self.balena.models.device.get_supervisor_state(type(self).device["uuid"])
        self.assertIn("No online device(s) found", str(cm.exception))

    def test_27_get_supervisor_target_state(self):
        # should match device and app
        supervisor_target_state = self.balena.models.device.get_supervisor_target_state(type(self).device["uuid"])
        self.assertEqual(
            int(list(supervisor_target_state["local"]["apps"].keys())[0]),
            type(self).app["id"],
        )
        self.assertEqual(
            supervisor_target_state["local"]["apps"]["{}".format(type(self).app["id"])]["name"],
            type(self).app["app_name"],
        )

        # should be rejected if the device doesn't exist.
        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get_supervisor_target_state("9999999")

    def test_28_remove(self):
        all_devices_len = len(self.balena.models.device.get_all())
        app_devices_len = len(self.balena.models.device.get_all_by_application(type(self).app["id"]))
        # should be able to remove the device by uuid
        self.balena.models.device.remove(type(self).device["uuid"])
        self.assertEqual(len(self.balena.models.device.get_all()), all_devices_len - 1)
        self.assertEqual(
            len(self.balena.models.device.get_all_by_application(type(self).app["id"])),
            app_devices_len - 1,
        )

        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.get(type(self).device["uuid"])


if __name__ == "__main__":
    unittest.main()
