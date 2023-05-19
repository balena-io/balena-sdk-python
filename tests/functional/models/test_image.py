import unittest

from tests.helper import TestHelper


class TestImage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.current_web_image = cls.helper.create_multicontainer_app()["current_web_image"]

    @classmethod
    def tearDownClass(cls):
        cls.helper.wipe_application()

    def test_01_should_reject_if_image_id_does_not_exist(self):
        with self.assertRaises(self.helper.balena_exceptions.ImageNotFound):
            self.balena.models.image.get(123)

        with self.assertRaises(self.helper.balena_exceptions.ImageNotFound):
            self.balena.models.image.get_logs(123)

    def test_02_should_get_image(self):
        id = self.current_web_image["id"]
        img = self.balena.models.image.get(id)
        self.assertEqual(img["project_type"], "dockerfile")
        self.assertEqual(img["status"], "success")
        self.assertEqual(img["id"], id)
        self.assertIsNone(img.get("build_log"))

    def test_03_should_get_image_build_logs(self):
        id = self.current_web_image["id"]
        logs = self.balena.models.image.get_logs(id)
        self.assertEqual(logs, "new web log")
