from helpers import _get_resource, _post_resource


class Device(object):

    """Device Object"""

    def __init__(self, Connection, uuid=None, name=None):
        self.connection = Connection
        self.uuid = uuid
        self.name = name
        self.get()

    def get(self):
        '''
        @params device uuid or name
        returns device object
        '''
        if self.uuid != None:
        	data = {
	            'connection': self.connection,
	            'path': "device",
	            'filter': "uuid",
	            'eq': self.uuid
	        }

        elif self.name:
            data = {
	            'connection': self.connection,
	            'path': "device",
	            'filter': "name",
	            'eq': self.name
	        }

	    
	    device = _get_resource(data)[0]
        self.uuid = device['uuid']
        self.id = device['id']
        return device

    def get_name(self):
        '''
        @params device uuid
        returns device name
        '''
        return self.get()['name']

    def is_online(self):
        '''
        @params device uuid
        returns device connection status
        '''
        return self.get()['is_online']

    def envar_create(self, key, value):
        data = {
            'connection': self.connection,
            'path': "device_environment_variable",
            'body': {
                    'device': self.id,
                    'env_var_name': key,
                'value': value
            }
        }

        return _post_resource(data)
