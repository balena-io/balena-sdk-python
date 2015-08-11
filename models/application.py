from ..base_request import BaseRequest
from ..resources import Message
from .device import Device
from ..settings import Settings

class Application(object):

    def __init__(self):
        self.base_request = BaseRequest()
        self.device = Device()
        self.settings = Settings()

    def get_all(self):
        return self.base_request.request('application', 'GET', endpoint=self.settings.get('pine_endpoint'))['d'][0]

    def get(self, name):
        params = {
            'filter': 'app_name',
            'eq': name
        }
        app = self.base_request.request('application', 'GET', params=params, endpoint=self.settings.get('pine_endpoint'))['d'][0]
        if app:
            return app
        else:
            print(Message.NO_APPLICATION_FOUND.format(value=name, app_att="name"))

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
        app = self.base_request.request('application', 'GET', params=params, endpoint=self.settings.get('pine_endpoint'))['d'][0]
        if app:
            return app
        else:
            # found no application
            print(Message.NO_APPLICATION_FOUND.format(value=app_id, app_att="id"))

    def create(self, name, device_type):
        device_slug = self.device.get_device_slug(device_type)
        if device_slug:
            data = {
                'app_name': name,
                'device_type': device_slug
            }
            return self.base_request.request('application', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))

    def remove(self, name):
        params = {
            'filter': 'app_name',
            'eq': name
        }
        return self.base_request.request('application', 'DELETE', params=params, endpoint=self.settings.get('pine_endpoint'))            

    def restart(self, name):
        app = self.get(name)
        if app:
            return self.base_request.request('/application/{0}/restart'.format(app[0]['id']), 'POST', endpoint=self.settings.get('pine_endpoint'))

    def get_api_key(self, name):
        app = self.get(name)
        if app:
            return self.base_request.request('/application/{0}/generate-api-key'.format(app[0]['id']), 'POST', endpoint=self.settings.get('pine_endpoint'))

