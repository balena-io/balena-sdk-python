import unittest

from tests.helper import TestHelper


class TestDeviceType(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena

    def tearDown(self):
        # Wipe all apps after every test case.
        self.helper.wipe_application()

    def test_get(self):
        # should get the device type for a known slug.
        dt = self.balena.models.device_type.get("raspberry-pi")
        self.assertEqual(dt["slug"], "raspberry-pi")
        self.assertEqual(dt["name"], "Raspberry Pi (v1 / Zero / Zero W)")

        # should get the device type for a known id.
        dt = self.balena.models.device_type.get(dt["id"])
        self.assertEqual(dt["slug"], "raspberry-pi")
        self.assertEqual(dt["name"], "Raspberry Pi (v1 / Zero / Zero W)")

        # should be rejected if the slug is invalid.
        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.device_type.get("PYTHONSDK")

        # should be rejected if the id is invalid.
        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.device_type.get(99999)

    def test_get_by_slug_or_name(self):
        # should be the slug from a display name.
        dt = self.balena.models.device_type.get_by_slug_or_name("Raspberry Pi (v1 / Zero / Zero W)")
        self.assertEqual(dt["slug"], "raspberry-pi")
        self.assertEqual(dt["name"], "Raspberry Pi (v1 / Zero / Zero W)")

        dt = self.balena.models.device_type.get_by_slug_or_name("raspberry-pi")
        self.assertEqual(dt["slug"], "raspberry-pi")
        self.assertEqual(dt["name"], "Raspberry Pi (v1 / Zero / Zero W)")

        # should be rejected if the display name is invalid.
        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.device_type.get("PYTHONSDK")

    def test_get_name(self):
        # should get the display name for a known slug.
        self.assertEqual(
            self.balena.models.device_type.get_name("raspberry-pi"),
            "Raspberry Pi (v1 / Zero / Zero W)",
        )

        # should be rejected if the slug is invalid.
        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.device_type.get_name("PYTHONSDK")

    def test_get_slug_by_name(self):
        # should get the display name for a known name.
        self.assertEqual(
            self.balena.models.device_type.get_slug_by_name("Raspberry Pi (v1 / Zero / Zero W)"),
            "raspberry-pi",
        )

        # should be rejected if the slug is invalid.
        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.device_type.get_slug_by_name("PYTHONSDK")

    def test_get_supported_device_types(self):
        # should return a non empty array.
        self.assertGreater(len(self.balena.models.device_type.get_all_supported()), 0)

        # should return all valid display names.
        for dev_type in self.balena.models.device_type.get_all_supported():
            self.assertTrue(self.balena.models.device_type.get(dev_type["slug"]))


if __name__ == "__main__":
    unittest.main()
