import jwt
from datetime import datetime

from .settings import Settings

TOKEN_KEY = 'token'

class Token(object):

	def __init__(self):
		self.settings = Settings()

	def __parse_token(self, token):
		try:
			return jwt.decode(token, verify=False)
		except jwt.InvalidTokenError:
			# TODO: need exception type for invalid token
			pass

	def is_valid_token(self, token):
		try:
			self.__parse_token(token)
			return True
		except:
			return False

	def set(self, token):
		if self.is_valid_token(token):
			self.settings.set(TOKEN_KEY, token)

	def get(self):
		return self.settings.get(TOKEN_KEY)

	def has(self):
		return self.settings.has(TOKEN_KEY)

	def remove(self):
		return self.settings.remove(TOKEN_KEY)

	def get_data(self):
		if self.has():
			return self.__parse_token(self.settings.get(TOKEN_KEY))
		else:
			# TODO: raise exception when token doesn't exist
			pass

	def get_property(self, element):
		token_data = self.get_data()
		if element in token_data:
			return token_data[element]
		else:
			# TODO: raise exception when property doesn't exist
			pass

	def get_username(self):
		return self.get_property('username')

	def get_user_id(self):
		return self.get_property('id')

	def get_email(self):
		return self.get_property('email')

	def get_age(self):
		# dt will be the same as Date.now() in Javascript but converted to milliseconds for consistency with js/sc sdk
		dt = ((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds()) * 1000

		# iat stands for "issued at"
		return dt - (int(self.get_property('iat')) * 1000)

