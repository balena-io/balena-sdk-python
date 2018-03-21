"""
Welcome to the Resin Python SDK documentation.
This document aims to describe all the functions supported by the SDK, as well as
showing examples of their expected usage.
If you feel something is missing, not clear or could be improved, please don't
hesitate to open an issue in GitHub, we'll be happy to help.
"""

from .base_request import BaseRequest
from .auth import Auth
from .token import Token
from .logs import Logs
from .settings import Settings
from .models import Models
from .twofactor_auth import TwoFactorAuth


__version__ = '3.0.0'


class Resin(object):
    """
    This class implements all functions supported by the Python SDK.
    Attributes:
            settings (Settings): configuration settings for Resin Python SDK.
            logs (Logs): logs from devices working on Resin.
            auth (Auth): authentication handling.
            models (Models): all models in Resin Python SDK.

    """

    def __init__(self):
        self.settings = Settings()
        self.logs = Logs()
        self.auth = Auth()
        self.models = Models()
        self.twofactor_auth = TwoFactorAuth()
