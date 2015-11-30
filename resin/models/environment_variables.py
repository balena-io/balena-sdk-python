import re

from ..base_request import BaseRequest
from .device import Device
from ..settings import Settings


class EnvironmentVariable(object):
    """
    This class is a wrapper for device and application environment variable models.

    """

    def __init__(self):
        self.device = DeviceEnvVariable()
        self.application = ApplicationEnvVariable()


class DeviceEnvVariable(object):
    """
    This class implements device environment variable model for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.device = Device()
        self.settings = Settings()

    def get_all(self, uuid):
        """
        Get all device environment variables.

        Args:
            uuid (str): device uuid.

        Returns:
            list: device environment variables.

        Examples:
            >>> resin.models.environment_variables.device.get_all('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            [{u'device': {u'__deferred': {u'uri': u'/ewa/device(122950)'}, u'__id': 122950}, u'__metadata': {u'type': u'', u'uri': u'/ewa/device_environment_variable(2173)'}, u'id': 2173, u'value': u'1322944771964103', u'env_var_name': u'RESIN_DEVICE_RESTART'}]

        """

        device = self.device.get(uuid)
        params = {
            'filter': 'device',
            'eq': device['id']
        }
        return self.base_request.request(
            'device_environment_variable', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def create(self, uuid, name, value):
        """
        Create a device environment variable.

        Args:
            uuid (str): device uuid.
            name (str): environment variable name.
            value (str): environment variable value.

        Returns:
            str: new device environment variable info.

        Examples:
            >>> resin.models.environment_variables.device.create('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143','tmp-env-var', 'test')
            '{"id":2184,"device":{"__deferred":{"uri":"/ewa/device(122950)"},"__id":122950},"env_var_name":"tmp-env-var","value":"test","__metadata":{"uri":"/ewa/device_environment_variable(2184)","type":""}}'

        """

        device = self.device.get(uuid)
        data = {
            'device': device['id'],
            'env_var_name': name,
            'value': value
        }
        return self.base_request.request(
            'device_environment_variable', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def update(self, var_id, value):
        """
        Update a device environment variable.

        Args:
            var_id (str): environment variable id.
            value (str): new environment variable value.

        Examples:
            >>> resin.models.environment_variables.device.update(2184, 'new value')
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': var_id
        }
        data = {
            'value': value
        }
        return self.base_request.request(
            'device_environment_variable', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def remove(self, var_id):
        """
        Remove a device environment variable.

        Args:
            var_id (str): environment variable id.

        Examples:
            >>> resin.models.environment_variables.device.remove(2184)
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': var_id
        }
        return self.base_request.request(
            'device_environment_variable', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )


class ApplicationEnvVariable(object):
    """
    This class implements application environment variable model for Resin Python SDK.

    Attributes:
        SYSTEM_VARIABLE_RESERVED_NAMES (list): list of reserved system variable names.
        OTHER_RESERVED_NAMES_START (list): list of prefix for system variable.

    """

    SYSTEM_VARIABLE_RESERVED_NAMES = ['RESIN', 'USER']
    OTHER_RESERVED_NAMES_START = 'RESIN_'

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def get_all(self, app_id):
        """
        Get all environment variables by application.

        Args:
            app_id (str): application id.

        Returns:
            list: application environment variables.

        Examples:
            >>> resin.models.environment_variables.application.get_all(9020)
            [{u'application': {u'__deferred': {u'uri': u'/ewa/application(9020)'}, u'__id': 9020}, u'__metadata': {u'type': u'', u'uri': u'/ewa/environment_variable(5650)'}, u'id': 5650, u'value': u'7330634368117899', u'name': u'RESIN_RESTART'}]

        """

        params = {
            'filter': 'application',
            'eq': app_id
        }
        return self.base_request.request(
            'environment_variable', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def create(self, app_id, name, value):
        """
        Create an environment variable for application.

        Args:
            app_id (str): application id.
            name (str): environment variable name.
            value (str): environment variable value.

        Returns:
            str: new application environment info.

        Examples:
            >>> resin.models.environment_variables.application.create(9020, 'app-test-env', 'test')
            '{"id":5652,"application":{"__deferred":{"uri":"/ewa/application(9020)"},"__id":9020},"name":"app-test-env","value":"test","__metadata":{"uri":"/ewa/environment_variable(5652)","type":""}}'

        """

        data = {
            'name': name,
            'value': value,
            'application': app_id
        }
        return self.base_request.request(
            'environment_variable', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def update(self, var_id, value):
        """
        Update an environment variable value for application.

        Args:
            var_id (str): environment variable id.
            value (str): new environment variable value.

        Examples:
            >>> resin.models.environment_variables.application.update(5652, 'new value')
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': var_id
        }

        data = {
            'value': value
        }
        return self.base_request.request(
            'environment_variable', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def remove(self, var_id):
        """
        Remove application environment variable.

        Args:
            var_id (str): environment variable id.

        Examples:
            >>> resin.models.environment_variables.application.remove(5652)
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': var_id
        }
        return self.base_request.request(
            'environment_variable', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )

    def is_system_variable(self, variable):
        """
        Check if a variable is system specific.

        Args:
            variable (str): environment variable name.

        Returns:
            bool: True if system variable, False otherwise.

        Examples:
            >>> resin.models.environment_variables.application.is_system_variable('RESIN_API_KEY')
            True
            >>> resin.models.environment_variables.application.is_system_variable('APPLICATION_API_KEY')
            False

        """

        if variable in self.SYSTEM_VARIABLE_RESERVED_NAMES:
            return True
        return variable.startswith(self.OTHER_RESERVED_NAMES_START)
