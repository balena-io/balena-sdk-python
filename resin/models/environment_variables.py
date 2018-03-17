import re
import json

from ..base_request import BaseRequest
from .device import Device
from ..settings import Settings
from .. import exceptions
from .service import Service
from .service_install import ServiceInstall


def _is_valid_env_var_name(env_var_name):
    return re.match('^[a-zA-Z_]+[a-zA-Z0-9_]*$', env_var_name)


class EnvironmentVariable(object):
    """
    This class is a wrapper for environment variable models.

    """

    def __init__(self):
        self.device_service_environment_variable = DeviceServiceEnvVariable()
        self.application = ApplicationEnvVariable()

class DeviceServiceEnvVariable(object):
    """
    This class implements device service variable model for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.device = Device()
        self.settings = Settings()
        self.service = Service()
        self.service_install = ServiceInstall()

    def get_all(self, uuid):
        """
        Get all device service environment variables belong to a device.

        Args:
            uuid (str): device uuid.

        Returns:
            list: device service environment variables.

        Examples:
            >>> resin.models.environment_variables.device.get_all('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            [{u'device': {u'__deferred': {u'uri': u'/ewa/device(122950)'}, u'__id': 122950}, u'__metadata': {u'type': u'', u'uri': u'/ewa/device_environment_variable(2173)'}, u'id': 2173, u'value': u'1322944771964103', u'env_var_name': u'RESIN_DEVICE_RESTART'}]

        """

        device = self.device.get(uuid)
        service_installs = self.service_install.get_all_by_device(device['id'])

        env_vars = []
        for service_install in service_installs:
            params = {
                'filter': 'service_install',
                'eq': service_install['id']
            }

            env_vars += (self.base_request.request(
                'device_service_environment_variable', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d'])
        return env_vars

    def create(self, uuid, service_name, env_var_name, value):
        """
        Create a device service environment variable.

        Args:
            uuid (str): device uuid.
            service_name (str): service name.
            env_var_name (str): device service environment variable name.
            value (str): device service environment variable value.

        Returns:
            dict: new device service environment variable info.

        Examples:
            >>> resin.models.environment_variables.device_service_environment_variable.create('f5213eac0d63ac47721b037a7406d306', 'data', 'dev_data_sdk', 'test1')
            {"id":28970,"created_at":"2018-03-17T10:13:14.184Z","service_install":{"__deferred":{"uri":"/resin/service_install(30789)"},"__id":30789},"value":"test1","name":"dev_data_sdk","__metadata":{"uri":"/resin/device_service_environment_variable(28970)","type":""}}

        """

        if not _is_valid_env_var_name(env_var_name):
            raise exceptions.InvalidParameter('env_var_name', env_var_name)

        device = self.device.get(uuid)
        services = self.service.get_all_by_application(device['belongs_to__application']['__id'])
        service_id = [i['id'] for i in services if i['service_name'] == service_name]
        if service_id:
            service_installs = self.service_install.get_all_by_device(device['id'])
            service_install_id = [i['id'] for i in service_installs if i['installs__service']['__id'] == service_id[0]]

            data = {
                'service_install': service_install_id[0],
                'name': env_var_name,
                'value': value
            }

            return json.loads(self.base_request.request(
                'device_service_environment_variable', 'POST', data=data,
                endpoint=self.settings.get('pine_endpoint')
            ).decode('utf-8'))
        else:
            raise exceptions.ServiceNotFound(service_name)

    def update(self, var_id, value):
        """
        Update a device service environment variable.

        Args:
            var_id (str): device environment variable id.
            value (str): new device environment variable value.

        Examples:
            >>> resin.models.environment_variables.device_service_environment_variable.update('28970', 'test1 new value')
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
            'device_service_environment_variable', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def remove(self, var_id):
        """
        Remove a device service environment variable.

        Args:
            var_id (str): device service environment variable id.

        Examples:
            >>> resin.models.environment_variables.device_service_environment_variable.remove('28970')
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': var_id
        }
        return self.base_request.request(
            'device_service_environment_variable', 'DELETE', params=params,
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
