from .device import Device
from .application import Application
from .config import Config
from .environment_variables import EnvironmentVariable
from .key import Key
from .os import Os

class Models(object):

	def __init__(self):
		self.device = Device()
		self.application = Application()
		self.config = Config()
		self.environment_variables = EnvironmentVariable()
		self.key = Key()
		self.os = Os()