from ..base_request import BaseRequest
from ..settings import Settings
from .config import Config
from .. import exceptions


class Application(object):
    """
    This class implements application model for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()

    def get_all(self):
        """
        Get all applications.

        Returns:
            list: list contains info of applications.

        Examples:
            >>> resin.models.application.get_all()
            [{u'app_name': u'RPI1', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9020)'}, u'git_repository': u'g_trong_nghia_nguyen@git.resin.io:g_trong_nghia_nguyen/rpi1.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi', u'commit': None, u'id': 9020}, {u'app_name': u'RPI2', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9019)'}, u'git_repository': u'g_trong_nghia_nguyen@git.resin.io:g_trong_nghia_nguyen/rpi2.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi2', u'commit': None, u'id': 9019}]

        """

        return self.base_request.request(
            'application', 'GET', endpoint=self.settings.get('pine_endpoint')
        )['d']

    def get(self, name):
        """
        Get a single application.

        Args:
            name (str): application name.

        Returns:
            dict: application info.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >>> resin.models.application.get('RPI1')
            {u'app_name': u'RPI1', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9020)'}, u'git_repository': u'g_trong_nghia_nguyen@git.resin.io:g_trong_nghia_nguyen/rpi1.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi', u'commit': None, u'id': 9020}

        """

        params = {
            'filter': 'app_name',
            'eq': name
        }
        try:
            return self.base_request.request(
                'application', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d'][0]
        except IndexError:
            raise exceptions.ApplicationNotFound(name)

    def has(self, name):
        """
        Check if an application exists.

        Args:
            name (str): application name.

        Returns:
            bool: True if application exists, False otherwise.

        Examples:
            >>> resin.models.application.has('RPI1')
            True

        """

        params = {
            'filter': 'app_name',
            'eq': name
        }
        app = self.base_request.request(
            'application', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']
        return bool(app)

    def has_any(self):
        """
        Check if the user has any applications.

        Returns:
            bool: True if user has any applications, False otherwise.

        Examples:
            >>> resin.models.application.has_any()
            True

        """

        apps = self.base_request.request(
            'application', 'GET', endpoint=self.settings.get('pine_endpoint')
        )['d']
        return bool(apps)

    def get_by_id(self, app_id):
        """
        Get a single application by application id.

        Args:
            app_id (str): application id.

        Returns:
            dict: application info.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >>> resin.models.application.get_by_id(9020)
            {u'app_name': u'RPI1', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9020)'}, u'git_repository': u'g_trong_nghia_nguyen@git.resin.io:g_trong_nghia_nguyen/rpi1.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi', u'commit': None, u'id': 9020}

        """

        params = {
            'filter': 'id',
            'eq': app_id
        }
        try:
            return self.base_request.request(
                'application', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d'][0]
        except IndexError:
            raise exceptions.ApplicationNotFound(app_id)

    def create(self, name, device_type):
        """
        Create an application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.
            device_type (str): device type (display form).

        Returns:
            dict: application info.

        Raises:
            InvalidDeviceType: if device type is not supported.

        Examples:
            >>> resin.models.application.create('Edison','Intel Edison')
            '{"id":9021,"user":{"__deferred":{"uri":"/ewa/user(5397)"},"__id":5397},"app_name":"Edison","git_repository":"g_trong_nghia_nguyen@git.resin.io:g_trong_nghia_nguyen/edison.git","commit":null,"device_type":"intel-edison","__metadata":{"uri":"/ewa/application(9021)","type":""}}'

        """

        device_types = self.config.get_device_types()
        device_slug = [device['slug'] for device in device_types
                       if device['name'] == device_type]
        if device_slug:
            data = {
                'app_name': name,
                'device_type': device_slug[0]
            }
            return self.base_request.request(
                'application', 'POST', data=data,
                endpoint=self.settings.get('pine_endpoint'), login=True
            )
        else:
            raise exceptions.InvalidDeviceType(device_type)

    def remove(self, name):
        """
        Remove application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.

        Examples:
            >>> resin.models.application.remove('Edison')
            'OK'

        """

        params = {
            'filter': 'app_name',
            'eq': name
        }
        return self.base_request.request(
            'application', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )

    def restart(self, name):
        """
        Restart application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >>> resin.models.application.restart('RPI1')
            'OK'

        """

        app = self.get(name)
        return self.base_request.request(
            'application/{0}/restart'.format(app['id']), 'POST',
            endpoint=self.settings.get('api_endpoint'), login=True
        )

    def get_api_key(self, name):
        """
        Get the API key for a specific application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.

        Returns:
            str: API key.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >>> resin.models.application.get_api_key('RPI1')
            u'XbKn5GhK4YieOLpX4KjQTqjqo1moRWmP'

        """

        app = self.get(name)
        return self.base_request.request(
            'application/{0}/generate-api-key'.format(app['id']), 'POST',
            endpoint=self.settings.get('api_endpoint'), login=True
        )
