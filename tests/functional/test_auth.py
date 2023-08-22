import unittest

from balena import Balena
from balena.exceptions import NotLoggedIn, LoginFailed
from tests.helper import TestHelper
from typing import cast
from balena.auth import ApplicationKeyWhoAmIResponse, UserKeyWhoAmIResponse, DeviceKeyWhoAmIResponse


class TestAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = Balena()
        cls.app_info = cls.helper.create_multicontainer_app()

    @classmethod
    def tearDownClass(cls):
        cls.balena.auth.login(**TestAuth.creds)
        cls.helper.wipe_application()
        cls.helper.wipe_organization()

    def test_01_is_logged_in_false_when_not_logged_in(self):
        self.balena.auth.logout()
        self.assertFalse(self.balena.auth.is_logged_in())

    def test_02_logout_does_not_fail_when_not_logged_in(self):
        self.balena.auth.logout()

    def test_03_not_save_token_with_valid_credentials_on_authenticate(self):
        TestHelper.load_env()
        TestAuth.creds = {
            "username": TestHelper.credentials["user_id"],
            "password": TestHelper.credentials["password"],
        }

        token = self.balena.auth.authenticate(**TestAuth.creds)
        self.assertGreater(len(token), 1)

        # does not save token given valid credentials
        self.assertFalse(self.balena.auth.is_logged_in())

    def test_04_rejects_with_invalid_credentials(self):
        with self.assertRaises(LoginFailed):
            self.balena.auth.authenticate(**{"username": TestAuth.creds["username"], "password": "NOT-CORRECT"})

    def test_05_should_reject_to_get_token_when_not_logged_in(self):
        self.assertIsNone(self.balena.auth.get_token())

    def test_06_should_be_able_to_login_with_session_token(self):
        token = self.balena.auth.authenticate(**TestAuth.creds)
        self.balena.auth.login_with_token(token)
        self.assertEqual(self.balena.auth.get_token(), token)

    def test_07_should_be_able_to_login_with_api_key(self):
        key = self.balena.models.api_key.create("apiKey")
        self.balena.auth.logout()
        self.balena.auth.login_with_token(key)
        self.assertEqual(self.balena.auth.get_token(), key)
        TestAuth.test_api_key = key

    def test_08_getters_should_throw_when_not_logged_in(self):
        self.balena.auth.logout()

        with self.assertRaises(NotLoggedIn):
            self.balena.auth.whoami()

        with self.assertRaises(NotLoggedIn):
            self.balena.auth.get_actor_id()

        with self.assertRaises(NotLoggedIn):
            self.balena.auth.get_user_info()

    def test_09_should_not_throw_login_with_malformed_token(self):
        token = self.balena.auth.authenticate(**TestAuth.creds)
        self.balena.auth.login_with_token(f"{token}malformingsuffix")
        self.assertEqual(self.balena.auth.get_token(), f"{token}malformingsuffix")

    def test_10_is_logged_in_should_be_false_with_malformed_token(self):
        self.assertFalse(self.balena.auth.is_logged_in())

    def test_11_getters_should_throw_with_malformed_token(self):
        with self.assertRaises(NotLoggedIn):
            self.balena.auth.whoami()

        with self.assertRaises(NotLoggedIn):
            self.balena.auth.get_actor_id()

        with self.assertRaises(NotLoggedIn):
            self.balena.auth.get_user_info()

    def test_12_should_get_logged_in_after_logged_in(self):
        TestAuth.creds = {
            "username": TestHelper.credentials["user_id"],
            "password": TestHelper.credentials["password"],
        }
        self.balena.auth.login(**TestAuth.creds)
        self.assertTrue(self.balena.auth.is_logged_in())

    def test_13_getters_should_return_info_when_logged_in(self):
        whoami = cast(UserKeyWhoAmIResponse, self.balena.auth.whoami())

        self.assertEqual(whoami["actorType"], "user")
        self.assertEqual(whoami["username"], TestAuth.creds["username"])
        self.assertEqual(whoami["email"], TestHelper.credentials["email"])
        self.assertIsInstance(whoami["id"], int)
        self.assertIsInstance(whoami["actorTypeId"], int)

        actor_id = self.balena.auth.get_actor_id()
        self.assertIsInstance(actor_id, int)
        self.assertGreater(actor_id, 0)

        user_info = self.balena.auth.get_user_info()
        self.assertEqual(user_info["username"], TestAuth.creds["username"])
        self.assertEqual(user_info["email"], TestHelper.credentials["email"])
        self.assertEqual(user_info["actor"], actor_id)
        self.assertIsInstance(user_info["id"], int)
        self.assertGreater(user_info["id"], 0)

    def test_14_should_not_return_logged_in_when_logged_out(self):
        self.balena.auth.logout()
        self.assertFalse(self.balena.auth.is_logged_in())

    def test_15_getters_should_return_info_when_logged_in_with_api_key(self):
        self.balena.auth.login_with_token(TestAuth.test_api_key)
        self.assertTrue(self.balena.auth.is_logged_in())

        user_id = self.balena.auth.get_user_info()["id"]
        self.assertIsInstance(user_id, int)
        self.assertGreater(user_id, 0)

        actor_id = self.balena.auth.get_actor_id()
        self.assertIsInstance(actor_id, int)
        self.assertGreater(actor_id, 0)

        self.balena.auth.logout()
        self.assertFalse(self.balena.auth.is_logged_in())

        self.assertIsNone(self.balena.auth.get_token())

    def test_16_2fa(self):
        self.balena.auth.login(**TestAuth.creds)

        self.assertFalse(self.balena.auth.two_factor.is_enabled())
        self.assertTrue(self.balena.auth.two_factor.is_passed())

        secret = self.balena.auth.two_factor.get_setup_key()
        self.assertEqual(len(secret), 32)

    def test_17_should_login_with_device_key(self):
        device_uuid = self.app_info["device"]["uuid"]

        device_key = self.balena.models.device.generate_device_key(device_uuid)
        self.balena.auth.login_with_token(device_key)

        self.assertTrue(self.balena.auth.is_logged_in())
        whoami = cast(DeviceKeyWhoAmIResponse, self.balena.auth.whoami())

        self.assertEqual(whoami["actorType"], "device")
        self.assertEqual(whoami["actorTypeId"], self.app_info["device"]["id"])
        self.assertEqual(whoami["uuid"], device_uuid)
        self.assertEqual(whoami["id"], self.app_info["device"]["actor"])

        self.assertEqual(self.balena.auth.get_actor_id(), self.app_info["device"]["actor"])

        errMsg = "The authentication credentials in use are not of a user"
        with self.assertRaises(Exception) as cm:
            self.balena.auth.get_user_info()
        self.assertIn(errMsg, str(cm.exception))

        self.balena.auth.logout()
        self.assertFalse(self.balena.auth.is_logged_in())

        self.assertIsNone(self.balena.auth.get_token())

    def test_18_should_login_with_app_key(self):
        TestAuth.creds = {
            "username": TestHelper.credentials["user_id"],
            "password": TestHelper.credentials["password"],
        }
        self.balena.auth.login(**TestAuth.creds)
        self.assertTrue(self.balena.auth.is_logged_in())
        app_id = self.app_info["app"]["id"]

        app_key = self.balena.models.application.generate_provisioning_key(app_id)
        self.balena.auth.login_with_token(app_key)

        self.assertTrue(self.balena.auth.is_logged_in())
        whoami = cast(ApplicationKeyWhoAmIResponse, self.balena.auth.whoami())

        self.assertEqual(whoami["actorType"], "application")
        self.assertEqual(whoami["actorTypeId"], app_id)
        self.assertEqual(whoami["id"], self.app_info["app"]["actor"])
        self.assertEqual(whoami["slug"], self.app_info["app"]["slug"])

        self.assertEqual(self.balena.auth.get_actor_id(), self.app_info["app"]["actor"])

        errMsg = "The authentication credentials in use are not of a user"
        with self.assertRaises(Exception) as cm:
            self.balena.auth.get_user_info()
        self.assertIn(errMsg, str(cm.exception))

        self.balena.auth.logout()
        self.assertFalse(self.balena.auth.is_logged_in())

        self.assertIsNone(self.balena.auth.get_token())
