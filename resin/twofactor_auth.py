try:  # Python 3 imports
    from urllib.parse import urlparse
except ImportError:  # Python 2 imports
    from urlparse import urlparse

import pyotp
import jwt

from .base_request import BaseRequest
from .settings import Settings
from . import exceptions

TOKEN_KEY = 'token'


class TwoFactorAuth(object):
    """
    This class implements basic 2FA functionalities for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

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
            token = self.settings.get(TOKEN_KEY)
            token_data = jwt.decode(token, verify=False)
            if 'twoFactorRequired' in token_data:
                return True
            return False
        except jwt.InvalidTokenError:
            # in case it's not Auth token
            raise exceptions.UnsupportedFeature()

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
        return False

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
        self.settings.set(TOKEN_KEY, token)

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
