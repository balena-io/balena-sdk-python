import requests, json
import resin

from .device import Device
from .application import Application
from .environment_variables import Environment_Variables

class Client(object):

    def __init__(self, token=None):
        # Probably and example of bad design
        self.application = Application(token)
        self.device = Device(token)
        self.environment_variables = Environment_Variables(token)


