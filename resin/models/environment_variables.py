import re

from ..base_request import BaseRequest
from .device import Device
from ..settings import Settings


class EnvironmentVariable(object):

    def __init__(self):
        self.device = DeviceEnvVariable()
        self.application = ApplicationEnvVariable()


class DeviceEnvVariable(object):
    def __init__(self):
        self.base_request = BaseRequest()
        self.device = Device()
        self.settings = Settings()

    def get_all(self, uuid):
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
        params = {
            'filter': 'id',
            'eq': var_id
        }
        return self.base_request.request(
            'device_environment_variable', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )


class ApplicationEnvVariable(object):
    SYSTEM_VARIABLE_RESERVED_NAMES = ['RESIN', 'USER']
    OTHER_RESERVED_NAMES_START = 'RESIN_'

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def get_all(self, app_id):
        params = {
            'filter': 'application',
            'eq': app_id
        }
        return self.base_request.request(
            'environment_variable', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def create(self, app_id, name, value):
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
        params = {
            'filter': 'id',
            'eq': var_id
        }
        return self.base_request.request(
            'environment_variable', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )

    def is_system_variable(self, variable):

        if variable in self.SYSTEM_VARIABLE_RESERVED_NAMES:
            return True
        return variable.startswith(self.OTHER_RESERVED_NAMES_START)
