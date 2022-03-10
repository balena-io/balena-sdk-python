try:  # Python 3 imports
    from urllib.parse import parse_qs
except ImportError:  # Python 2 imports
    from urlparse.parse import parse_qs

import pyotp
import jwt

from .base_request import BaseRequest
from .settings import Settings
from . import exceptions

TOKEN_KEY = 'token'


class TwoFactorAuth:
    """
    This class implements basic 2FA functionalities for balena python SDK.

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
            >>> balena.twofactor_auth.is_enabled()
            False

        """

        try:
            token = self.settings.get(TOKEN_KEY)
            token_data = jwt.decode(token, algorithms=["HS256"], options={"verify_signature": False})
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
            >>> balena.twofactor_auth.is_passed()
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
            >>> balena.twofactor_auth.is_passed()
            False
            >>> secret = balena.twofactor_auth.get_setup_key()
            >>> balena.twofactor_auth.challenge(balena.twofactor_auth.generate_code(secret))
            # Check again if two-factor authentication is passed for current session.
            >>> balena.twofactor_auth.is_passed()
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
            >>> secret = balena.twofactor_auth.get_setup_key()
            >>> balena.twofactor_auth.generate_code(secret)
            '259975'

        """

        totp = pyotp.TOTP(secret)
        return totp.now()

    def get_setup_key(self):
        """
        Retrieves a setup key for enabling two factor authentication.
        This function only works if you disable two-factor authentication or log in using Auth Token from dashboard.

        Returns:
            str: setup key.

        Examples:
            >>> balena.twofactor_auth.get_setup_key()
            'WGURB3DIUWXTGQDBGFNGKDLV2L3LXOVN'

        """

        otp_auth_url = self.base_request.request(
            'auth/totp/setup', 'GET',
            endpoint=self.settings.get('api_endpoint'), login=True
        )
        tmp = parse_qs(otp_auth_url)
        return tmp['secret'.encode()][0]

    def verify(self, code):
        """
        Verifies two factor authentication.
        Note that this method not update the token automatically. You should use balena.twofactor_auth.challenge() when possible, as it takes care of that as well.

        Args:
            code (str): two-factor authentication code.

        Returns:
            str: session token.

        Examples:
            >>> balena.twofactor_auth.verify('123456')
            ''

        """

        data = {
            'code': code
        }

        return self.base_request.request(
            'auth/totp/verify', 'POST', data=data,
            endpoint=self.settings.get('api_endpoint'), login=True
        )

    def enable(self, code):
        """
        Enable two factor authentication.

        Args:
            code (str): two-factor authentication code.

        Returns:
            str: session token.

        Examples:
            >>> balena.twofactor_auth.enable('')
            ''

        """

        token = self.verify(code)
        self.settings.set(TOKEN_KEY, token)
        return token

    def disable(self, password):
        """
        Disable two factor authentication.

        Args:
            password (str): password.

        Returns:
            str: session token.

        Examples:
            >>> balena.twofactor_auth.verify('')
            ''

        """

        data = {
            'password': password
        }

        token = self.base_request.request(
            'auth/totp/disable', 'POST', data=data,
            endpoint=self.settings.get('api_endpoint'), login=True
        )

        self.settings.set(TOKEN_KEY, token)
        return token
