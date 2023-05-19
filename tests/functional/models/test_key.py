import unittest

from tests.helper import TestHelper

PUBLIC_KEY = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDMBWf5hwmL97rtCD8Gljz30+25vLAV8jumD9SPG9JxNbBTVot1tYNQw6rvpdN/dLlf13G1qG9AMkAwlgRFXPDFrVheKH13HzGJZYTu7sKLENHMFKzdANa5XHoVX9kthbYsJT0mBPtxRfSxhx6ALapfr8zqdAQSxspsMzwiTTRoVwIRQthEWxqSASpOYw2/OFwKgZdg0EbHQHUJgOa2bSd6lxAU3o3zbnG/8Bww9b8/avS0GCZ9XnLT0RSBMrtxzLKt+mr22pUDmwFMq275rxUqjQmdRChpLcizaJAiSxSTdaRwWphtf/8myKwezgmH8pbU7WkHUU6xEJz6xRj2P0ZB 
"""  # noqa


class TestKey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena

    @classmethod
    def tearDownClass(cls):
        cls.helper.wipe_application()
        cls.helper.reset_user()

    def test_01_should_be_empty_array(self):
        result = self.balena.models.key.get_all()
        self.assertEqual(result, [])

    def test_02_should_be_able_to_create_key_with_whitespaces(self):
        key = self.balena.models.key.create("MyKey", f"    {PUBLIC_KEY}    ")

        self.assertEqual(key["title"], "MyKey")
        self.assertEqual(key["public_key"].strip(" \n"), PUBLIC_KEY.strip(" \n"))

        result = self.balena.models.key.get_all()
        self.assertEqual(result[0]["title"], "MyKey")
        self.assertEqual(result[0]["public_key"].strip(" \n"), PUBLIC_KEY.strip(" \n"))

    def test_03_should_be_able_to_create_key(self):
        self.helper.reset_user()
        TestKey.key = self.balena.models.key.create("MyKey", PUBLIC_KEY)

        self.assertEqual(TestKey.key["title"], "MyKey")
        self.assertEqual(TestKey.key["public_key"].strip(" \n"), PUBLIC_KEY.strip(" \n"))

        result = self.balena.models.key.get_all()
        self.assertEqual(result[0]["title"], "MyKey")
        self.assertEqual(result[0]["public_key"].strip(" \n"), PUBLIC_KEY.strip(" \n"))

    def test_04_should_support_pinejs_options(self):
        [key] = self.balena.models.key.get_all(
            {
                "$select": ["public_key"],
            }
        )

        self.assertEqual(key["public_key"].strip(" \n"), PUBLIC_KEY.strip(" \n"))
        self.assertIsNone(key.get("title"))

    def test_05_should_get_key(self):
        key = self.balena.models.key.get(TestKey.key["id"])

        self.assertEqual(key["public_key"].strip(" \n"), PUBLIC_KEY.strip(" \n"))
        self.assertEqual(key["title"], "MyKey")

        with self.assertRaises(self.helper.balena_exceptions.RequestError):
            self.balena.models.key.get(99999999999)

    def test_06_should_remove_key(self):
        self.balena.models.key.remove(TestKey.key["id"])

        with self.assertRaises(self.helper.balena_exceptions.KeyNotFound):
            self.balena.models.key.get(TestKey.key["id"])
        self.assertEqual(self.balena.models.key.get_all(), [])
