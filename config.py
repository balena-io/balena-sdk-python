import sys

from .baseapi import BaseAPI
from .resources import Message

class Config(BaseAPI):

	def get_all(self):
		return self.request('/config', 'GET')

	def get_pubnub_keys(self):
		return self.request('/config', 'GET')['pubnub']

	def get_device_type(self):
		return self.request('/config', 'GET')['deviceTypes']
