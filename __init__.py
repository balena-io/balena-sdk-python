import requests, json
import resin

class Connection(object):

	"""
	This is a python library for accessing the resin api
	http://github.com/craig-mulligan/resin-api-python
	Usage:
	    import resin_io
	    c = resin_io.Connection('{{JWT}}')
	"""

	def __init__(self, JWT):
	    self.base_url = 'https://api.resin.io/ewa'
	    self.headers = {'Content-type': 'application/json',
               'Authorization': 'Bearer ' + JWT}

	def device(self, uuid=None, name=None):
		""" 
		intiates device class
		"""
		return resin.Device(self, uuid=uuid, name=name)

	def devices(self, app_id=None):
		""" 
		intiates device class
		"""
		return resin.Devices(self, app_id=app_id)
		
from resin.device import *  # noqa
from resin.devices import *  # noqa