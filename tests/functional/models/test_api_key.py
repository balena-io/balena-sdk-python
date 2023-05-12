import unittest

from tests.helper import TestHelper


class TestApiKey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.helper.wipe_application()
        cls.helper.reset_user()
        cls.app_info = cls.helper.create_multicontainer_app()
        cls.device = cls.balena.models.device.register(
            cls.app_info["app"]["id"], cls.balena.models.device.generate_uuid()
        )

        cls.balena.models.application.generate_provisioning_key(cls.app_info["app"]["id"], "provisionTestKey")
        cls.balena.models.device.generate_device_key(cls.device["uuid"], "deviceTestKey")

    @classmethod
    def tearDownClass(cls):
        cls.helper.wipe_organization()
        cls.helper.wipe_application()

    def __assert_matching_keys(self, expected_keys, actual_keys):
        expected_set = set((d["name"], d["description"]) for d in expected_keys)
        actual_set = set((d["name"], d["description"]) for d in actual_keys)

        self.assertEqual(expected_set, actual_set)
        for key in actual_keys:
            self.assertIsInstance(key["id"], int)
            self.assertIsInstance(key["created_at"], str)

    def test_01_create_api_key(self):
        key = self.balena.models.api_key.create("apiKey1")
        self.assertIsInstance(key, str)

    def test_02_create_api_key_wth_description(self):
        key = self.balena.models.api_key.create("apiKey2", "apiKey2Description")
        self.assertIsInstance(key, str)

    def test_03_get_all_named_user_api_keys(self):
        keys = self.balena.models.api_key.get_all_named_user_api_keys()
        TestApiKey.named_user_api_key = keys[0]
        self.__assert_matching_keys(
            [
                {
                    "name": "apiKey1",
                    "description": None,
                },
                {
                    "name": "apiKey2",
                    "description": "apiKey2Description",
                },
            ],
            keys,
        )

    def test_04_get_provisioning_api_keys_by_application_for_non_existing(self):
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.api_key.get_provisioning_api_keys_by_application(
                "nonExistentOrganization/nonExistentApp"
            )

    def test_05_get_provisioning_api_keys_by_application(self):
        keys = self.balena.models.api_key.get_provisioning_api_keys_by_application(self.app_info["app"]["id"])
        provisioning_keys_names = set(map(lambda k: k["name"], keys))
        self.assertIn("provisionTestKey", provisioning_keys_names)

    def test_06_get_device_api_keys_by_device_for_non_existing(self):
        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.balena.models.api_key.get_device_api_keys_by_device("nonexistentuuid")

    def test_07_get_device_api_keys_by_device_for_non_existing(self):
        keys = self.balena.models.api_key.get_device_api_keys_by_device(self.device["uuid"])
        device_keys_names = set(map(lambda k: k["name"], keys))
        self.assertIn("deviceTestKey", device_keys_names)

    def test_08_should_be_able_to_update_a_key_name(self):
        app_key_id = TestApiKey.named_user_api_key["id"]
        self.balena.models.api_key.update(app_key_id, {"name": "updatedApiKeyName"})

        keys = self.balena.models.api_key.get_all_named_user_api_keys()
        names = set(map(lambda k: k["name"], keys))
        self.assertIn("updatedApiKeyName", names)

    def test_09_should_be_able_to_update_a_key_descr(self):
        app_key_id = TestApiKey.named_user_api_key["id"]
        self.balena.models.api_key.update(app_key_id, {"description": "updatedApiKeyDescription"})

        keys = self.balena.models.api_key.get_all_named_user_api_keys()
        new_description = [k for k in keys if k["name"] == "updatedApiKeyName"][0]["description"]
        self.assertEqual(new_description, "updatedApiKeyDescription")

    def test_10_update_to_set_null_to_key_descr(self):
        app_key_id = TestApiKey.named_user_api_key["id"]
        self.balena.models.api_key.update(app_key_id, {"description": None})

        keys = self.balena.models.api_key.get_all_named_user_api_keys()
        new_description = [k for k in keys if k["name"] == "updatedApiKeyName"][0]["description"]
        self.assertIsNone(new_description)

    def test_11_update_to_set_empty_str_to_key_descr(self):
        app_key_id = TestApiKey.named_user_api_key["id"]
        self.balena.models.api_key.update(app_key_id, {"description": ""})

        keys = self.balena.models.api_key.get_all_named_user_api_keys()
        new_description = [k for k in keys if k["name"] == "updatedApiKeyName"][0]["description"]
        self.assertEqual(new_description, "")

    def test_12_revoke(self):
        app_key_id = TestApiKey.named_user_api_key["id"]
        self.balena.models.api_key.revoke(app_key_id)
        keys = self.balena.models.api_key.get_all_named_user_api_keys()
        ids = set(map(lambda k: k["id"], keys))

        self.assertNotIn(app_key_id, ids)


if __name__ == "__main__":
    unittest.main()
