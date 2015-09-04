import jwt
from datetime import datetime

from .settings import Settings
from . import exceptions

TOKEN_KEY = 'token'


class Token(object):
    """
    This class provides Auth Token utilities for Resin Python SDK.
    This is low level class and is not meant to be used by end users directly.
    """

    def __init__(self):
        self.settings = Settings()

    def __parse_token(self, token):
        try:
            return jwt.decode(token, verify=False)
        except jwt.InvalidTokenError:
            raise exceptions.MalformedToken(token)

    def is_valid_token(self, token):
        """
        Check if an auth token is valid.

        Args:
            token (str): auth token.

        Returns:
            bool: True if the token is valid, False otherwise.

        """

        try:
            self.__parse_token(token)
            return True
        except:
            return False

    def set(self, token):
        """
        Set auth token.

        Args:
            token (str): auth token.

        """

        if self.is_valid_token(token):
            self.settings.set(TOKEN_KEY, token)

    def get(self):
        """
        Get auth token.

        Returns:
            bool: True if the token is valid, False otherwise.

        Raises:
            InvalidOption: if auth token is not set.

        """

        return self.settings.get(TOKEN_KEY)

    def has(self):
        """
        Check if auth token is exist.

        Returns:
            bool: True if the auth token exists, False otherwise.

        """

        return self.settings.has(TOKEN_KEY)

    def remove(self):
        """
        Remove auth token.

        Returns:
            bool: True if successful, False otherwise.

        """

        return self.settings.remove(TOKEN_KEY)

    def get_data(self):
        """
        Read encoded information in the auth token.

        Returns:
            dict: auth token data.

        Raises:
            NotLoggedIn: if there is no user logged in.

        """

        if self.has():
            return self.__parse_token(self.settings.get(TOKEN_KEY))
        else:
            raise exceptions.NotLoggedIn()

    def get_property(self, element):
        """
        Get a property from auth token data.

        Args:
            element (str): property name.

        Returns:
            str: property value.

        Raises:
            InvalidOption: If getting a non-existent property.
            NotLoggedIn: if there is no user logged in.

        """

        token_data = self.get_data()
        if element in token_data:
            return token_data[element]
        else:
            raise exceptions.InvalidOption(element)

    def get_username(self):
        """
        Get username from auth token data.

        Returns:
            str: username.

        Raises:
            NotLoggedIn: if there is no user logged in.

        """

        return self.get_property('username')

    def get_user_id(self):
        """
        Get user id from auth token data.

        Returns:
            str: user id.

        Raises:
            NotLoggedIn: if there is no user logged in.

        """

        return self.get_property('id')

    def get_email(self):
        """
        Get email from auth token data.

        Returns:
            str: email.

        Raises:
            NotLoggedIn: if there is no user logged in.

        """

        return self.get_property('email')

    def get_age(self):
        """
        Get age of the auth token data.

        Returns:
            int: age in milliseconds.

        Raises:
            NotLoggedIn: if there is no user logged in.

        """

        # dt will be the same as Date.now() in Javascript but converted to
        # milliseconds for consistency with js/sc sdk
        dt = (datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds()
        dt = dt * 1000

        # iat stands for "issued at"
        return dt - (int(self.get_property('iat')) * 1000)
