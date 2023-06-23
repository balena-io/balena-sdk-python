from typing import List

from .. import exceptions
from ..auth import Auth
from ..pine import PineClient
from ..types import AnyObject
from ..types.models import SSHKeyType
from ..settings import Settings


class Key:
    """
    This class implements ssh key model for balena python SDK.

    """

    def __init__(self, pine: PineClient, settings: Settings):
        self.__pine = pine
        self.__auth = Auth(pine, settings)

    def get_all(self, options: AnyObject = {}) -> List[SSHKeyType]:
        """
        Get all ssh keys.

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[SSHKeyType]: list of ssh keys.
        """
        return self.__pine.get({"resource": "user__has__public_key", "options": options})

    def get(self, id: int) -> SSHKeyType:
        """
        Get a single ssh key.

        Args:
            id (int): key id.

        Returns:
            SSHKeyType: ssh key info.
        """

        key = self.__pine.get({"resource": "user__has__public_key", "id": id})

        if key is None:
            raise exceptions.KeyNotFound(id)

        return key

    def remove(self, id: int) -> None:
        """
        Remove a ssh key.

        Args:
            id (int): key id.
        """

        self.__pine.delete({"resource": "user__has__public_key", "id": id})

    def create(self, title: str, key: str) -> SSHKeyType:
        """
        Create a ssh key.

        Args:
            title (str): key title.
            key (str): the public ssh key.

        Returns:
            SSHKeyType: new ssh key id.
        """
        # Avoid ugly whitespaces
        key = key.strip()

        user_id = self.__auth.get_user_id()
        return self.__pine.post(
            {"resource": "user__has__public_key", "body": {"title": title, "public_key": key, "user": user_id}}
        )
