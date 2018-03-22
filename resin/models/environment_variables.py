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
        self.service_environment_variable = ServiceEnvVariable()
        self.device_service_environment_variable = DeviceServiceEnvVariable()


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
            >>> resin.models.environment_variables.device_service_environment_variable.get_all('f5213eac0d63ac47721b037a7406d306')
            [{u'name': u'dev_proxy', u'created_at': u'2018-03-16T19:23:21.727Z', u'__metadata': {u'type': u'', u'uri': u'/resin/device_service_environment_variable(28888)'}, u'value': u'value', u'service_install': [{u'__metadata': {u'type': u'', u'uri': u'/resin/service_install(30788)'}, u'id': 30788, u'service': [{u'service_name': u'proxy', u'__metadata': {u'type': u'', u'uri': u'/resin/service(NaN)'}}]}], u'id': 28888}, {u'name': u'dev_data', u'created_at': u'2018-03-16T19:23:11.614Z', u'__metadata': {u'type': u'', u'uri': u'/resin/device_service_environment_variable(28887)'}, u'value': u'dev_data_value', u'service_install': [{u'__metadata': {u'type': u'', u'uri': u'/resin/service_install(30789)'}, u'id': 30789, u'service': [{u'service_name': u'data', u'__metadata': {u'type': u'', u'uri': u'/resin/service(NaN)'}}]}], u'id': 28887}, {u'name': u'dev_data1', u'created_at': u'2018-03-17T05:53:19.257Z', u'__metadata': {u'type': u'', u'uri': u'/resin/device_service_environment_variable(28964)'}, u'value': u'aaaa', u'service_install': [{u'__metadata': {u'type': u'', u'uri': u'/resin/service_install(30789)'}, u'id': 30789, u'service': [{u'service_name': u'data', u'__metadata': {u'type': u'', u'uri': u'/resin/service(NaN)'}}]}], u'id': 28964}]

        """

        # TODO: pine client for python
        device = self.device.get(uuid)

        query = '$expand=service_install($select=id&$expand=service($select=service_name))&$filter=service_install/any(d:d/device%20eq%20{device_id})'.format(device_id=device['id'])

        return self.base_request.request(
            'device_service_environment_variable', 'GET', raw_query=query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']
        #return env_vars

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


class ServiceEnvVariable(object):
    """
    This class implements service environment variable model for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.service = Service()

    def get_all(self, app_id):
        """
        Get all service environment variables by application.

        Args:
            app_id (str): application id.

        Returns:
            list: service application environment variables.

        Examples:
            >>> resin.models.environment_variables.service_environment_variable.get_all('1005160')
            [{u'name': u'app_data', u'service': {u'__deferred': {u'uri': u'/resin/service(21667)'}, u'__id': 21667}, u'created_at': u'2018-03-16T19:21:21.087Z', u'__metadata': {u'type': u'', u'uri': u'/resin/service_environment_variable(12365)'}, u'value': u'app_data_value', u'id': 12365}, {u'name': u'app_data1', u'service': {u'__deferred': {u'uri': u'/resin/service(21667)'}, u'__id': 21667}, u'created_at': u'2018-03-16T19:21:49.662Z', u'__metadata': {u'type': u'', u'uri': u'/resin/service_environment_variable(12366)'}, u'value': u'app_data_value', u'id': 12366}, {u'name': u'app_front', u'service': {u'__deferred': {u'uri': u'/resin/service(21669)'}, u'__id': 21669}, u'created_at': u'2018-03-16T19:22:06.955Z', u'__metadata': {u'type': u'', u'uri': u'/resin/service_environment_variable(12367)'}, u'value': u'front_value', u'id': 12367}]


        """

        # TODO: pine client for python
        raw_query = '$expand=service&$filter=service/any(a:a/application%20eq%20{app_id})'.format(app_id=app_id)

        return self.base_request.request(
            'service_environment_variable', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def create(self, app_id, service_name, env_var_name, value):
        """
        Create a service environment variable for application.

        Args:
            app_id (str): application id.
            service_name(str): service name.
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Returns:
            str: new service environment variable info.

        Examples:
            >>> resin.models.environment_variables.service_environment_variable.create('1005160', 'proxy', 'app_proxy', 'test value')
            {"id":12444,"created_at":"2018-03-18T09:34:09.144Z","service":{"__deferred":{"uri":"/resin/service(21668)"},"__id":21668},"name":"app_proxy","value":"test value","__metadata":{"uri":"/resin/service_environment_variable(12444)","type":""}}

        """

        if not _is_valid_env_var_name(env_var_name):
            raise exceptions.InvalidParameter('env_var_name', env_var_name)

        services = self.service.get_all_by_application(app_id)
        service_id = [i['id'] for i in services if i['service_name'] == service_name]

        data = {
            'name': env_var_name,
            'value': value,
            'service': service_id
        }
        return json.loads(self.base_request.request(
            'service_environment_variable', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint')
        ).decode('utf-8'))

    def update(self, var_id, value):
        """
        Update a service environment variable value for application.

        Args:
            var_id (str): service environment variable id.
            value (str): new service environment variable value.

        Examples:
            >>> resin.models.environment_variables.service_environment_variable.update('12444', 'new test value')
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
            'service_environment_variable', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def remove(self, var_id):
        """
        Remove service environment variable.

        Args:
            var_id (str): service environment variable id.

        Examples:
            >>> resin.models.environment_variables.service_environment_variable.remove('12444')
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': var_id
        }
        return self.base_request.request(
            'service_environment_variable', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )
