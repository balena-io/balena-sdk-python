from .baseapi import BaseAPI

class Device(BaseAPI):

    """Device Object"""

    def get(self, uuid):
        '''
        @params device uuid or name
        returns device object
        '''
        params = {
        	'filter': 'uuid',
        	'eq': uuid
        }
        return self.request('device', 'GET', params=params)[0]

    def get_all(self):
    	return self.request('device', 'GET')

    def get_all_by_application(self, name):
    	#notworkingyet
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
        return self.request('device', 'GET', params=params)[0]

    def identify(self, uuid):
    	data = {
    		'uuid': uuid
    	}
        return self.request('/blink', 'POST', data=data)

    def get_name(self, uuid):
    	return self.get(uuid)['name']

    def is_online(self, uuid):
    	return self.get(uuid)['is_online']