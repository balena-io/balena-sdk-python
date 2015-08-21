import json

from ..base_request import BaseRequest
from ..settings import Settings
from ..token import Token
from .. import exceptions

class Key(object):

	def __init__(self):
		self.base_request = BaseRequest()
		self.settings = Settings()
		self.token = Token()

	def get_all(self):
		return self.base_request.request('user__has__public_key', 'GET', endpoint=self.settings.get('pine_endpoint'))['d']

	def get(self, id):
		params = {
			'filter': 'id',
			'eq': id
		}
		key = self.base_request.request('user__has__public_key', 'GET', params=params, endpoint=self.settings.get('pine_endpoint'))['d']
		if key:
			return key
		else:
			raise exceptions.KeyNotFound(id)

	def remove(self, id):
		params = {
			'filter': 'id',
			'eq': id
		}
		return self.base_request.request('user__has__public_key', 'DELETE', params=params, endpoint=self.settings.get('pine_endpoint'))

	def create(self, title, key):
		# Trim ugly whitespaces
		key = key.strip()

		data = {
			'title': title,
			'public_key': key,
			'user': self.token.get_user_id()
		}
		key = self.base_request.request('user__has__public_key', 'POST', data=data, endpoint=self.settings.get('pine_endpoint'))
		return json.loads(key)['id']
