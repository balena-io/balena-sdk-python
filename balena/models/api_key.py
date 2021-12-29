from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions
from .application import Application


class ApiKey:
    """
    This class implements user API key model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.application = Application()

    def create_api_key(self, name, description=None):
        """
        This function registers a new api key for the current user with the name given.

        Args:
            name (str): user API key name.
            description (Optional[str]): API key description.

        Returns:
            str: user API key.

        Examples:
            >>> balena.models.api_key.create_api_key('myApiKey')
            3YHD9DVPLe6LbjEgQb7FEFXYdtPEMkV9

        """

        data = {
            'name': name,
            'description': description
        }

        return self.base_request.request(
            '/api-key/user/full', 'POST', data=data,
            endpoint=self.settings.get('api_endpoint')
        )

    def get_all(self):
        """
        This function gets all API keys.

        Returns:
            list: user API key.

        Examples:
            >>> balena.models.api_key.get_all()
            [{u'description': None, u'created_at': u'2018-04-06T03:53:34.189Z', u'__metadata': {u'type': u'', u'uri': u'/balena/api_key(1296047)'}, u'is_of__actor': {u'__deferred': {u'uri': u'/balena/actor(2454095)'}, u'__id': 2454095}, u'id': 1296047, u'name': u'myApiKey'}]

        """

        return self.base_request.request(
            'api_key', 'GET',
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def update(self, id, api_key_info):
        """
        This function updates details of an API key.

        Args:
            id (str): API key id.
            api_key_info: new API key info.
                name (str): new API key name.
                description (Optional[str]): new API key description.

        Examples:
            >>> balena.models.api_key.update(1296047, {'name':'new name')
            OK

        """

        data = api_key_info
        params = {
            'filter': 'id',
            'eq': id
        }

        return self.base_request.request(
            'api_key', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def revoke(self, id):
        """
        This function revokes an API key.

        Args:
            id (str): API key id.

        Examples:
            >>> balena.models.api_key.revoke(1296047)
            OK

        """

        params = {
            'filter': 'id',
            'eq': id
        }

        return self.base_request.request(
            'api_key', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )

    def get_provisioning_api_keys_by_application(self, app_id):
        """
        Get all provisioning API keys for an application.

        Args:
            app_id (str): application id.

        Examples:
            >>> balena.models.api_key.get_provisioning_api_keys_by_application(1296047)
            [{'id': 5492033, 'created_at': '2021-12-29T03:38:04.470Z', 'is_of__actor': {'__id': 6444453, '__deferred': {'uri': '/resin/actor(@id)?@id=6444453'}}, 'name': None, 'description': None, '__metadata': {'uri': '/resin/api_key(@id)?@id=5492033'}}, {'id': 5492044, 'created_at': '2021-12-29T03:41:04.441Z', 'is_of__actor': {'__id': 6444453, '__deferred': {'uri': '/resin/actor(@id)?@id=6444453'}}, 'name': 'key p1', 'description': 'key desc', '__metadata': {'uri': '/resin/api_key(@id)?@id=5492044'}}, {'id': 3111481, 'created_at': '2020-06-25T04:24:53.621Z', 'is_of__actor': {'__id': 6444453, '__deferred': {'uri': '/resin/actor(@id)?@id=6444453'}}, 'name': None, 'description': None, '__metadata': {'uri': '/resin/api_key(@id)?@id=3111481'}}]

        """

        app = self.application.get_by_id(app_id)

        params = {
            'filter': 'is_of__actor',
            'eq': app['actor']
        }

        return self.base_request.request(
            'api_key', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']
