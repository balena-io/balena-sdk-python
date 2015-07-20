import sys

from .baseapi import BaseAPI
from .resources import Message

class Device(BaseAPI):

    def get(self, uuid):
        params = {
            'filter': 'uuid',
            'eq': uuid
        }
        try:
            return self.request('device', 'GET', params=params)[0]
        except IndexError:
            # found no device
            print(Message.NO_DEVICE_FOUND.format(value=uuid,dev_att="uuid"))
        except:
            # unexpected exception
            raise

    def get_all(self):
        return self.request('device', 'GET')

    def get_all_by_application(self, name):
        # notworkingyet
        params = {
            'expand': 'application',
            'eq': name,
            'filter': "app_name"
        }
        return self.request('device', 'GET', params=params)

    def get_by_name(self, name):
        params = {
            'filter': 'name',
            'eq': name
        }
        return self.request('device', 'GET', params=params)

    def identify(self, uuid):
        data = {
            'uuid': uuid
        }
        return self.request('/blink', 'POST', data=data)

    def get_name(self, uuid):
        return self.get(uuid)['name']

    def is_online(self, uuid):
        return self.get(uuid)['is_online']
