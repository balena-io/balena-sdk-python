import unittest

from balena.hup import get_hup_action_type
from tests.helper import TestHelper


class TestDevice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena

    @classmethod
    def tearDownClass(cls):
        cls.helper.wipe_organization()

    def test_01_get_supported_os_versions_by_device_type_slug(self):
        # should become the manifest if the slug is valid.
        supported_device_os_versions = self.balena.models.os.get_supported_os_update_versions(
            "raspberrypi3", "2.9.6+rev1.prod"
        )
        self.assertEqual(supported_device_os_versions["current"], "2.9.6+rev1.prod")
        self.assertIsInstance(supported_device_os_versions["recommended"], str)
        self.assertIsInstance(supported_device_os_versions["versions"], list)
        self.assertGreater(len(supported_device_os_versions["versions"]), 2)

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
            get_hup_action_type("", ver, ver)


if __name__ == "__main__":
    unittest.main()
