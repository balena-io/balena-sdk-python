from .base_request import BaseRequest
from .resources import Message
from .token  import Token
from .settings import Settings

class Auth(object):

	def __init__(self):
		self.base_request = BaseRequest()
		self.settings = Settings()
		self.token = Token()

	def login(self, **credentials):
		try:
			self.token.set(self.authenticate(**credentials))
		except:
			# TODO: need exception type
			raise

	def login_with_token(self, token):
		if self.token.is_valid_token(token):
			self.token.set(token)
		else:
			# TODO: need exception type for invalid token
			raise

	def who_am_i(self):
		return self.token.get_username()

	def authenticate(self, **credentials):
		return self.base_request.request('login_', 'POST', data=credentials, endpoint=self.settings.get('api_endpoint'), auth=False)

	def is_logged_in(self):
		return self.token.has()

	def get_token(self):
		return self.toket.get()

	def get_user_id(self):
		return self.token.get_user_id()

	def get_email(self):
		return self.token.get_email()

	def log_out(self):
		return self.token.remove()

	def register(self, **credentials):
		return self.base_request.request('user/register', 'POST', data=credentials, endpoint=self.settings.get('api_endpoint'))
