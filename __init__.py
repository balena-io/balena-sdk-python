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

	def device(self):
		""" Gets device resource
		@parameter uuid: uuid of requested device.
		returns device object
		"""
		return resin.Device(self)
		
from resin.device import *  # noqa
