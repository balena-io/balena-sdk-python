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
        self.code = self.__class__.__name__
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
        self.code = self.__class__.__name__
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
        self.code = self.__class__.__name__
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
        self.code = self.__class__.__name__
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
        self.code = self.__class__.__name__
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
        self.code = self.__class__.__name__
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

    def __init__(self, uuid):
        self.code = self.__class__.__name__
        self.exit_code = 1
        self.message = Message.DEVICE_NOT_FOUND.format(uuid=uuid)


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
        self.code = self.__class__.__name__
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
        self.code = self.__class__.__name__
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
        self.code = self.__class__.__name__
        self.exit_code = 1
        self.message = Message.NOT_LOGGED_IN


class Unauthorized(Exception):
    """
    Exception when no user logged in and no Resin API Key provided.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self):
        self.code = self.__class__.__name__
        self.exit_code = 1
        self.message = Message.UNAUTHORIZED


class LoginFailed(Exception):
    """
    Exception when login unsuccessful.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self):
        self.code = self.__class__.__name__
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
        self.code = self.__class__.__name__
        self.exit_code = 1
        self.message = Message.DEVICE_OFFLINE.format(uuid=uuid)


class DeviceNotWebAccessible(Exception):
    """
    Exception when a device is not web accessible.

    Args:
        uuid (str): device uuid.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, uuid):
        self.code = self.__class__.__name__
        self.exit_code = 1
        self.message = Message.DEVICE_NOT_WEB_ACCESSIBLE.format(uuid=uuid)


class IncompatibleApplication(Exception):
    """
    Exception when moving a device to an application with different device-type.

    Args:
        application (str): application name.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, application):
        self.code = self.__class__.__name__
        self.exit_code = 1
        self.message = Message.INCOMPATIBLE_APPLICATION.format(application=application)


class UnsupportedFunction(Exception):
    """
    Exception when invoking an unsupported function in a specific supervisor version.

    Args:
        required_version (str): required supervisor version.
        current_version (str): current supervisor version.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, required_version, current_version):
        self.code = self.__class__.__name__
        self.exit_code = 1
        self.message = Message.SUPERVISOR_VERSION_ERROR.format(req_version=required_version, cur_version=current_version)


class AmbiguousApplication(Exception):
    """
    Args:
        application (str): application name.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, application):
        self.code = self.__class__.__name__
        self.exit_code = 1
        self.message = Message.AMBIGUOUS_APPLICATION.format(application=application)


class AmbiguousDevice(Exception):
    """
    Args:
        uuid (str): device uuid.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, uuid):
        self.code = self.__class__.__name__
        self.exit_code = 1
        self.message = Message.AMBIGUOUS_DEVICE.format(uuid=uuid)


class BuildNotFound(Exception):
    """
    Args:
        id (str): build id.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, id):
        self.code = self.__class__.__name__
        self.exit_code = 1
        self.message = Message.BUILD_NOT_FOUND.format(id=id)


class InvalidParameter(Exception):
    """
    Args:
        parameter (str): parameter name.
        value (str): provided value.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self, parameter, value):
        self.code = self.__class__.__name__
        self.exit_code = 1
        self.message = Message.INVALID_PARAMETER.format(parameter=parameter, value=value)
