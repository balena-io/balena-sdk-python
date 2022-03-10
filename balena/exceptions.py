# coding: utf-8
from .resources import Message


class BalenaException(Exception):
    """
    Exception base class for python SDK.

    Attributes:
        code (str): exception code.
        exit_code (int): program exit code.

    """

    def __init__(self):
        self.code = self.__class__.__name__
        self.exit_code = 1


class MissingOption(BalenaException):
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


class InvalidOption(BalenaException):
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


class NonAllowedOption(BalenaException):
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


class InvalidDeviceType(BalenaException):
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


class MalformedToken(BalenaException):
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


class ApplicationNotFound(BalenaException):
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


class DeviceNotFound(BalenaException):
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


class KeyNotFound(BalenaException):
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


class RequestError(BalenaException):
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


class NotLoggedIn(BalenaException):
    """
    Exception when no user logged in.

    Attributes:
        message (str): error message.

    """

    def __init__(self):
        super(NotLoggedIn, self).__init__()
        self.message = Message.NOT_LOGGED_IN


class Unauthorized(BalenaException):
    """
    Exception when no user logged in and no Balena API Key provided.

    Attributes:
        message (str): error message.

    """

    def __init__(self):
        super(Unauthorized, self).__init__()
        self.message = Message.UNAUTHORIZED


class LoginFailed(BalenaException):
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


class DeviceOffline(BalenaException):
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


class DeviceNotWebAccessible(BalenaException):
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


class IncompatibleApplication(BalenaException):
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


class UnsupportedFunction(BalenaException):
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


class AmbiguousApplication(BalenaException):
    """
    Args:
        application (str): application name.

    Attributes:
        message (str): error message.

    """

    def __init__(self, application):
        super(AmbiguousApplication, self).__init__()
        self.message = Message.AMBIGUOUS_APPLICATION.format(application=application)


class AmbiguousDevice(BalenaException):
    """
    Args:
        uuid (str): device uuid.

    Attributes:
        message (str): error message.

    """

    def __init__(self, uuid):
        super(AmbiguousDevice, self).__init__()
        self.message = Message.AMBIGUOUS_DEVICE.format(uuid=uuid)


class InvalidParameter(BalenaException):
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


class ImageNotFound(BalenaException):
    """
    Args:
        image_id (str): image id.

    Attributes:
        message (str): error message.

    """

    def __init__(self, image_id):
        super(ImageNotFound, self).__init__()
        self.message = Message.IMAGE_NOT_FOUND.format(id=image_id)


class ReleaseNotFound(BalenaException):
    """
    Args:
        release_id (str): release id.

    Attributes:
        message (str): error message.

    """

    def __init__(self, release_id):
        super(ReleaseNotFound, self).__init__()
        self.message = Message.RELEASE_NOT_FOUND.format(id=release_id)


class AmbiguousRelease(BalenaException):
    """
    Args:
        commit (str): release commit.

    Attributes:
        message (str): error message.

    """

    def __init__(self, commit):
        super(AmbiguousRelease, self).__init__()
        self.message = Message.AMBIGUOUS_RELEASE.format(commit=commit)


class ServiceNotFound(BalenaException):
    """
    Args:
        service_id (str): service id.

    Attributes:
        message (str): error message.

    """

    def __init__(self, service_id):
        super(ServiceNotFound, self).__init__()
        self.message = Message.SERVICE_NOT_FOUND.format(id=service_id)


class InvalidApplicationType(BalenaException):
    """
    Args:
        app_type (str): application type.

    Attributes:
        message (str): error message.

    """

    def __init__(self, app_type):
        super(InvalidApplicationType, self).__init__()
        self.message = Message.INVALID_APPLICATION_TYPE.format(app_type=app_type)


class UnsupportedFeature(BalenaException):
    """
    Attributes:
        message (str): error message.

    """

    def __init__(self):
        super(UnsupportedFeature, self).__init__()
        self.message = Message.UNSUPPORTED_FEATURE


class OsUpdateError(BalenaException):
    """

    Args:
        message (str): message.

    Attributes:
        message (str): error message.

    """

    def __init__(self, message):
        super(OsUpdateError, self).__init__()
        self.message = Message.OS_UPDATE_ERROR.format(message=message)


class BuilderRequestError(BalenaException):
    """
    Args:
        message (str): message.

    Attributes:
        message (str): error message.
    """

    def __init__(self, message):
        super(BuilderRequestError, self).__init__()
        self.message = message


class LocalModeError(BalenaException):
    """
    Generic Local Mode Exception.

    Args:
        message (str): message.

    Attributes:
        message (str): error message.

    """

    def __init__(self, message):
        super(LocalModeError, self).__init__()
        self.message = message


class OrganizationNotFound(BalenaException):
    """
    Exception type for organization not found.

    Args:
        organization (str): organization detail (organization handle or id).

    Attributes:
        message (str): error message.

    """

    def __init__(self, organization):
        super(OrganizationNotFound, self).__init__()
        self.message = Message.ORGANIZATION_NOT_FOUND.format(
            organization=organization)


class OrganizationMembershipNotFound(BalenaException):
    """
    Exception type for organization membership not found.

    Args:
        org_membership (str): organization membership id.

    Attributes:
        message (str): error message.

    """

    def __init__(self, org_membership):
        super(OrganizationMembershipNotFound, self).__init__()
        self.message = Message.ORGANIZATION_MEMBERSHIP_NOT_FOUND.format(
            org_membership=org_membership)


class BalenaDiscontinuedDeviceType(BalenaException):
    """
    The device type that you specified is invalid because it is discontinued, and this operation is no longer supported.

    Args:
        type (str): device type.

    Attributes:
        message (str): error message.

    """

    def __init__(self, type):
        super(BalenaDiscontinuedDeviceType, self).__init__()
        self.message = Message.BALENA_DISCONTINUE_DEVICE_TYPE.format(type=type)


class BalenaOrganizationMembershipRoleNotFound(BalenaException):
    """
    Balena organization membership role not found.
    Args:
        role_name (str): role name.
    Attributes:
        message (str): error message.
    """

    def __init__(self, role_name):
        super(BalenaOrganizationMembershipRoleNotFound, self).__init__()
        self.message = Message.BALENA_ORG_MEMBERSHIP_ROLE_NOT_FOUND.format(role_name=role_name)


class BalenaApplicationMembershipRoleNotFound(BalenaException):
    """
    Balena application membership role not found.

    Args:
        role_name (str): role name.

    Attributes:
        message (str): error message.

    """

    def __init__(self, role_name):
        super(BalenaApplicationMembershipRoleNotFound, self).__init__()
        self.message = Message.BALENA_APP_MEMBERSHIP_ROLE_NOT_FOUND.format(role_name=role_name)


class ApplicationMembershipNotFound(BalenaException):
    """
    Exception type for application membership not found.

    Args:
        membership (str): application membership id.

    Attributes:
        message (str): error message.

    """

    def __init__(self, membership):
        super(ApplicationMembershipNotFound, self).__init__()
        self.message = Message.APPLICATION_MEMBERSHIP_NOT_FOUND.format(
            membership=membership)


class BalenaInvalidDeviceType(BalenaException):
    """
    Exception type for invalid device type.

    Args:
        device_type (str): device type.

    Attributes:
        message (str): error message.

    """

    def __init__(self, device_type):
        super(BalenaInvalidDeviceType, self).__init__()
        self.message = Message.BALENA_INVALID_DEVICE_TYPE.format(
            device_type=device_type)
