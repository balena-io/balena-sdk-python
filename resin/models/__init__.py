"""
This module implements all models for Resin Python SDK.

"""

from .device import Device
from .application import Application
from .config import Config
from .environment_variables import EnvironmentVariable
from .key import Key
from .device_os import DeviceOs
from .supervisor import Supervisor


class Models(object):

    def __init__(self):
        self.device = Device()
        self.application = Application()
        self.config = Config()
        self.environment_variables = EnvironmentVariable()
        self.key = Key()
        self.device_os = DeviceOs()
        self.supervisor = Supervisor()
