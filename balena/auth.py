from . import exceptions
from .balena_auth import request
from .settings import Settings
from typing import TypedDict, Optional, Literal, Union, cast
from typing_extensions import Unpack
from .pine import PineClient
from .twofactor_auth import TwoFactorAuth


TOKEN_KEY = "token"


class CredentialsType(TypedDict):
    username: str
    password: str


class WhoamiResult(TypedDict):
    id: int
    username: str
    email: str


class Auth:
    """
    This class implements all authentication functions for balena python SDK.

    """

    _user_detail_cache: Optional[WhoamiResult] = None
    _user_actor_id_cache: Optional[int] = None

    def __init__(self, pine: PineClient, settings: Settings):
        self.two_factor = TwoFactorAuth(settings)
        self.__pine = pine
        self.__settings = settings

    def __get_user_details(self, no_cache: bool = False) -> Optional[WhoamiResult]:
        """
        Get user details from token.

        Returns:
            Optional[WhoamiResult]: user details.
        """
        if not self._user_detail_cache or no_cache:
            whoami = request(method="GET", settings=self.__settings, path="/user/v1/whoami")
            if isinstance(whoami, dict) and set(whoami.keys()) == set(["id", "username", "email"]):
                self._user_detail_cache = cast(WhoamiResult, whoami)
            else:
                raise exceptions.NotLoggedIn()

        return self._user_detail_cache

    def __get_property(self, element: Literal["id", "username", "email"]) -> Union[str, int]:
        """
        Get a property from user details.

        Args:
            element (Literal["id", "username", "email"]): property name.

        Returns:
            Union[str, int]: property value.
        """
        details = self.__get_user_details()
        if details:
            return details[element]
        else:
            raise exceptions.InvalidOption(element)

    def whoami(self) -> str:
        """
        Return current logged in username.

        Returns:
            str: username.

        Examples:
            >>> balena.auth.whoami()
        """
        return str(self.__get_property("username"))

    def authenticate(self, **credentials: Unpack[CredentialsType]) -> str:
        """
        This function authenticates provided credentials information.
        You should use Auth.login when possible, as it takes care of saving the Auth Token and username as well.

        Args:
            **credentials: credentials keyword arguments.
                username (str): Balena username.
                password (str): Password.

        Returns:
            str: Auth Token,

        Examples:
            >>> balena.auth.authenticate(username='<your email>', password='<your password>')
        """
        req = request(
            method="POST", settings=self.__settings, path="login_", body=credentials, send_token=False, return_raw=True
        )

        if not req.ok:
            if req.status_code == 401:
                raise exceptions.LoginFailed()
            elif req.status_code == 429:
                raise exceptions.TooManyRequests()

        return req.content.decode()

    def login(self, **credentials: Unpack[CredentialsType]) -> None:
        """
        This function is used for logging into balena using email and password.

        Args:
            **credentials: credentials keyword arguments.
                username (str): Balena email.
                password (str): Password.

        Examples:
            >>> from balena import Balena
            ... balena = Balena()
            ... credentials = {'username': '<your email>', 'password': '<your password>'}
            ... balena.auth.login(**credentials)
            ... # or
            ... balena.auth.login(username='<your email>', password='<your password>')
        """
        token = self.authenticate(**credentials)
        self._user_detail_cache = None
        self._user_actor_id_cache = None
        self.__settings.set(TOKEN_KEY, token)

    def login_with_token(self, token: str) -> None:
        """
        This function is used for logging into balena using Auth Token.
        Auth Token can be found in Preferences section on balena Dashboard.

        Args:
            token (str): Auth Token.

        Returns:
            This functions saves Auth Token to Settings and returns nothing.

        Examples:
            >>> from balena import Balena
            >>> balena = Balena()
            >>> auth_token = <your token>
            >>> balena.auth.login_with_token(auth_token)

        """
        self._user_detail_cache = None
        self._user_actor_id_cache = None
        self.__settings.set(TOKEN_KEY, token)

    def is_logged_in(self) -> bool:
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
            self.__get_user_details(True)
            return True
        except (
            exceptions.RequestError,
            exceptions.Unauthorized,
            exceptions.NotLoggedIn,
        ):
            return False

    def get_token(self) -> Optional[str]:
        """
        This function retrieves Auth Token.

        Returns:
            str: Auth Token.

        Examples:
            >>> balena.auth.get_token()
        """
        try:
            return self.__settings.get(TOKEN_KEY)
        except exceptions.InvalidOption:
            return None

    def get_user_id(self) -> int:
        """
        This function retrieves current logged in user's id.

        Returns:
            int: user id.

        Examples:
            # If you are logged in.
            >>> balena.auth.get_user_id()
        """
        return int(self.__get_property("id"))

    def get_user_actor_id(self) -> int:
        """
        Get current logged in user's actor id.

        Returns:
            int: User actor id

        Examples:
            # If you are logged in.
            >>> balena.auth.get_user_actor_id()
        """
        return self.__pine.get(
            {
                "resource": "user",
                "id": self.get_user_id(),
                "options": {"$select": "actor"},
            }
        )["actor"]

    def get_email(self) -> str:
        """
        This function retrieves current logged in user's get_email

        Returns:
            str: user email.

        Examples:
            # If you are logged in.
            >>> balena.auth.get_email()
        """
        return str(self.__get_property("email"))

    def logout(self) -> None:
        """
        This function is used for logging out from balena.

        Examples:
            # If you are logged in.
            >>> balena.auth.logout()
        """
        self._user_detail_cache = None
        self._user_actor_id_cache = None
        self.__settings.remove(TOKEN_KEY)

    def register(self, **creentials: Unpack[CredentialsType]) -> str:
        """
        This function is used for registering to balena.

        Args:
            **credentials: credentials keyword arguments.
                email (str): email to register.
                password (str): Password.

        Returns:
            str: Auth Token for new account.

        Examples:
            >>> credentials = {'email': '<your email>', 'password': '<your password>'}
            >>> balena.auth.register(**credentials)
        """
        return request(
            method="POST",
            settings=self.__settings,
            path="/user/register",
            body=creentials,
            send_token=False,
        )
