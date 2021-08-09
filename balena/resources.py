"""
This is a python library for resources like message templates etc.
"""


class Message(object):
    """
    Message templates
    """

    # Exception Error Message
    NOT_LOGGED_IN = "You have to log in!"
    UNAUTHORIZED = "You have to log in or BALENA_API_KEY environment variable must be set!"
    REQUEST_ERROR = "Request error: {body}"
    KEY_NOT_FOUND = "Key not found: {key}"
    DEVICE_NOT_FOUND = "Device not found: {uuid}"
    APPLICATION_NOT_FOUND = "Application not found: {application}"
    FLEET_NOT_FOUND = "Fleet not found: {fleet}"
    MALFORMED_TOKEN = "Malformed token: {token}"
    INVALID_DEVICE_TYPE = "Invalid device type: {dev_type}"
    INVALID_OPTION = "Invalid option: {option}"
    MISSING_OPTION = "Missing option: {option}"
    NON_ALLOWED_OPTION = "Non allowed option: {option}"
    LOGIN_FAILED = "Invalid credentials"
    DEVICE_OFFLINE = "Device is offline: {uuid}"
    DEVICE_NOT_WEB_ACCESSIBLE = "Device is not web accessible: {uuid}"
    INCOMPATIBLE_APPLICATION = "Incompatible application: {application}"
    INCOMPATIBLE_FLEET = "Incompatible fleet: {fleet}"
    INVALID_SETTINGS = "Settings file not found or not in proper format. Rewriting default settings to: {path}"
    SUPERVISOR_VERSION_ERROR = "Unsupported function! Supervisor version v{req_version} required, current supervisor version is v{cur_version}."
    AMBIGUOUS_APPLICATION = "Application is ambiguous: {application}"
    AMBIGUOUS_FLEET = "Fleet is ambiguous: {fleet}"
    AMBIGUOUS_DEVICE = "Device is ambiguous: {uuid}"
    INVALID_PARAMETER = "Invalid parameter: {value} is not a valid value for parameter `{parameter}`"
    IMAGE_NOT_FOUND = "Image not found: {id}"
    RELEASE_NOT_FOUND = "Release not found: {id}"
    AMBIGUOUS_RELEASE = "Release commit is ambiguous: {commit}"
    SERVICE_NOT_FOUND = "Service not found: {id}"
    INVALID_APPLICATION_TYPE = "Invalid application type: {app_type}"
    INVALID_FLEET_TYPE = "Invalid fleet type: {fleet_type}"
    UNSUPPORTED_FEATURE = "You have to log in using credentials or Auth Token to use this function!"
    OS_UPDATE_ERROR = "OS update failed: {message}"
    DEVICE_NOT_PROVISIONED = "Device is not yet fully provisioned"
    DEVICE_OS_NOT_SUPPORT_LOCAL_MODE = "Device OS version does not support local mode"
    DEVICE_SUPERVISOR_NOT_SUPPORT_LOCAL_MODE = "Device supervisor version does not support local mode"
    DEVICE_OS_TYPE_NOT_SUPPORT_LOCAL_MODE = "Local mode is only supported on development OS versions"
    ORGANIZATION_NOT_FOUND = "Organization not found: {organization}"
    ORGANIZATION_MEMBERSHIP_NOT_FOUND = "Organization membership not found: {org_membership}"
    BALENA_DISCONTINUE_DEVICE_TYPE = "Discontinued device type: {type}"
    BALENA_ORG_MEMBERSHIP_ROLE_NOT_FOUND = "Organization membership role not found: {role_name}"
    BALENA_APP_MEMBERSHIP_ROLE_NOT_FOUND = "Application membership role not found: {role_name}"
    BALENA_FLEET_MEMBERSHIP_ROLE_NOT_FOUND = "Fleet membership role not found: {role_name}"
    APPLICATION_MEMBERSHIP_NOT_FOUND = "Application membership not found: {membership}"
    FLEET_MEMBERSHIP_NOT_FOUND = "Fleet membership not found: {membership}"
