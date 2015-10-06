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

        """

        app = self.get(name)
        return self.base_request.request(
            'application/{0}/generate-api-key'.format(app['id']), 'POST',
            endpoint=self.settings.get('api_endpoint'), login=True
        )
