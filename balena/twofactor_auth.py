from urllib.parse import parse_qs
import jwt

from . import exceptions
from .balena_auth import request
from .settings import Settings

TOKEN_KEY = "token"


class TwoFactorAuth:
    """
    This class implements basic 2FA functionalities for balena python SDK.

    """

    def __init__(self, settings: Settings):
        self.__settings = settings

    def is_enabled(self) -> bool:
        """
        Check if two-factor authentication is enabled.

        Returns:
            bool: True if enabled. Otherwise False.

        Examples:
            >>> balena.twofactor_auth.is_enabled()
        """
        try:
            token = self.__settings.get(TOKEN_KEY)
            token_data = jwt.decode(token, algorithms=["HS256"], options={"verify_signature": False})
            return "twoFactorRequired" in token_data
        except jwt.InvalidTokenError:
            raise exceptions.UnsupportedFeature()

    def is_passed(self) -> bool:
        """
        Check if two-factor authentication challenge was passed.
        If the user does not have 2FA enabled, this will be True.

        Returns:
            bool: True if passed. Otherwise False.

        Examples:
            >>> balena.twofactor_auth.is_passed()
        """
        try:
            token = self.__settings.get(TOKEN_KEY)
            token_data = jwt.decode(token, algorithms=["HS256"], options={"verify_signature": False})
            if "twoFactorRequired" in token_data:
                return not token_data["twoFactorRequired"]
            return True
        except jwt.InvalidTokenError:
            raise exceptions.UnsupportedFeature()

    def verify(self, code: str) -> str:
        """
        Verifies two factor authentication.
        Note that this method not update the token automatically.
        You should use balena.twofactor_auth.challenge() when possible, as it takes care of that as well.

        Args:
            code (str): two-factor authentication code.

        Returns:
            str: session token.

        Examples:
            >>> balena.twofactor_auth.verify('123456')
        """
        return request(
            method="POST",
            settings=self.__settings,
            path="auth/totp/verify",
            body={"code": code},
        )

    def get_setup_key(self) -> str:
        """
        Retrieves a setup key for enabling two factor authentication.
        This value should be provided to your 2FA app in order to get a token.
        This function only works if you disable two-factor authentication or log in using Auth Token from dashboard.

        Returns:
            str: setup key.

        Examples:
            >>> balena.twofactor_auth.get_setup_key()
        """
        otp_auth_url = request(
            method="GET",
            settings=self.__settings,
            path="auth/totp/setup",
        )
        return parse_qs(otp_auth_url)["secret"][0]

    def enable(self, code: str) -> str:
        """
        Enable two factor authentication.

        Args:
            code (str): two-factor authentication code.

        Returns:
            str: session token.

        Examples:
            >>> balena.twofactor_auth.enable('123456')
        """
        token = self.verify(code)
        self.__settings.set(TOKEN_KEY, token)
        return token

    def challenge(self, code: str) -> None:
        """
        Challenge two-factor authentication.
        If your account has two-factor authentication enabled and logging in using credentials,
        you need to pass two-factor authentication before being allowed to use other functions.

        Args:
            code (str): two-factor authentication code.

        Examples:
            # You need to enable two-factor authentication on dashboard first.
            # Check if two-factor authentication is passed for current session.
            >>> balena.twofactor_auth.is_passed()
            False
            >>> balena.twofactor_auth.challenge('123456')
            # Check again if two-factor authentication is passed for current session.
            >>> balena.twofactor_auth.is_passed()
            True
        """
        token = self.verify(code)
        self.__settings.set(TOKEN_KEY, token)

    def disable(self, password: str) -> str:
        """
        Disable two factor authentication.
        __Note__: Disable will only work when using a token that has 2FA enabled.

        Args:
            password (str): password.

        Returns:
            str: session token.

        Examples:
            >>> balena.twofactor_auth.disable('your_password')
        """
        token = request(
            method="POST",
            settings=self.__settings,
            path="auth/totp/disable",
            body={"password": password},
        )

        self.__settings.set(TOKEN_KEY, token)
        return token
