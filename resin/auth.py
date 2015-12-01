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
        This function is used for logging into Resin.io using email and password.

        Args:
            **credentials: credentials keyword arguments.
                username (str): Resin.io email.
                password (str): Password.

        Returns:
            This functions saves Auth Token to Settings and returns nothing.

        Raises:
            LoginFailed: if the email or password is invalid.

        Examples:
            >>> from resin import Resin
            >>> resin = Resin()
            >>> credentials = {'username': '<your email>', 'password': '<your password>''}
            >>> resin.auth.login(**credentials)
            (Empty Return)

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

        Examples:
            >>> from resin import Resin
            >>> resin = Resin()
            >>> auth_token = <your token>
            >>> resin.auth.login_with_token(auth_token)
            (Empty Return)

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

        Examples:
            >>> resin.auth.who_am_i()
            u'g_trong_nghia_nguyen'

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

        Examples:
            >>> resin.auth.authenticate(username='<your email>', password='<your password>')
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6NTM5NywidXNlcm5hbWUiOiJnX3Ryb25nX25naGlhX25ndXllbiIsImVtYWlsIjoicmVzaW5weXRob25zZGt0ZXN0QGdtYWlsLmNvbSIsInNvY2lhbF9zZXJ2aWNlX2FjY291bnQiOlt7ImNyZWF0ZWRfYXQiOiIyMDE1LTExLTIzVDAzOjMwOjE0LjU3MloiLCJpZCI6MTE2NiwidXNlciI6eyJfX2RlZmVycmVkIjp7InVyaSI6Ii9ld2EvdXNlcig1Mzk3KSJ9LCJfX2lkIjo1Mzk3fSwicHJvdmlkZXIiOiJnb29nbGUiLCJyZW1vdGVfaWQiOiIxMDE4OTMzNzc5ODQ3NDg1NDMwMDIiLCJkaXNwbGF5X25hbWUiOiJUcm9uZyBOZ2hpYSBOZ3V5ZW4iLCJfX21ldGFkYXRhIjp7InVyaSI6Ii9ld2Evc29jaWFsX3NlcnZpY2VfYWNjb3VudCgxMTY2KSIsInR5cGUiOiIifX1dLCJoYXNfZGlzYWJsZWRfbmV3c2xldHRlciI6ZmFsc2UsImp3dF9zZWNyZXQiOiI0UDVTQzZGV1pIVU5JR0NDT1dJQUtST0tST0RMUTRNVSIsImhhc1Bhc3N3b3JkU2V0Ijp0cnVlLCJuZWVkc1Bhc3N3b3JkUmVzZXQiOmZhbHNlLCJwdWJsaWNfa2V5Ijp0cnVlLCJmZWF0dXJlcyI6W10sImludGVyY29tVXNlck5hbWUiOiJnX3Ryb25nX25naGlhX25ndXllbiIsImludGVyY29tVXNlckhhc2giOiI5YTM0NmUwZTgzNjk0MzYxODU3MTdjNWRhZTZkZWZhZDdiYmM4YzZkOGNlMzgxYjhhYTY5YWRjMTRhYWZiNGU0IiwicGVybWlzc2lvbnMiOltdLCJpYXQiOjE0NDgyNTYzMDYsImV4cCI6MTQ0ODg2MTEwNn0.U9lfEpPHBRvGQSayASE-glI-lQtAjyIFYd00uXOUzLI'

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

        Examples:
            # Check if user logged in.
            >>> if resin.auth.is_logged_in():
            ...     print('You are logged in!')
            ... else:
            ...     print('You are not logged in!')

        """

        try:
            self.base_request.request(
                '/whoami', 'GET', endpoint=self.settings.get('api_endpoint')
            )
            return True
        except exceptions.RequestError:
            return False

    def get_token(self):
        """
        This function retrieves Auth Token.

        Returns:
            str: Auth Token.

        Raises:
            InvalidOption: if not logged in and there is no token in Settings.

        Examples:
            # If you are logged in.
            >>> resin.auth.get_token()
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6NTM5NywidXNlcm5hbWUiOiJnX3Ryb25nX25naGlhX25ndXllbiIsImVtYWlsIjoicmVzaW5weXRob25zZGt0ZXN0QGdtYWlsLmNvbSIsInNvY2lhbF9zZXJ2aWNlX2FjY291bnQiOlt7ImNyZWF0ZWRfYXQiOiIyMDE1LTExLTIzVDAzOjMwOjE0LjU3MloiLCJpZCI6MTE2NiwidXNlciI6eyJfX2RlZmVycmVkIjp7InVyaSI6Ii9ld2EvdXNlcig1Mzk3KSJ9LCJfX2lkIjo1Mzk3fSwicHJvdmlkZXIiOiJnb29nbGUiLCJyZW1vdGVfaWQiOiIxMDE4OTMzNzc5ODQ3NDg1NDMwMDIiLCJkaXNwbGF5X25hbWUiOiJUcm9uZyBOZ2hpYSBOZ3V5ZW4iLCJfX21ldGFkYXRhIjp7InVyaSI6Ii9ld2Evc29jaWFsX3NlcnZpY2VfYWNjb3VudCgxMTY2KSIsInR5cGUiOiIifX1dLCJoYXNfZGlzYWJsZWRfbmV3c2xldHRlciI6ZmFsc2UsImp3dF9zZWNyZXQiOiI0UDVTQzZGV1pIVU5JR0NDT1dJQUtST0tST0RMUTRNVSIsImhhc1Bhc3N3b3JkU2V0Ijp0cnVlLCJuZWVkc1Bhc3N3b3JkUmVzZXQiOmZhbHNlLCJwdWJsaWNfa2V5Ijp0cnVlLCJmZWF0dXJlcyI6W10sImludGVyY29tVXNlck5hbWUiOiJnX3Ryb25nX25naGlhX25ndXllbiIsImludGVyY29tVXNlckhhc2giOiI5YTM0NmUwZTgzNjk0MzYxODU3MTdjNWRhZTZkZWZhZDdiYmM4YzZkOGNlMzgxYjhhYTY5YWRjMTRhYWZiNGU0IiwicGVybWlzc2lvbnMiOltdLCJpYXQiOjE0NDgyNTY2ODMsImV4cCI6MTQ0ODg2MTQ4M30.oqq4DUI4cTbhzYznSwODZ_4zLOeGiJYuZRn82gTfQ6o'


        """

        return self.token.get()

    def get_user_id(self):
        """
        This function retrieves current logged in user's id.

        Returns:
            str: user id.

        Raises:
            InvalidOption: if not logged in.

        Examples:
            # If you are logged in.
            >>> resin.auth.get_user_id()
            5397

        """

        return self.token.get_user_id()

    def get_email(self):
        """
        This function retrieves current logged in user's get_email

        Returns:
            str: user email.

        Raises:
            InvalidOption: if not logged in.

        Examples:
            # If you are logged in.
            >>> resin.auth.get_email()
            u'resinpythonsdktest@gmail.com'

        """

        return self.token.get_email()

    def log_out(self):
        """
        This function is used for logging out from Resin.io.

        Returns:
            bool: True if successful, False otherwise.

        Examples:
            # If you are logged in.
            >>> resin.auth.log_out()
            True

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

        Examples:
            >>> credentials = {'email': '<your email>', 'password': '<your password>'}
            >>> resin.auth.register(**credentials)
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6NTM5OCwidXNlcm5hbWUiOiJ0ZXN0MjcxMCIsImVtYWlsIjoidGVzdDI3MTBAZ21haWwuY29tIiwic29jaWFsX3NlcnZpY2VfYWNjb3VudCI6bnVsbCwiaGFzX2Rpc2FibGVkX25ld3NsZXR0ZXIiOmZhbHNlLCJqd3Rfc2VjcmV0IjoiQlJXR0ZIVUgzNVBKT0VKTVRSSVo2MjdINjVKVkJKWDYiLCJoYXNQYXNzd29yZFNldCI6dHJ1ZSwibmVlZHNQYXNzd29yZFJlc2V0IjpmYWxzZSwicHVibGljX2tleSI6ZmFsc2UsImZlYXR1cmVzIjpbXSwiaW50ZXJjb21Vc2VyTmFtZSI6InRlc3QyNzEwIiwiaW50ZXJjb21Vc2VySGFzaCI6IjNiYTRhZDRkZjk4MDQ1OTc1YmU2ZGUwYWJmNjFiYjRmYWY4ZmEzYTljZWI0YzE4Y2QxOGU1NmViNmI1NzkxZDAiLCJwZXJtaXNzaW9ucyI6W10sImlhdCI6MTQ0ODI1NzgyOCwiZXhwIjoxNDQ4ODYyNjI4fQ.chhf6deZ9BNDMmPr1Hm-SlRoWkK7t_4cktAPo12aCoE'

        """

        return self.base_request.request(
            'user/register', 'POST', data=credentials,
            endpoint=self.settings.get('api_endpoint'), auth=False
        )
