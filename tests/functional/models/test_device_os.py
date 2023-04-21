import unittest

from tests.helper import TestHelper


class TestDevice(unittest.TestCase):
    helper = None
    balena = None

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        # Wipe all apps before the tests run.

    @classmethod
    def tearDownClass(cls):
        # Wipe all apps after the tests run.
        cls.helper.wipe_organization()

    def test_01_get_supported_os_versions_by_device_type_slug(self):
        # should become the manifest if the slug is valid.
        supported_device_os_versions = self.balena.models.device_os.get_supported_versions("raspberrypi3")
        self.assertGreater(len(supported_device_os_versions), 0)


if __name__ == "__main__":
    unittest.main()
