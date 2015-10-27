from .base_request import BaseRequest
from .token import Token
from .settings import Settings
from . import exceptions


class TwoFactor_Auth(object):
    """
    This class implements basic 2FA functionalities for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.token = Token()

    def is_enabled(self):
        """
        Check if two factor authentication is enabled.

        Returns:
            bool: True if enabled. Otherwise False.

        """

        try:
            self.token.get_property('twoFactorRequired')
            return True
        except exceptions.InvalidOption:
            return False

    def is_passed(self):
        """
        Check if two factor authentication challenge was passed.

        Returns:
            bool: True if enabled. Otherwise False.

        """

        if not self.is_enabled():
            return True
        return not self.token.get_property('twoFactorRequired')

    def challenge(self, token):
        """
        Challenge two factor authentication.

        Args:
            token (str): two factor authentication token.

        """

        data = {
            'code': token
        }
        token = self.base_request.request(
            'auth/totp/verify', 'POST', data=data,
            endpoint=self.settings.get('api_endpoint'), login=True
        )
        self.token.set(token)
