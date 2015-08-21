# coding: utf-8
from .resources import Message

class MissingOption(Exception):
	def __init__(self, option):
		self.code = 'MissingOption'
		self.exit_code = 1
		self.message = Message.MISSING_OPTION.format(option=option)

class InvalidOption(Exception):
	def __init__(self, option):
		self.code = 'InvalidOption'
		self.exit_code = 1
		self.message = Message.INVALID_OPTION.format(option=option)

class NonAllowedOption(Exception):
	def __init__(self, option):
		self.code = 'NonAllowedOption'
		self.exit_code = 1
		self.message = Message.NON_ALLOWED_OPTION(option=option)

class InvalidDeviceType(Exception):
	def __init__(self, dev_type):
		self.code = 'InvalidDeviceType'
		self.exit_code = 1
		self.message = Message.INVALID_DEVICE_TYPE.format(dev_type=dev_type)

class MalformedToken(Exception):
	def __init__(self, token):
		self.code = 'MalformedToken'
		self.exit_code = 1
		self.message = Message.MALFORMED_TOKEN.format(token=token)

class ApplicationNotFound(Exception):
	def __init__(self, application):
		self.code = 'ApplicationNotFound'
		self.exit_code = 1
		self.message = Message.APPLICATION_NOT_FOUND.format(application=application)

class DeviceNotFound(Exception):
	def __init__(self):
		self.code = 'DeviceNotFound'
		self.exit_code = 1
		self.message = Message.DEVICE_NOT_FOUND.format(device=device)

class KeyNotFound(Exception):
	def __init__(self, key):
		self.code = 'KeyNotFound'
		self.exit_code = 1
		self.message = Message.KEY_NOT_FOUND.format(key=key)

class RequestError(Exception):
	def __init__(self, body):
		self.code = 'RequestError'
		self.exit_code = 1
		self.message = Message.REQUEST_ERROR.format(body=body)

class NotLoggedIn(Exception):
	def __init__(self):
		self.code = 'NotLoggedIn'
		self.exit_code = 1
		self.message = Message.NOT_LOGGED_IN

class LoginFailed(Exception):
	def __init__(self):
		self.code = 'LoginFailed'
		self.exit_code = 1
		self.message = Message.LOGIN_FAILED

class DeviceOffline(Exception):
	def __init__(self, uuid):
		self.code = 'DeviceOffline'
		self.exit_code = 1
		self.message = Message.DEVICE_OFFLINE.format(uuid=uuid)
