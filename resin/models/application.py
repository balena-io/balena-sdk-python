from ..base_request import BaseRequest
from ..settings import Settings
from .config import Config
from .. import exceptions

class Application(object):

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()

    def get_all(self):
        return self.base_request.request('application', 'GET', endpoint=self.settings.get('pine_endpoint'))['d']

    def get(self, name):
        params = {
            'filter': 'app_name',
            'eq': name
        }
        try:
            return self.base_request.request('application', 'GET', params=params, endpoint=self.settings.get('pine_endpoint'))['d'][0]
        except IndexError:
            raise exceptions.ApplicationNotFound(name)

    def has(self, name):
        params = {
            'filter': 'app_name',
            'eq': name
        }
        app = self.base_request.request('application', 'GET', params=params, endpoint=self.settings.get('pine_endpoint'))['d']
        return bool(app)

    def has_any(self):
        apps = self.base_request.request('application', 'GET', endpoint=self.settings.get('pine_endpoint'))['d']
        return bool(apps)

    def get_by_id(self, app_id):
        params = {
            'filter': 'id',
            'eq': app_id
        }
        try:
            return self.base_request.request('application', 'GET', params=params, endpoint=self.settings.get('pine_endpoint'))['d'][0]
        except IndexError:
            raise exceptions.ApplicationNotFound(app_id)

    def create(self, name, device_type):
        device_types = self.config.get_device_types()
        device_slug = [device['slug'] for device in device_types
                        if device['name'] == device_type]
        if device_slug:
            data = {
                'app_name': name,
                'device_type': device_slug[0]
            }
            return self.base_request.request('application', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))
        else:
            raise exceptions.InvalidDeviceType(device_type)

    def remove(self, name):
        params = {
            'filter': 'app_name',
            'eq': name
        }
        return self.base_request.request('application', 'DELETE', params=params, endpoint=self.settings.get('pine_endpoint'))            

    def restart(self, name):
        app = self.get(name)
        return self.base_request.request('/application/{0}/restart'.format(app['id']), 'POST', endpoint=self.settings.get('pine_endpoint'))

    def get_api_key(self, name):
        app = self.get(name)
        return self.base_request.request('/application/{0}/generate-api-key'.format(app['id']), 'POST', endpoint=self.settings.get('pine_endpoint'))

