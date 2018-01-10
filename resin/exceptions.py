# coding: utf-8
from .resources import Message


class ResinException(Exception):
    """
    Exception base class for Python SDK.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.

    """

    def __init__(self):
        self.code = self.__class__.__name__
        self.exit_code = 1


class MissingOption(ResinException):
    """
    Exception type for missing option in settings or auth token.

    Args:
        option (str): option name.

    Attributes:
        message (str): error message.

    """

    def __init__(self, option):
        super(MissingOption, self).__init__()
        self.message = Message.MISSING_OPTION.format(option=option)


class InvalidOption(ResinException):
    """
    Exception type for invalid option in settings or auth token.

    Args:
        option (str): option name.

    Attributes:
        message (str): error message.

    """

    def __init__(self, option):
        super(InvalidOption, self).__init__()
        self.message = Message.INVALID_OPTION.format(option=option)


class NonAllowedOption(ResinException):
    """
    Exception type for non allowed option in parameters for downloading device OS.

    Args:
        option (str): option name.

    Attributes:
        message (str): error message.

    """

    def __init__(self, option):
        super(NonAllowedOption, self).__init__()
        self.message = Message.NON_ALLOWED_OPTION.format(option=option)


class InvalidDeviceType(ResinException):
    """
    Exception type for invalid device type.

    Args:
        dev_type (str): device type.

    Attributes:
        message (str): error message.

    """

    def __init__(self, dev_type):
        super(InvalidDeviceType, self).__init__()
        self.message = Message.INVALID_DEVICE_TYPE.format(dev_type=dev_type)


class MalformedToken(ResinException):
    """
    Exception type for malformed token.

    Args:
        token (str): token.

    Attributes:
        message (str): error message.

    """

    def __init__(self, token):
        super(MalformedToken, self).__init__()
        self.message = Message.MALFORMED_TOKEN.format(token=token)


class ApplicationNotFound(ResinException):
    """
    Exception type for application not found.

    Args:
        application (str): application detail (application name or id).

    Attributes:
        message (str): error message.

    """

    def __init__(self, application):
        super(ApplicationNotFound, self).__init__()
        self.message = Message.APPLICATION_NOT_FOUND.format(
            application=application)


class DeviceNotFound(ResinException):
    """
    Exception type for device not found.

    Args:
        device (str): device detail (device uuid or device name).

    Attributes:
        message (str): error message.

    """

    def __init__(self, uuid):
        super(DeviceNotFound, self).__init__()
        self.message = Message.DEVICE_NOT_FOUND.format(uuid=uuid)


class KeyNotFound(ResinException):
    """
    Exception type for ssh key not found.

    Args:
        key (str): ssh key id.

    Attributes:
        message (str): error message.

    """

    def __init__(self, key):
        super(KeyNotFound, self).__init__()
        self.message = Message.KEY_NOT_FOUND.format(key=key)


class RequestError(ResinException):
    """
    Exception type for request error.

    Args:
        body (str): response body.

    Attributes:
        message (str): error message.

    """

    def __init__(self, body):
        super(RequestError, self).__init__()
        self.message = Message.REQUEST_ERROR.format(body=body)


class NotLoggedIn(ResinException):
    """
    Exception when no user logged in.

    Attributes:
        message (str): error message.

    """

    def __init__(self):
        super(NotLoggedIn, self).__init__()
        self.message = Message.NOT_LOGGED_IN


class Unauthorized(ResinException):
    """
    Exception when no user logged in and no Resin API Key provided.

    Attributes:
        message (str): error message.

    """

    def __init__(self):
        super(Unauthorized, self).__init__()
        self.message = Message.UNAUTHORIZED


class LoginFailed(ResinException):
    """
    Exception when login unsuccessful.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.
        message (str): error message.

    """

    def __init__(self):
        super(LoginFailed, self).__init__()
        self.message = Message.LOGIN_FAILED


class DeviceOffline(ResinException):
    """
    Exception when a device is offline.

    Args:
        uuid (str): device uuid.

    Attributes:
        message (str): error message.

    """

    def __init__(self, uuid):
        super(DeviceOffline, self).__init__()
        self.message = Message.DEVICE_OFFLINE.format(uuid=uuid)


class DeviceNotWebAccessible(ResinException):
    """
    Exception when a device is not web accessible.

    Args:
        uuid (str): device uuid.

    Attributes:
        message (str): error message.

    """

    def __init__(self, uuid):
        super(DeviceNotWebAccessible, self).__init__()
        self.message = Message.DEVICE_NOT_WEB_ACCESSIBLE.format(uuid=uuid)


class IncompatibleApplication(ResinException):
    """
    Exception when moving a device to an application with different device-type.

    Args:
        application (str): application name.

    Attributes:
        message (str): error message.

    """

    def __init__(self, application):
        super(IncompatibleApplication, self).__init__()
        self.message = Message.INCOMPATIBLE_APPLICATION.format(application=application)


class UnsupportedFunction(ResinException):
    """
    Exception when invoking an unsupported function in a specific supervisor version.

    Args:
        required_version (str): required supervisor version.
        current_version (str): current supervisor version.

    Attributes:
        message (str): error message.

    """

    def __init__(self, required_version, current_version):
        super(UnsupportedFunction, self).__init__()
        self.message = Message.SUPERVISOR_VERSION_ERROR.format(req_version=required_version, cur_version=current_version)


class AmbiguousApplication(ResinException):
    """
    Args:
        application (str): application name.

    Attributes:
        message (str): error message.

    """

    def __init__(self, application):
        super(AmbiguousApplication, self).__init__()
        self.message = Message.AMBIGUOUS_APPLICATION.format(application=application)


class AmbiguousDevice(ResinException):
    """
    Args:
        uuid (str): device uuid.

    Attributes:
        message (str): error message.

    """

    def __init__(self, uuid):
        super(AmbiguousDevice, self).__init__()
        self.message = Message.AMBIGUOUS_DEVICE.format(uuid=uuid)


class BuildNotFound(ResinException):
    """
    Args:
        build_id (str): build id.

    Attributes:
        message (str): error message.

    """

    def __init__(self, build_id):
        super(BuildNotFound, self).__init__()
        self.message = Message.BUILD_NOT_FOUND.format(id=build_id)


class FailedBuild(ResinException):
    """
    Args:
        build_id (str): build id.

    Attributes:
        message (str): error message.

    """

    def __init__(self, build_id):
        super(FailedBuild, self).__init__()
        self.message = Message.FAILED_BUILD.format(id=build_id)


class InvalidParameter(ResinException):
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
        super(InvalidParameter, self).__init__()
        self.message = Message.INVALID_PARAMETER.format(parameter=parameter, value=value)
