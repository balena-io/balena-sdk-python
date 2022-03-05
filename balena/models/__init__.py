"""
This module implements all models for balena python SDK.

"""

from .device import Device
from .application import Application
from .config import Config
from .environment_variables import EnvironmentVariable
from .key import Key
from .device_os import DeviceOs
from .device_type import DeviceType
from .supervisor import Supervisor
from .image import Image
from .service import Service
from .release import Release
from .config_variable import ConfigVariable
from .api_key import ApiKey
from .tag import Tag
from .organization import Organization


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
