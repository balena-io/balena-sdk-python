from .device import Device
from .application import Application
from .config import Config
from .environment_variables import EnvironmentVariable
from .key import Key
from .device_os import DeviceOs

class Models(object):

	def __init__(self):
		self.device = Device()
		self.application = Application()
		self.config = Config()
		self.environment_variables = EnvironmentVariable()
		self.key = Key()
		self.device_os = DeviceOs()
