from .baseapi import BaseAPI
from .resources import Message


class Key(BaseAPI):

	def get_all(self):
		return self.request('user__has__public_key', 'GET')['d']

	def get(self, id):
		params = {
			'filter': 'id',
			'eq': id
		}
		key = self.request('user__has__public_key', 'GET', params=params)['d']
		if key:
			return key
		else:
			print(Message.NO_KEY_FOUND.format(value=id,key_att="id"))

	def remove(self, id):
		params = {
			'filter': 'id',
			'eq': id
		}
		return self.request('user__has__public_key', 'DELETE', params=params)

	# TODO: not working yet
	def create(self, title, key):
		# Trim ugly whitespaces
		key = key.strip()
		print key
		data = {
			'title': title,
			'key': key
		}
		key = self.request('user__has__public_key', 'POST', data=data)
		return key
