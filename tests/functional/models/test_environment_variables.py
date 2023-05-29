import unittest

from tests.helper import TestHelper


class TestAppVars(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        # Wipe all apps before the tests run.
        cls.helper.wipe_application()
        cls.app = cls.balena.models.application.create("FooBar", "raspberry-pi2", cls.helper.default_organization["id"])
        cls.__app_fetch_resources = ["id", "slug", "uuid"]
        cls.app_vars = [
            cls.balena.models.application.env_var,
            cls.balena.models.application.build_var,
            cls.balena.models.application.config_var,
        ]

        cls.app_var_prefix = [
            "EDITOR_BY_",
            "EDITOR_BY_",
            "BALENA_"
        ]

    @classmethod
    def tearDownClass(cls):
        cls.helper.wipe_organization()

    def test_01_get_emtpy_application_vars(self):
        for app_var in self.app_vars:
            self.assertIsNone(app_var.get(self.app["id"], "DOES_NOT_EXIST"))

            with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
                self.assertIsNone(app_var.get("org-does-not/exist", "DOES_NOT_EXIST"))

    def test_02_can_create_and_retrieve_application_vars(self):
        for app_var, var_prefix in zip(self.app_vars, self.app_var_prefix):
            for resource in self.__app_fetch_resources:
                app_var.set(self.app[resource], f"{var_prefix}{resource}", f"VIM{resource}")
                self.assertEqual(
                    app_var.get(self.app[resource], f"{var_prefix}{resource}"),
                    f"VIM{resource}",
                )

    def test_03_can_get_all_app_vars(self):
        for app_var, var_prefix in zip(self.app_vars, self.app_var_prefix):
            for resource in self.__app_fetch_resources:
                app_vars = app_var.get_all_by_application(self.app[resource])
                expected_vars = [
                    {"name": f"{var_prefix}{resource}", "value": f"VIM{resource}"}
                    for resource in self.__app_fetch_resources
                ]
                app_vars_wo_id = [{"name": entry["name"], "value": entry["value"]} for entry in app_vars]

                for var in expected_vars:
                    self.assertIn(var, app_vars_wo_id)

    def test_04_can_update_app_vars(self):
        for app_var, var_prefix in zip(self.app_vars, self.app_var_prefix):
            for resource in self.__app_fetch_resources:
                app_var.set(
                    self.app[resource],
                    f"{var_prefix}{resource}",
                    f"VIM{resource}_edit",
                )
                self.assertEqual(
                    app_var.get(self.app[resource], f"{var_prefix}{resource}"),
                    f"VIM{resource}_edit",
                )

    def test_05_can_remove_application_env_vars(self):
        for app_var, var_prefix in zip(self.app_vars, self.app_var_prefix):
            for resource in self.__app_fetch_resources:
                app_var.remove(self.app[resource], f"{var_prefix}{resource}")
                self.assertIsNone(
                    app_var.get(self.app[resource], f"{var_prefix}{resource}"),
                )


class TestDeviceEnvironmentVariables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        # Wipe all apps before the tests run.
        cls.helper.wipe_application()
        cls.app = cls.balena.models.application.create("FooBar", "raspberry-pi2", cls.helper.default_organization["id"])
        cls.device = cls.balena.models.device.register(cls.app["id"], cls.balena.models.device.generate_uuid())
        cls.__device_fetch_resources = ["id", "uuid"]
        cls.device_env_var = cls.balena.models.device.env_var

    @classmethod
    def tearDownClass(cls):
        cls.helper.wipe_organization()

    def test_01_get_emtpy_device_env_var(self):
        self.assertIsNone(self.device_env_var.get(self.device["id"], "DOES_NOT_EXIST"))

        with self.assertRaises(self.helper.balena_exceptions.DeviceNotFound):
            self.assertIsNone(self.device_env_var.get("64705dcef0ec11eda05b0242ac120003", "DOES_NOT_EXIST"))

    def test_02_can_create_and_retrieve_device_env_var(self):
        for resource in self.__device_fetch_resources:
            self.device_env_var.set(self.device[resource], f"EDITOR_BY_{resource}", f"VIM{resource}")
            self.assertEqual(
                self.device_env_var.get(self.device[resource], f"EDITOR_BY_{resource}"),
                f"VIM{resource}",
            )

    def test_03_can_get_all_device_vars_by_application(self):
        for resource in self.__device_fetch_resources:
            device_vars = self.device_env_var.get_all_by_application(self.app[resource])
            expected_vars = [
                {"name": f"EDITOR_BY_{resource}", "value": f"VIM{resource}"}
                for resource in self.__device_fetch_resources
            ]
            device_vars_wo_id = [{"name": entry["name"], "value": entry["value"]} for entry in device_vars]

            for var in expected_vars:
                self.assertIn(var, device_vars_wo_id)

    def test_04_can_get_all_device_vars_by_device(self):
        for resource in self.__device_fetch_resources:
            device_vars = self.device_env_var.get_all_by_device(self.device[resource])
            expected_vars = [
                {"name": f"EDITOR_BY_{resource}", "value": f"VIM{resource}"}
                for resource in self.__device_fetch_resources
            ]
            device_vars_wo_id = [{"name": entry["name"], "value": entry["value"]} for entry in device_vars]

            for var in expected_vars:
                self.assertIn(var, device_vars_wo_id)

    def test_05_can_update_device_vars(self):
        for resource in self.__device_fetch_resources:
            self.device_env_var.set(
                self.device[resource],
                f"EDITOR_BY_{resource}",
                f"VIM{resource}_edit",
            )
            self.assertEqual(
                self.device_env_var.get(self.device[resource], f"EDITOR_BY_{resource}"),
                f"VIM{resource}_edit",
            )

    def test_06_can_remove_device_env_vars(self):
        for resource in self.__device_fetch_resources:
            self.device_env_var.remove(self.device[resource], f"EDITOR_BY_{resource}")
            self.assertIsNone(
                self.device_env_var.get(self.device[resource], f"EDITOR_BY_{resource}"),
            )


class TestDeviceServiceEnvironmentVariables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        # Wipe all apps before the tests run.
        cls.helper.wipe_application()
        mc_app = cls.helper.create_multicontainer_app()
        cls.device = mc_app["device"]
        cls.app = mc_app["app"]
        cls.service = mc_app["web_service"]
        cls.__device_fetch_resources = ["id", "uuid"]
        cls.device_service_env_var = cls.balena.models.device.service_var

    @classmethod
    def tearDownClass(cls):
        cls.helper.wipe_organization()

    def test_01_get_emtpy_device_service_env_var(self):
        self.assertIsNone(self.device_service_env_var.get(self.device["id"], self.service["id"], "DOES_NOT_EXIST"))

        with self.assertRaises(self.helper.balena_exceptions.ServiceNotFound):
            self.device_service_env_var.set(self.device["id"], 123, "bla", "vai existir")

    def test_02_can_create_and_retrieve_device_service_env_var(self):
        for resource in self.__device_fetch_resources:
            self.device_service_env_var.set(
                self.device[resource],
                self.service["id"],
                f"EDITOR_BY_{resource}",
                f"VIM{resource}",
            )
            self.assertEqual(
                self.device_service_env_var.get(
                    self.device[resource],
                    self.service["id"],
                    f"EDITOR_BY_{resource}",
                ),
                f"VIM{resource}",
            )

    def test_03_can_get_all_device_service_vars(self):
        for resource in self.__device_fetch_resources:
            device_vars = self.device_service_env_var.get_all_by_application(self.app[resource])
            expected_vars = [
                {"name": f"EDITOR_BY_{resource}", "value": f"VIM{resource}"}
                for resource in self.__device_fetch_resources
            ]
            device_vars_wo_id = [{"name": entry["name"], "value": entry["value"]} for entry in device_vars]

            for var in expected_vars:
                self.assertIn(var, device_vars_wo_id)

    def test_04_can_get_all_device_vars_by_device(self):
        for resource in self.__device_fetch_resources:
            device_vars = self.device_service_env_var.get_all_by_device(self.device[resource])
            expected_vars = [
                {"name": f"EDITOR_BY_{resource}", "value": f"VIM{resource}"}
                for resource in self.__device_fetch_resources
            ]
            device_vars_wo_id = [{"name": entry["name"], "value": entry["value"]} for entry in device_vars]

            for var in expected_vars:
                self.assertIn(var, device_vars_wo_id)

    def test_05_can_update_device_service_vars(self):
        for resource in self.__device_fetch_resources:
            self.device_service_env_var.set(
                self.device[resource],
                self.service["id"],
                f"EDITOR_BY_{resource}",
                f"VIM{resource}_edit",
            )
            self.assertEqual(
                self.device_service_env_var.get(
                    self.device[resource],
                    self.service["id"],
                    f"EDITOR_BY_{resource}",
                ),
                f"VIM{resource}_edit",
            )

    def test_06_can_remove_device_service_env_vars(self):
        for resource in self.__device_fetch_resources:
            self.device_service_env_var.remove(
                self.device[resource],
                self.service["id"],
                f"EDITOR_BY_{resource}",
            )
            self.assertIsNone(
                self.device_service_env_var.get(
                    self.device[resource],
                    self.service["id"],
                    f"EDITOR_BY_{resource}",
                ),
            )
