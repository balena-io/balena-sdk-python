import re
import json

from ..base_request import BaseRequest
from .device import Device
from ..settings import Settings
from .. import exceptions


def _is_valid_env_var_name(env_var_name):
    return re.match('^[a-zA-Z_]+[a-zA-Z0-9_]*$', env_var_name)


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

    def _fix_device_env_var_name_key(self, env_var):
        """
        Internal method to workaround the fact that applications environment variables contain a `name` property
        while device environment variables contain an `env_var_name` property instead.
        """

        if 'env_var_name' in env_var:
            env_var['name'] = env_var['env_var_name']
            env_var.pop('env_var_name', None)
        return env_var

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

    def create(self, uuid, env_var_name, value):
        """
        Create a device environment variable.

        Args:
            uuid (str): device uuid.
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Returns:
            dict: new device environment variable info.

        Examples:
            >>> resin.models.environment_variables.device.create('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143','test_env4', 'testing1')
            {'name': u'test_env4', u'__metadata': {u'type': u'', u'uri': u'/resin/device_environment_variable(42166)'}, u'value': u'testing1', u'device': {u'__deferred': {u'uri': u'/resin/device(115792)'}, u'__id': 115792}, u'id': 42166}

        """

        if not _is_valid_env_var_name(env_var_name):
            raise exceptions.InvalidParameter('env_var_name', env_var_name)
        device = self.device.get(uuid)
        data = {
            'device': device['id'],
            'env_var_name': env_var_name,
            'value': value
        }
        new_env_var = json.loads(self.base_request.request(
            'device_environment_variable', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint')
        ).decode('utf-8'))
        return self._fix_device_env_var_name_key(new_env_var)

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

    def get_all_by_application(self, app_id):
        """
        Get all device environment variables for an application.

        Args:
            app_id (str): application id.

        Returns:
            list: list of device environment variables.

        Examples:
            >>> resin.models.environment_variables.device.get_all_by_application('5780')
            [{'name': u'device1', u'__metadata': {u'type': u'', u'uri': u'/resin/device_environment_variable(40794)'}, u'value': u'test', u'device': {u'__deferred': {u'uri': u'/resin/device(115792)'}, u'__id': 115792}, u'id': 40794}, {'name': u'RESIN_DEVICE_RESTART', u'__metadata': {u'type': u'', u'uri': u'/resin/device_environment_variable(1524)'}, u'value': u'961506585823372', u'device': {u'__deferred': {u'uri': u'/resin/device(121794)'}, u'__id': 121794}, u'id': 1524}]

        """

        params = {
            'filter': 'device/belongs_to__application',
            'eq': app_id
        }
        env_list = self.base_request.request(
            'device_environment_variable', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint'))
        return list(map(self._fix_device_env_var_name_key, env_list['d']))


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

    def create(self, app_id, env_var_name, value):
        """
        Create an environment variable for application.

        Args:
            app_id (str): application id.
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Returns:
            dict: new application environment info.

        Examples:
            >>> resin.models.environment_variables.application.create('978062', 'test2', '123')
            {'id': 91138, 'application': {'__deferred': {'uri': '/resin/application(978062)'}, '__id': 978062}, 'name': 'test2', 'value': '123', '__metadata': {'uri': '/resin/environment_variable(91138)', 'type': ''}}

        """

        if not _is_valid_env_var_name(env_var_name):
            raise exceptions.InvalidParameter('env_var_name', env_var_name)
        data = {
            'name': env_var_name,
            'value': value,
            'application': app_id
        }
        return json.loads(self.base_request.request(
            'environment_variable', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint')
        ).decode('utf-8'))

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
