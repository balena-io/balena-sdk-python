"""
This module implements all models for balena python SDK.

"""

from .api_key import ApiKey
from .application import Application
from .billing import Billing
from .credit_bundle import CreditBundle
from .config import Config
from .device import Device
from .device_type import DeviceType
from .image import Image
from .key import Key
from .organization import Organization
from .os import DeviceOs
from .release import Release
from .service import Service


class Models:
    def __init__(self):
        self.application = Application()
        self.billing = Billing()
        self.credit_bundle = CreditBundle()
        self.device = Device()
        self.device_type = DeviceType()
        self.api_key = ApiKey()
        self.key = Key()
        self.organization = Organization()
        self.os = DeviceOs()
        self.config = Config()
        self.release = Release()
        self.service = Service()
        self.image = Image()
