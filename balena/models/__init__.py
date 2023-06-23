"""
This module implements all models for balena python SDK.

"""

from ..pine import PineClient
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
from ..settings import Settings


class Models:
    def __init__(self, pine: PineClient, settings: Settings):
        self.application = Application(pine, settings)
        self.billing = Billing(pine, settings)
        self.credit_bundle = CreditBundle(pine, settings)
        self.device = Device(pine, settings)
        self.device_type = DeviceType(pine, settings)
        self.api_key = ApiKey(pine, settings)
        self.key = Key(pine, settings)
        self.organization = Organization(pine, settings)
        self.os = DeviceOs(pine, settings)
        self.config = Config(settings)
        self.release = Release(pine, settings)
        self.service = Service(pine, settings)
        self.image = Image(pine, settings)
