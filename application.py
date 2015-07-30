from .baseapi import BaseAPI
from .resources import Message
from .device import Device

class Application(BaseAPI):

    def __init__(self, token=None):
        super(Application, self).__init__(token)
        self.token = token
        self.device = Device(self.token)

    def get_all(self):
        return self.request('application', 'GET')['d']

    def get(self, name):
        params = {
            'filter': 'app_name',
            'eq': name
        }
        app = self.request('application', 'GET', params=params)['d']
        if app:
            return app
        else:
            print(Message.NO_APPLICATION_FOUND.format(value=name, app_att="name"))

    def has(self, name):
        params = {
            'filter': 'app_name',
            'eq': name
        }
        app = self.request('application', 'GET', params=params)['d']
        return bool(app)

    def has_any(self):
        apps = self.request('application', 'GET')['d']
        return bool(apps)

    def get_by_id(self, app_id):
        params = {
            'filter': 'id',
            'eq': app_id
        }
        app = self.request('application', 'GET', params=params)['d']
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
            return self.request('application', 'POST', data=data)

    def remove(self, name):
        params = {
            'filter': 'app_name',
            'eq': name
        }
        return self.request('application', 'DELETE', params=params)            

    def restart(self, name):
        app = self.get(name)
        if app:
            return self.request('/application/{0}/restart'.format(app[0]['id']), 'POST')

    def get_api_key(self, name):
        app = self.get(name)
        if app:
            return self.request('/application/{0}/generate-api-key'.format(app[0]['id']), 'POST')

