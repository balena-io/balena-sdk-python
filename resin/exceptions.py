# coding: utf-8
from .resources import Message


class MissingOption(Exception):
    """
    Exception type for missing option in settings or auth token.

    Args:
        option (str): option name.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, option):
        self.code = 'MissingOption'
        self.exit_code = 1
        self.message = Message.MISSING_OPTION.format(option=option)


class InvalidOption(Exception):
    """
    Exception type for invalid option in settings or auth token.

    Args:
        option (str): option name.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, option):
        self.code = 'InvalidOption'
        self.exit_code = 1
        self.message = Message.INVALID_OPTION.format(option=option)


class NonAllowedOption(Exception):
    """
    Exception type for non allowed option in parameters for downloading device OS.

    Args:
        option (str): option name.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, option):
        self.code = 'NonAllowedOption'
        self.exit_code = 1
        self.message = Message.NON_ALLOWED_OPTION(option=option)


class InvalidDeviceType(Exception):
    """
    Exception type for invalid device type.

    Args:
        dev_type (str): device type.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, dev_type):
        self.code = 'InvalidDeviceType'
        self.exit_code = 1
        self.message = Message.INVALID_DEVICE_TYPE.format(dev_type=dev_type)


class MalformedToken(Exception):
    """
    Exception type for malformed token.

    Args:
        token (str): token.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, token):
        self.code = 'MalformedToken'
        self.exit_code = 1
        self.message = Message.MALFORMED_TOKEN.format(token=token)


class ApplicationNotFound(Exception):
    """
    Exception type for application not found.

    Args:
        application (str): application detail (application name or id).

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, application):
        self.code = 'ApplicationNotFound'
        self.exit_code = 1
        self.message = Message.APPLICATION_NOT_FOUND.format(
            application=application)


class DeviceNotFound(Exception):
    """
    Exception type for device not found.

    Args:
        device (str): device detail (device uuid or device name).

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self):
        self.code = 'DeviceNotFound'
        self.exit_code = 1
        self.message = Message.DEVICE_NOT_FOUND.format(device=device)


class KeyNotFound(Exception):
    """
    Exception type for ssh key not found.

    Args:
        key (str): ssh key id.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, key):
        self.code = 'KeyNotFound'
        self.exit_code = 1
        self.message = Message.KEY_NOT_FOUND.format(key=key)


class RequestError(Exception):
    """
    Exception type for request error.

    Args:
        body (str): response body.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, body):
        self.code = 'RequestError'
        self.exit_code = 1
        self.message = Message.REQUEST_ERROR.format(body=body)


class NotLoggedIn(Exception):
    """
    Exception when no user logged in.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self):
        self.code = 'NotLoggedIn'
        self.exit_code = 1
        self.message = Message.NOT_LOGGED_IN


class LoginFailed(Exception):
    """
    Exception when login unsuccessful.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self):
        self.code = 'LoginFailed'
        self.exit_code = 1
        self.message = Message.LOGIN_FAILED


class DeviceOffline(Exception):
    """
    Exception when a device is offline.

    Args:
        uuid (str): device uuid.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, uuid):
        self.code = 'DeviceOffline'
        self.exit_code = 1
        self.message = Message.DEVICE_OFFLINE.format(uuid=uuid)
