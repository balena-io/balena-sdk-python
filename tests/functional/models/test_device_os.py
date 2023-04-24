import unittest
from balena.models.hup import Hup

from tests.helper import TestHelper


class TestDevice(unittest.TestCase):
    helper = None
    balena = None
    hup = None

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.hup = Hup()
        # Wipe all apps before the tests run.

    @classmethod
    def tearDownClass(cls):
        # Wipe all apps after the tests run.
        cls.helper.wipe_organization()

    def test_01_get_supported_os_versions_by_device_type_slug(self):
        # should become the manifest if the slug is valid.
        supported_device_os_versions = self.balena.models.device_os.get_supported_versions("raspberrypi3")
        self.assertGreater(len(supported_device_os_versions), 0)

    def test_02_get_hup_action_type(self):
        testVersion = [
            "2.108.1+rev2",
            "2.106.7",
            "2.98.11+rev4",
            "2.98.11+rev3",
            "2.98.11+rev2",
            "2.98.11",
            "2.91.5",
            "2.85.2+rev4.prod",
        ]
        for ver in testVersion:
            self.hup.get_hup_action_type("", ver, ver)


if __name__ == "__main__":
    unittest.main()
