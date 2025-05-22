import unittest

from balena.hup import get_hup_action_type
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
        # Ensure version advances
        testVersion = [
            "2.85.2+rev4.prod",
            "2.91.5",
            "2.98.11",
            "2.98.11+rev2",
            "2.98.11+rev3",
            "2.98.11+rev4",
            "2.106.7",
            "2.108.1+rev2"
        ]
        last_ver = testVersion[0]
        for ver in testVersion[1:]:
            get_hup_action_type("", last_ver, ver)
            last_ver = ver

    def test_03_get_supervisor_releases_for_cpu_architecture(self):
        # return an empty array if no image was found
        svRelease = self.balena.models.os.get_supervisor_releases_for_cpu_architecture("notACpuArch")
        self.assertEqual(svRelease, [])

        # by default include the id, semver and known_issue_list
        dt = self.balena.models.device_type.get(
            "raspberrypi4-64", {"$select": "slug", "$expand": {"is_of__cpu_architecture": {"$select": "slug"}}}
        )

        svReleases = self.balena.models.os.get_supervisor_releases_for_cpu_architecture(
            dt["is_of__cpu_architecture"][0]["slug"]
        )

        self.assertGreater(len(svReleases), 0)
        svRelease = svReleases[0]
        self.assertListEqual(sorted(svRelease.keys()), sorted(["id", "raw_version", "known_issue_list"]))

        # return the right string when asking for raspberrypi4-64 and v12.11.0
        dt = self.balena.models.device_type.get(
            "raspberrypi4-64", {"$select": "slug", "$expand": {"is_of__cpu_architecture": {"$select": "slug"}}}
        )
        svReleases = self.balena.models.os.get_supervisor_releases_for_cpu_architecture(
            dt["is_of__cpu_architecture"][0]["slug"],
            {
                "$select": "id",
                "$expand": {
                    "release_image": {
                        "$select": "id",
                        "$expand": {"image": {"$select": "is_stored_at__image_location"}},
                    },
                },
                "$filter": {"raw_version": "12.11.0"},
            },
        )

        self.assertEqual(len(svReleases), 1)
        svRelease = svReleases[0]
        imageLocation = svRelease["release_image"][0]["image"][0]["is_stored_at__image_location"]
        self.assertRegex(imageLocation, r"registry2\.[a-z0-9_\-.]+\.[a-z]+\/v2\/[0-9a-f]+")
        self.assertEqual(imageLocation, "registry2.balena-cloud.com/v2/4ca706e1c624daff7e519b3009746b2c")

    def test_04_start_os_update(self):
        uuid = self.balena.models.device.generate_uuid()
        device = self.balena.models.device.register(self.app["id"], uuid)
        # sanity check
        self.assertEqual(device["uuid"], uuid)
        device["is_online"] = False
        self.assertEqual(device["is_online"], False)

        # Perform sanity checks on input
        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.device.start_os_update('999999999999', '6.0.10')

        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.device.start_os_update(uuid, None)
        # device is offline
        with self.assertRaises(self.helper.balena_exceptions.OsUpdateError):
            self.balena.models.device.start_os_update(uuid, '99.99.0')


if __name__ == "__main__":
    unittest.main()
