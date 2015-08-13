from .base_request import BaseRequest
from .auth import Auth
from .token import Token
#from .logs import Logs
from .settings import Settings
from .models import Models


class Client(object):

	def __init__(self):
		self.settings = Settings()
		#self.logs = Logs()
		self.auth = Auth()
		self.models = Models()

