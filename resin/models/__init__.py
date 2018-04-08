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
from .image import Image
from .service import Service
from .release import Release
from .config_variable import ConfigVariable
from .api_key import ApiKey


class Models(object):

    def __init__(self):
        self.device = Device()
        self.application = Application()
        self.config = Config()
        self.environment_variables = EnvironmentVariable()
        self.key = Key()
        self.device_os = DeviceOs()
        self.supervisor = Supervisor()
        self.image = Image()
        self.service = Service()
        self.release = Release()
        self.config_variable = ConfigVariable()
        self.api_key = ApiKey()
