from .base_request import BaseRequest
from .token import Token
from .settings import Settings
from . import exceptions


class Auth(object):
    """
    This class implements all authentication functions for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.token = Token()

    def login(self, **credentials):
        """
        This function is used for logging into Resin.io using username and password.

        Args:
            **credentials: credentials keyword arguments.
                username (str): Resin.io username.
                password (str): Password.

        Returns:
            This functions saves Auth Token to Settings and returns nothing.

        Raises:
            LoginFailed: if the username or password is invalid.

        """

        token = self.authenticate(**credentials)
        if self.token.is_valid_token(token):
            self.token.set(token)
        else:
            raise exceptions.LoginFailed()

    def login_with_token(self, token):
        """
        This function is used for logging into Resin.io using Auth Token.
        Auth Token can be found in Preferences section on Resin.io Dashboard.

        Args:
            token (str): Auth Token.

        Returns:
            This functions saves Auth Token to Settings and returns nothing.

        Raises:
            MalformedToken: if token is invalid.

        """

        if self.token.is_valid_token(token):
            self.token.set(token)
        else:
            raise exceptions.MalformedToken(token)

    def who_am_i(self):
        """
        This function retrieves username of logged in user.

        Returns:
            str: username.

        Raises:
            NotLoggedIn: if there is no user logged in.

        """

        return self.token.get_username()

    def authenticate(self, **credentials):
        """
        This function authenticates provided credentials information.
        You should use Auth.login when possible, as it takes care of saving the Auth Token and username as well.

        Args:
            **credentials: credentials keyword arguments.
                username (str): Resin.io username.
                password (str): Password.

        Returns:
            str: Auth Token,

        Raises:
            LoginFailed: if the username or password is invalid.

        """

        return self.base_request.request(
            'login_', 'POST', data=credentials,
            endpoint=self.settings.get('api_endpoint'), auth=False
        )

    def is_logged_in(self):
        """
        This function checks if you're logged in

        Returns:
            bool: True if logged in, False otherwise.

        """

        return self.token.has()

    def get_token(self):
        """
        This function retrieves Auth Token.

        Returns:
            str: Auth Token.

        Raises:
            InvalidOption: if not logged in and there is no token in Settings.

        """

        return self.token.get()

    def get_user_id(self):
        """
        This function retrieves current logged in user's id.

        Returns:
            str: user id.

        Raises:
            InvalidOption: if not logged in.

        """

        return self.token.get_user_id()

    def get_email(self):
        """
        This function retrieves current logged in user's get_email

        Returns:
            str: user email.

        Raises:
            InvalidOption: if not logged in.

        """

        return self.token.get_email()

    def log_out(self):
        """
        This function is used for logging out from Resin.io.

        Returns:
            bool: True if successful, False otherwise.

        """

        return self.token.remove()

    def register(self, **credentials):
        """
        This function is used for registering to Resin.io.

        Args:
            **credentials: credentials keyword arguments.
                email (str): email to register.
                password (str): Password.

        Returns:
            str: Auth Token for new account.

        Raises:
            RequestError: if error occurs during registration.

        """

        return self.base_request.request(
            'user/register', 'POST', data=credentials,
            endpoint=self.settings.get('api_endpoint'), auth=False
        )
