import json

from ..base_request import BaseRequest
from ..settings import Settings
from ..token import Token
from .. import exceptions


class Key(object):
    """
    This class implements ssh key model for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.token = Token()

    def get_all(self):
        """
        Get all ssh keys.

        Returns:
            list: list of ssh keys.

        """
        return self.base_request.request(
            'user__has__public_key', 'GET',
            endpoint=Settings.get('pine_endpoint')
        )['d']

    def get(self, id):
        """
        Get a single ssh key.

        Args:
            id (str): key id.

        Returns:
            dict: ssh key info.

        Raises:
            KeyNotFound: if ssh key couldn't be found.

        """

        params = {
            'filter': 'id',
            'eq': id
        }
        key = self.base_request.request(
            'user__has__public_key', 'GET', params=params,
            endpoint=Settings.get('pine_endpoint')
        )['d']
        if key:
            return key[0]
        else:
            raise exceptions.KeyNotFound(id)

    def remove(self, id):
        """
        Remove a ssh key. This function only works if you log in using credentials or Auth Token.

        Args:
            id (str): key id.

        """

        params = {
            'filter': 'id',
            'eq': id
        }
        return self.base_request.request(
            'user__has__public_key', 'DELETE', params=params,
            endpoint=Settings.get('pine_endpoint'), login=True
        )

    def create(self, title, key):
        """
        Create a ssh key. This function only works if you log in using credentials or Auth Token.

        Args:
            title (str): key title.
            key (str): the public ssh key.

        Returns:
            str: new ssh key id.

        """

        # Trim ugly whitespaces
        key = key.strip()

        data = {
            'title': title,
            'public_key': key,
            'user': self.token.get_user_id()
        }
        key = self.base_request.request(
            'user__has__public_key', 'POST', data=data,
            endpoint=Settings.get('pine_endpoint'), login=True
        )
        return json.loads(key)['id']
