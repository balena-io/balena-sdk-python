"""
This module implements all models for balena python SDK.

"""

from .api_key import ApiKey
from .application import Application
from .config import Config
from .config_variable import ConfigVariable
from .device import Device
from .device_os import DeviceOs
from .device_type import DeviceType
from .environment_variables import EnvironmentVariable
from .history import History
from .image import Image
from .key import Key
from .organization import Organization
from .release import Release
from .service import Service
from .supervisor import Supervisor
from .tag import Tag


class Models:
    def __init__(self):
        self.device = Device()
        self.application = Application()
        self.config = Config()
        self.environment_variables = EnvironmentVariable()
        self.key = Key()
        self.device_os = DeviceOs()
        self.device_type = DeviceType()
        self.supervisor = Supervisor()
        self.image = Image()
        self.service = Service()
        self.release = Release()
        self.config_variable = ConfigVariable()
        self.api_key = ApiKey()
        self.tag = Tag()
        self.organization = Organization()
        self.history = History()
