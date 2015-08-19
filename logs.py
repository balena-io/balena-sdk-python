from pubnub import Pubnub

from .base_request import BaseRequest
from .models.config import Config

class Logs(object):
	def __init__(self):
		self.config = Config()

	def init_pubnub(func):
		def wrapper(self, *args, **kwargs):
			if not hasattr(self, 'pubnub'):
				pubnub_key = self.config.get_pubnub_keys()
				self.pubnub = Pubnub(publish_key=pubnub_key['publish_key'], subscribe_key=pubnub_key['subscribe_key'])
			return func(self, *args, **kwargs)
		return wrapper

	@init_pubnub
	def subscribe(self, uuid, callback, error):
		channel = self.get_channel(uuid)
		self.pubnub.subscribe(channels=channel, callback=callback, error=error)

	@init_pubnub
	def history(self, uuid, callback, error):
		channel = self.get_channel(uuid)
		self.pubnub.history(channel=channel, callback=callback, error=error)

	def unsubscribe(self, uuid):
		if hasattr(self, 'pubnub'):
			channel = self.get_channel(uuid)
			self.pubnub.unsubscribe(channel=channel)

	@staticmethod
	def get_channel(uuid):
		return 'device-{uuid}-logs'.format(uuid=uuid)

	
