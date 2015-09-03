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
            dict: new device environment variable info.

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

        """

        params = {
            'filter': 'id',
            'eq': var_id
        }
        return self.base_request.request(
            'device_environment_variable', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
    """
    This class implements application environment variable model for Resin Python SDK.

    Attributes:
        SYSTEM_VARIABLE_RESERVED_NAMES (list): list of reserved system variable names.
        OTHER_RESERVED_NAMES_START (list): list of prefix for system variable.

    """

        )


class ApplicationEnvVariable(object):
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
            dict: new application environment info.

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

        """

        if variable in self.SYSTEM_VARIABLE_RESERVED_NAMES:
            return True
        return variable.startswith(self.OTHER_RESERVED_NAMES_START)
