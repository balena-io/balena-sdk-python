import unittest

from balena import Balena
from balena.exceptions import NotLoggedIn, LoginFailed
from tests.helper import TestHelper


class TestAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.balena = Balena()

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
            self.balena.auth.get_email()

        with self.assertRaises(NotLoggedIn):
            self.balena.auth.get_user_id()

        with self.assertRaises(NotLoggedIn):
            self.balena.auth.get_user_actor_id()

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
            self.balena.auth.get_email()

        with self.assertRaises(NotLoggedIn):
            self.balena.auth.get_user_id()

        with self.assertRaises(NotLoggedIn):
            self.balena.auth.get_user_actor_id()

    def test_12_should_get_logged_in_after_logged_in(self):
        TestAuth.creds = {
            "username": TestHelper.credentials["user_id"],
            "password": TestHelper.credentials["password"],
        }
        self.balena.auth.login(**TestAuth.creds)
        self.assertTrue(self.balena.auth.is_logged_in())

    def test_13_getters_should_return_info_when_logged_in(self):
        self.assertEqual(self.balena.auth.whoami(), TestHelper.credentials["user_id"])
        self.assertEqual(self.balena.auth.get_email(), TestHelper.credentials["email"])

        user_id = self.balena.auth.get_user_id()
        self.assertIsInstance(user_id, int)
        self.assertGreater(user_id, 0)

        user_actor_id = self.balena.auth.get_user_actor_id()
        self.assertIsInstance(user_actor_id, int)
        self.assertGreater(user_actor_id, 0)

    def test_14_should_be_able_to_login(self):
        self.balena.auth.logout()
        self.assertFalse(self.balena.auth.is_logged_in())

    def test_15_getters_should_return_info_when_logged_in_with_api_key(self):
        self.balena.auth.login_with_token(TestAuth.test_api_key)
        self.assertTrue(self.balena.auth.is_logged_in())

        self.assertEqual(self.balena.auth.whoami(), TestHelper.credentials["user_id"])
        self.assertEqual(self.balena.auth.get_email(), TestHelper.credentials["email"])

        user_id = self.balena.auth.get_user_id()
        self.assertIsInstance(user_id, int)
        self.assertGreater(user_id, 0)

        user_actor_id = self.balena.auth.get_user_actor_id()
        self.assertIsInstance(user_actor_id, int)
        self.assertGreater(user_actor_id, 0)

        self.balena.auth.logout()
        self.assertFalse(self.balena.auth.is_logged_in())

        self.assertIsNone(self.balena.auth.get_token())
