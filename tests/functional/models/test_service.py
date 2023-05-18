import unittest

from tests.helper import TestHelper


class TestImage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.app = cls.helper.create_multicontainer_app()["app"]
        cls.empty_app = cls.balena.models.application.create(
            "ServiceTestApp", "raspberry-pi2", cls.helper.default_organization["id"]
        )

    @classmethod
    def tearDownClass(cls):
        cls.helper.wipe_application()

    def test_01_should_reject_if_application_does_not_exist(self):
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.service.get_all_by_application(123)

        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.service.get_all_by_application("AppDoesNotExist")

    def test_02_should_get_image(self):
        for prop in self.helper.application_retrieval_fields:
            services = self.balena.models.service.get_all_by_application(self.empty_app[prop])
            self.assertEqual(services, [])

    def test_03_should_get_image_build_logs(self):
        services = self.balena.models.service.get_all_by_application(self.app["id"])
        services = sorted(services, key=lambda s: s["service_name"])
        self.assertEqual(services[0]["service_name"], "db")
        self.assertEqual(services[0]["application"]["__id"], self.app["id"])
        self.assertEqual(services[1]["service_name"], "web")
        self.assertEqual(services[1]["application"]["__id"], self.app["id"])
