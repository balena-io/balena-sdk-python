from helpers import _get_resource

class Devices(object):

	def __init__(self, Connection, app_id=None):
	    self.connection = Connection
	    self.app_id = app_id

	def get(self):
		data = {
	            'connection': self.connection,
	            'path': "device",
	            'filter': "application",
	            'eq': self.app_id
	        }
		return _get_resource(data)
