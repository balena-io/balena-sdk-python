from .base_request import BaseRequest
from .settings import Settings
from . import exceptions

TOKEN_KEY = 'token'


class Auth:
    """
    This class implements all authentication functions for balena python SDK.

    """

    _user_detail_cache = {}

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def __get_user_data(self):
        """
        Get user details from token.

        Returns:
            dict: user details.

        Raises:
            NotLoggedIn: if there is no user logged in.

        """

        if not self._user_detail_cache:
            self._user_detail_cache = self.base_request.request(
                'user/v1/whoami', 'get',
                endpoint=self.settings.get('api_endpoint')
            )

        return self._user_detail_cache

    def __get_property(self, element):
        """
        Get a property from user details.

        Args:
            element (str): property name.

        Returns:
            str: property value.

        Raises:
            InvalidOption: If getting a non-existent property.
            NotLoggedIn: if there is no user logged in.

        """

        if element in self.__get_user_data():
            return self._user_detail_cache[element]
        else:
            raise exceptions.InvalidOption(element)

    def login(self, **credentials):
        """
        This function is used for logging into balena using email and password.

        Args:
            **credentials: credentials keyword arguments.
                username (str): Balena email.
                password (str): Password.

        Returns:
            This functions saves Auth Token to Settings and returns nothing.

        Raises:
            LoginFailed: if the email or password is invalid.

        Examples:
            >>> from balena import Balena
            >>> balena = Balena()
            >>> credentials = {'username': '<your email>', 'password': '<your password>'}
            >>> balena.auth.login(**credentials)
            (Empty Return)

        """

        token = self.authenticate(**credentials).decode("utf-8")
        self._user_detail_cache = {}
        self.settings.set(TOKEN_KEY, token)

    def login_with_token(self, token):
        """
        This function is used for logging into balena using Auth Token.
        Auth Token can be found in Preferences section on balena Dashboard.

        Args:
            token (str): Auth Token.

        Returns:
            This functions saves Auth Token to Settings and returns nothing.

        Raises:
            MalformedToken: if token is invalid.

        Examples:
            >>> from balena import Balena
            >>> balena = Balena()
            >>> auth_token = <your token>
            >>> balena.auth.login_with_token(auth_token)
            (Empty Return)

        """
        self._user_detail_cache = {}
        self.settings.set(TOKEN_KEY, token)

    def who_am_i(self):
        """
        This function retrieves username of logged in user.

        Returns:
            str: username.

        Raises:
            NotLoggedIn: if there is no user logged in.

        Examples:
            >>> balena.auth.who_am_i()
            u'g_trong_nghia_nguyen'

        """

        return self.__get_property('username')

    def authenticate(self, **credentials):
        """
        This function authenticates provided credentials information.
        You should use Auth.login when possible, as it takes care of saving the Auth Token and username as well.

        Args:
            **credentials: credentials keyword arguments.
                username (str): Balena username.
                password (str): Password.

        Returns:
            str: Auth Token,

        Raises:
            LoginFailed: if the username or password is invalid.

        Examples:
            >>> balena.auth.authenticate(username='<your email>', password='<your password>')
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
            >>> if balena.auth.is_logged_in():
            ...     print('You are logged in!')
            ... else:
            ...     print('You are not logged in!')

        """

        try:
            self.__get_user_data()
            return True
        except (exceptions.RequestError, exceptions.Unauthorized):
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
            >>> balena.auth.get_token()
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6NTM5NywidXNlcm5hbWUiOiJnX3Ryb25nX25naGlhX25ndXllbiIsImVtYWlsIjoicmVzaW5weXRob25zZGt0ZXN0QGdtYWlsLmNvbSIsInNvY2lhbF9zZXJ2aWNlX2FjY291bnQiOlt7ImNyZWF0ZWRfYXQiOiIyMDE1LTExLTIzVDAzOjMwOjE0LjU3MloiLCJpZCI6MTE2NiwidXNlciI6eyJfX2RlZmVycmVkIjp7InVyaSI6Ii9ld2EvdXNlcig1Mzk3KSJ9LCJfX2lkIjo1Mzk3fSwicHJvdmlkZXIiOiJnb29nbGUiLCJyZW1vdGVfaWQiOiIxMDE4OTMzNzc5ODQ3NDg1NDMwMDIiLCJkaXNwbGF5X25hbWUiOiJUcm9uZyBOZ2hpYSBOZ3V5ZW4iLCJfX21ldGFkYXRhIjp7InVyaSI6Ii9ld2Evc29jaWFsX3NlcnZpY2VfYWNjb3VudCgxMTY2KSIsInR5cGUiOiIifX1dLCJoYXNfZGlzYWJsZWRfbmV3c2xldHRlciI6ZmFsc2UsImp3dF9zZWNyZXQiOiI0UDVTQzZGV1pIVU5JR0NDT1dJQUtST0tST0RMUTRNVSIsImhhc1Bhc3N3b3JkU2V0Ijp0cnVlLCJuZWVkc1Bhc3N3b3JkUmVzZXQiOmZhbHNlLCJwdWJsaWNfa2V5Ijp0cnVlLCJmZWF0dXJlcyI6W10sImludGVyY29tVXNlck5hbWUiOiJnX3Ryb25nX25naGlhX25ndXllbiIsImludGVyY29tVXNlckhhc2giOiI5YTM0NmUwZTgzNjk0MzYxODU3MTdjNWRhZTZkZWZhZDdiYmM4YzZkOGNlMzgxYjhhYTY5YWRjMTRhYWZiNGU0IiwicGVybWlzc2lvbnMiOltdLCJpYXQiOjE0NDgyNTY2ODMsImV4cCI6MTQ0ODg2MTQ4M30.oqq4DUI4cTbhzYznSwODZ_4zLOeGiJYuZRn82gTfQ6o'


        """

        return self.settings.get(TOKEN_KEY)

    def get_user_id(self):
        """
        This function retrieves current logged in user's id.

        Returns:
            str: user id.

        Raises:
            InvalidOption: if not logged in.

        Examples:
            # If you are logged in.
            >>> balena.auth.get_user_id()
            5397

        """

        return self.__get_property('id')

    def get_email(self):
        """
        This function retrieves current logged in user's get_email

        Returns:
            str: user email.

        Raises:
            InvalidOption: if not logged in.

        Examples:
            # If you are logged in.
            >>> balena.auth.get_email()
            u'balenapythonsdktest@gmail.com'

        """

        return self.__get_property('email')

    def log_out(self):
        """
        This function is used for logging out from balena.

        Returns:
            bool: True if successful, False otherwise.

        Examples:
            # If you are logged in.
            >>> balena.auth.log_out()
            True

        """

        self._user_detail_cache = {}
        return self.settings.remove(TOKEN_KEY)

    def register(self, **credentials):
        """
        This function is used for registering to balena.

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
            >>> balena.auth.register(**credentials)
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6NTM5OCwidXNlcm5hbWUiOiJ0ZXN0MjcxMCIsImVtYWlsIjoidGVzdDI3MTBAZ21haWwuY29tIiwic29jaWFsX3NlcnZpY2VfYWNjb3VudCI6bnVsbCwiaGFzX2Rpc2FibGVkX25ld3NsZXR0ZXIiOmZhbHNlLCJqd3Rfc2VjcmV0IjoiQlJXR0ZIVUgzNVBKT0VKTVRSSVo2MjdINjVKVkJKWDYiLCJoYXNQYXNzd29yZFNldCI6dHJ1ZSwibmVlZHNQYXNzd29yZFJlc2V0IjpmYWxzZSwicHVibGljX2tleSI6ZmFsc2UsImZlYXR1cmVzIjpbXSwiaW50ZXJjb21Vc2VyTmFtZSI6InRlc3QyNzEwIiwiaW50ZXJjb21Vc2VySGFzaCI6IjNiYTRhZDRkZjk4MDQ1OTc1YmU2ZGUwYWJmNjFiYjRmYWY4ZmEzYTljZWI0YzE4Y2QxOGU1NmViNmI1NzkxZDAiLCJwZXJtaXNzaW9ucyI6W10sImlhdCI6MTQ0ODI1NzgyOCwiZXhwIjoxNDQ4ODYyNjI4fQ.chhf6deZ9BNDMmPr1Hm-SlRoWkK7t_4cktAPo12aCoE'

        """

        return self.base_request.request(
            'user/register', 'POST', data=credentials,
            endpoint=self.settings.get('api_endpoint'), auth=False
        )
