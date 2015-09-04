"""
This is a python library for resources like message templates etc.
"""


class Message(object):
    """
    Message templates
    """

    # Exception Error Message
    NOT_LOGGED_IN = "You have to log in"
    REQUEST_ERROR = "Request error: {body}"
    KEY_NOT_FOUND = "Key not found: {key}"
    DEVICE_NOT_FOUND = "Device not found: {device}"
    APPLICATION_NOT_FOUND = "Application not found: {application}"
    MALFORMED_TOKEN = "Malformed token: {token}"
    INVALID_DEVICE_TYPE = "Invalid device type: {dev_type}"
    INVALID_OPTION = "Invalid option: {option}"
    MISSING_OPTION = "Missing option: {option}"
    NON_ALLOWED_OPTION = "Non allowed option: {option}"
    LOGIN_FAILED = "Invalid credentials"
    DEVICE_OFFLINE = "Device is offline: {uuid}"
