import urlparse

import pyotp

from .base_request import BaseRequest
from .token import Token
from .settings import Settings
from . import exceptions


class TwoFactorAuth(object):
    """
    This class implements basic 2FA functionalities for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.token = Token()

    def is_enabled(self):
        """
        Check if two-factor authentication is enabled.

        Returns:
            bool: True if enabled. Otherwise False.

        Examples:
            >>> resin.twofactor_auth.is_enabled()
            False

        """

        try:
            self.token.get_property('twoFactorRequired')
            return True
        except exceptions.InvalidOption:
            return False

    def is_passed(self):
        """
        Check if two-factor authentication challenge was passed.

        Returns:
            bool: True if enabled. Otherwise False.

        Examples:
            >>> resin.twofactor_auth.is_passed()
            True

        """

        if not self.is_enabled():
            return True
        return not self.token.get_property('twoFactorRequired')

    def challenge(self, code):
        """
        Challenge two-factor authentication.
        If your account has two-factor authentication enabled and logging in using credentials, you need to pass two-factor authentication before being allowed to use other functions.

        Args:
            code (str): two-factor authentication code.

        Examples:
            # You need to enable two-factor authentication on dashboard first.
            # Check if two-factor authentication is passed for current session.
            >>> resin.twofactor_auth.is_passed()
            False
            >>> secret = resin.twofactor_auth.get_otpauth_secret()
            >>> resin.twofactor_auth.challenge(resin.twofactor_auth.generate_code(secret))
            # Check again if two-factor authentication is passed for current session.
            >>> resin.twofactor_auth.is_passed()
            True

        """

        data = {
            'code': code
        }
        token = self.base_request.request(
            'auth/totp/verify', 'POST', data=data,
            endpoint=self.settings.get('api_endpoint'), login=True
        )
        self.token.set(token)

    def generate_code(self, secret):
        """
        Generate two-factor authentication code.

        Args:
            secret (str): one time password authentication secret string.

        Returns:
            str: 6 digit two-factor authentication code.

        Examples:
            >>> secret = resin.twofactor_auth.get_otpauth_secret()
            >>> resin.twofactor_auth.generate_code(secret)
            '259975'

        """

        totp = pyotp.TOTP(secret)
        return totp.now()

    def get_otpauth_secret(self):
        """
        Retrieve one time password authentication secret string.
        This function only works if you disable two-factor authentication or log in using Auth Token from dashboard.

        Returns:
            str: one time password authentication secret string.

        Examples:
            >>> resin.twofactor_auth.get_otpauth_secret()
            'WGURB3DIUWXTGQDBGFNGKDLV2L3LXOVN'

        """

        otp_auth_url = self.base_request.request(
            'auth/totp/setup', 'GET',
            endpoint=self.settings.get('api_endpoint'), login=True
        )
        tmp = urlparse.parse_qs(otp_auth_url)
        return tmp['secret'][0]
