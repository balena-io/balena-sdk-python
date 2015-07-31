"""
This is a python library for resources like message templates etc.
"""

class Message(object):
	"""
	Message templates
	"""

	NO_DEVICE_FOUND="There is no device with {dev_att}: {value}! Please check the device {dev_att}!"
	NO_APPLICATION_FOUND="There is no application with {app_att}: {value}! Please check the application {app_att}!"
	DEVICE_OFFLINE="The device is offline: {uuid}"
	UNSUPPORTED_DEVICE="Unsupported device: {value}"
	NO_KEY_FOUND="There is no key with {key_att}: {value}! Please check the key {key_att}!"
