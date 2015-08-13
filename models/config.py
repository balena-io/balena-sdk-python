import sys

from ..base_request import BaseRequest
from ..resources import Message
from ..settings import Settings

class Config(object):

	def __init__(self):
		self.base_request = BaseRequest()
		self.settings = Settings()

	def get_all(self):
		return self.base_request.request('/config', 'GET', endpoint=self.settings.get('pine_endpoint'))

	def get_pubnub_keys(self):
		return self.base_request.request('/config', 'GET', endpoint=self.settings.get('pine_endpoint'))['pubnub']

	def get_device_type(self):
		return self.base_request.request('/config', 'GET', endpoint=self.settings.get('pine_endpoint'))['deviceTypes']
