import re
import json

from ..base_request import BaseRequest
from .device import Device
from ..settings import Settings
from .. import exceptions


def _is_valid_config_var_name(config_var_name):
    return config_var_name.startswith('RESIN_')


class ConfigVariable(object):
    """
    This class is a wrapper for config variable models.

    """

    def __init__(self):
        self.device_config_variable = DeviceConfigVariable()
        self.application_config_variable = ApplicationConfigVariable()


class DeviceConfigVariable(object):
    """
    This class implements device config variable model for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.device = Device()
        self.settings = Settings()

    def get_all(self, uuid):
        """
        Get all device config variables belong to a device.

        Args:
            uuid (str): device uuid.

        Returns:
            list: device config variables.

        Examples:
            >>> resin.models.config_variable.device_config_variable.get_all('f5213eac0d63ac47721b037a7406d306')
            [{u'device': {u'__deferred': {u'uri': u'/resin/device(1036574)'}, u'__id74}, u'__metadata': {u'type': u'', u'uri': u'/resin/device_config_variab8)'}, u'id': 130598, u'value': u'1', u'name': u'RESIN_HOST_CONFIG_avoid_'}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1036574)'}, u'_36574}, u'__metadata': {u'type': u'', u'uri': u'/resin/device_config_var0597)'}, u'id': 130597, u'value': u'1', u'name': u'RESIN_HOST_CONFIG_disash'}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1036574)'},  1036574}, u'__metadata': {u'type': u'', u'uri': u'/resin/device_config_(130596)'}, u'id': 130596, u'value': u'"i2c_arm=on","spi=on","audio=on"'': u'RESIN_HOST_CONFIG_dtparam'}, {u'device': {u'__deferred': {u'uri': udevice(1036574)'}, u'__id': 1036574}, u'__metadata': {u'type': u'', u'uresin/device_config_variable(130595)'}, u'id': 130595, u'value': u'16', uu'RESIN_HOST_CONFIG_gpu_mem'}, {u'device': {u'__deferred': {u'uri': u'/rice(1036574)'}, u'__id': 1036574}, u'__metadata': {u'type': u'', u'uri':n/device_config_variable(130594)'}, u'id': 130594, u'value': u'false', uu'RESIN_HOST_LOG_TO_DISPLAY'}]

        """

        device = self.device.get(uuid)

        params = {
            'filter': 'device',
            'eq': device['id']
        }

        return self.base_request.request(
            'device_config_variable', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def create(self, uuid, config_var_name, value):
        """
        Create a device config variable.

        Args:
            uuid (str): device uuid.
            config_var_name (str): device config variable name.
            value (str): device config variable value.

        Returns:
            dict: new device config variable info.

        Examples:
            >>> resin.models.environment_variables.device_service_environment_variable.create('f5213eac0d63ac47721b037a7406d306', 'data', 'dev_data_sdk', 'test1')
            {"id":28970,"created_at":"2018-03-17T10:13:14.184Z","service_install":{"__deferred":{"uri":"/resin/service_install(30789)"},"__id":30789},"value":"test1","name":"dev_data_sdk","__metadata":{"uri":"/resin/device_service_environment_variable(28970)","type":""}}

        """

        if not _is_valid_config_var_name(config_var_name):
            raise exceptions.InvalidParameter('config_var_name', config_var_name)

        device = self.device.get(uuid)

        data = {
            'device': device['id'],
            'application': device['belongs_to__application']['__id'],
            'name': config_var_name,
            'value': value
        }

        return json.loads(self.base_request.request(
            'device_config_variable', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint')
        ).decode('utf-8'))

    def update(self, var_id, value):
        """
        Update a device config variable.

        Args:
            var_id (str): device config variable id.
            value (str): new device config variable value.

        Examples:
            >>> resin.models.config_variable.device_config_variable.update('132715', 'new test value')
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
            'device_config_variable', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def remove(self, var_id):
        """
        Remove a device config environment variable.

        Args:
            var_id (str): device config environment variable id.

        Examples:
            >>> resin.models.config_variable.device_config_variable.remove('132715')
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': var_id
        }
        return self.base_request.request(
            'device_config_variable', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )


class ApplicationConfigVariable(object):
    """
    This class implements application config variable model for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def get_all(self, app_id):
        """
        Get all application config variables belong to an application.

        Args:
            app_id (str): application id.

        Returns:
            list: application config variables.

        Examples:
            >>> resin.models.config_variable.application_config_variable.get_all('1005160')
            [{u'application': {u'__deferred': {u'uri': u'/resin/application(1005160)'}, u'__id': 1005160}, u'__metadata': {u'type': u'', u'uri': u'/resin/application_config_variable(116965)'}, u'id': 116965, u'value': u'false', u'name': u'RESIN_SUPERVISOR_NATIVE_LOGGER'}]

        """

        params = {
            'filter': 'application',
            'eq': app_id
        }

        return self.base_request.request(
            'application_config_variable', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def create(self, app_id, config_var_name, value):
        """
        Create an application config variable.

        Args:
            app_id (str): application id.
            config_var_name (str): application config variable name.
            value (str): application config variable value.

        Returns:
            dict: new application config variable info.

        Examples:
            >>> print(resin.models.config_variable.application_config_variable.create('1005160', 'RESIN_TEST_APP_CONFIG_VAR', 'test value'))
            {"id":117738,"application":{"__deferred":{"uri":"/resin/application(1005160)"},"__id":1005160},"name":"RESIN_TEST_APP_CONFIG_VAR","value":"test value","__metadata":{"uri":"/resin/application_config_variable(117738)","type":""}}

        """

        if not _is_valid_config_var_name(config_var_name):
            raise exceptions.InvalidParameter('config_var_name', config_var_name)

        data = {
            'application': app_id,
            'name': config_var_name,
            'value': value
        }

        return json.loads(self.base_request.request(
            'application_config_variable', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint')
        ).decode('utf-8'))

    def update(self, var_id, value):
        """
        Update an application config variable.

        Args:
            var_id (str): application config variable id.
            value (str): new application config variable value.

        Examples:
            >>> resin.models.config_variable.application_config_variable.update('117738', 'new test value')
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
            'application_config_variable', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def remove(self, var_id):
        """
        Remove a application config environment variable.

        Args:
            var_id (str): application config environment variable id.

        Examples:
            >>> resin.models.config_variable.application_config_variable.remove('117738')
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': var_id
        }
        return self.base_request.request(
            'application_config_variable', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )
