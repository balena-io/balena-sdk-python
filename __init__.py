import requests, json
import resin

from .device import Device
from .application import Application

class Client(object):

    def __init__(self, token=None):
        # Probably and example of bad design
        self.application = Application(token)
        self.device = Device(token)
		


