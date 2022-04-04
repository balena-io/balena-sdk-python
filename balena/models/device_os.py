import json
import re

import semver

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions

NETWORK_WIFI = 'wifi'
NETWORK_ETHERNET = 'ethernet'

NETWORK_TYPES = [
    NETWORK_WIFI,
    NETWORK_ETHERNET
]

ARCH_COMPATIBILITY_MAP = {
    'aarch64': ['armv7hf', 'rpi'],
    'armv7hf': ['rpi']
}


# TODO: https://github.com/balena-io/balena-sdk/pull/288
class DeviceOs:
    """
    This class implements device os model for balena python SDK.

    """

    OS_UPDATE_ACTION_NAME = 'resinhup'

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def get_config(self, app_id, options):
        """
        Get an application config.json.

        Args:
            app_id (str): application id.
            options (dict): OS configuration options to use. The available options are listed below:
                version (str): the OS version of the image.
                network (Optional[str]): the network type that the device will use, one of 'ethernet' or 'wifi' and defaults to 'ethernet' if not specified.
                appUpdatePollInterval (Optional[str]): how often the OS checks for updates, in minutes.
                wifiKey (Optional[str]): the key for the wifi network the device will connect to.
                wifiSsid (Optional[str]): the ssid for the wifi network the device will connect to.
                ip (Optional[str]): static ip address.
                gateway (Optional[str]): static ip gateway.
                netmask (Optional[str]): static ip netmask.

        Returns:
            dict: application config.json

        """

        if 'version' not in options:
            raise exceptions.MissingOption('An OS version is required when calling device_os.get_config()')

        if 'network' not in options:
            options['network'] = 'ethernet'

        options['appId'] = app_id

        return self.base_request.request(
            'download-config', 'POST', data=options,
            endpoint=self.settings.get('api_endpoint')
        )

    def download(self, raw=False, **data):
        """
        Download an OS image. This function only works if you log in using credentials or Auth Token.

        Args:
            raw (bool): determining function return value.
            **data: os parameters keyword arguments.
                version (str): the balenaOS version of the image. The SDK will try to parse version into semver-compatible version, unsupported (unpublished) version will result in rejection.
                appId (str): the application ID.
                network (str): the network type that the device will use, one of 'ethernet' or 'wifi'.
                fileType (Optional[str]): one of '.img' or '.zip' or '.gz', defaults to '.img'.
                wifiKey (Optional[str]): the key for the wifi network the device will connect to if network is wifi.
                wifiSsid (Optional[str]): the ssid for the wifi network the device will connect to if network is wifi.
                appUpdatePollInterval (Optional[str]): how often the OS checks for updates, in minutes.

        Returns:
            object:
                If raw is True, urllib3.HTTPResponse object is returned.
                If raw is False, original response object is returned.

        Notes:
            default OS image file name can be found in response headers.

        Examples:
            >>> data = {'appId': '1476418', 'network': 'ethernet', 'version': '2.43.0+rev1.prod'}
            >>> response = balena.models.device_os.download(**data)
            >>> type(response)
            <class 'requests.models.Response'>
            >>> response['headers']
            >>> response.headers
            {'Content-Length': '134445838', 'Access-Control-Allow-Headers': 'Content-Type, Authorization, Application-Record-Count, MaxDataServiceVersion, X-Requested-With, X-Balena-Client', 'content-disposition': 'attachment; filename="balena-cloud-FooBar4-raspberry-pi2-2.43.0+rev1-v10.2.2.img.zip"', 'X-Content-Type-Options': 'nosniff', 'Access-Control-Max-Age': '86400', 'x-powered-by': 'Express', 'Vary': 'X-HTTP-Method-Override', 'x-transfer-length': '134445838', 'Connection': 'keep-alive', 'Access-Control-Allow-Credentials': 'true', 'Date': 'Tue, 07 Jan 2020 17:40:52 GMT', 'X-Frame-Options': 'DENY', 'Access-Control-Allow-Methods': 'GET, PUT, POST, PATCH, DELETE, OPTIONS, HEAD', 'Content-Type': 'application/zip', 'Access-Control-Allow-Origin': '*'}

        """

        self.params = self.parse_params(**data)
        data['version'] = self.get_device_os_semver_with_variant(data['version'])

        response = self.base_request.request(
            'download', 'POST', data=data,
            endpoint=self.settings.get('api_endpoint'), stream=True, login=True
        )
        if raw:
            # return urllib3.HTTPResponse object
            return response.raw
        else:
            return response

    def download_unconfigured_image(self, device_type, version, raw=False):
        """
        Download an unconfigured OS image.

        Args:
            device_type (str): device type slug.
            version (str): the balenaOS version of the image. The SDK will try to parse version into semver-compatible version, unsupported (unpublished) version will result in rejection.
            raw (bool): determining function return value.

        Returns:
            object:
                If raw is True, urllib3.HTTPResponse object is returned.
                If raw is False, original response object is returned.

        Notes:
            default OS image file name can be found in response headers.

        Examples:
            >>> response = balena.models.device_os.download_unconfigured_image('raspberry-pi2', 'latest')
            >>> type(response)
            <class 'requests.models.Response'>
            >>> response['headers']
            >>> response.headers
            {'Access-Control-Allow-Headers': 'Content-Type, Authorization, Application-Record-Count, MaxDataServiceVersion, X-Requested-With, X-Balena-Client', 'content-disposition': 'attachment; filename="balena-cloud-raspberry-pi2-2.43.0+rev1-v10.2.2.img"', 'X-Content-Type-Options': 'nosniff', 'Access-Control-Max-Age': '86400', 'Transfer-Encoding': 'chunked', 'x-powered-by': 'Express', 'content-encoding': 'gzip', 'x-transfer-length': '134445269', 'last-modified': 'Mon, 23 Sep 2019 15:21:33 GMT', 'Connection': 'keep-alive', 'Access-Control-Allow-Credentials': 'true', 'Date': 'Tue, 07 Jan 2020 18:14:47 GMT', 'X-Frame-Options': 'DENY', 'Access-Control-Allow-Methods': 'GET, PUT, POST, PATCH, DELETE, OPTIONS, HEAD', 'Content-Type': 'application/octet-stream', 'Access-Control-Allow-Origin': '*'}

        """

        if version == 'latest':
            version = self.get_supported_versions(device_type)['latest']
        else:
            version = self.get_device_os_semver_with_variant(version)

        response = self.base_request.request(
            '/download?deviceType={device_type}&version={version}'.format(device_type=device_type, version=version),
            'GET',
            endpoint=self.settings.get('api_endpoint'), stream=True, auth=False
        )
        if raw:
            # return urllib3.HTTPResponse object
            return response.raw
        else:
            return response

    def parse_params(self, **params):
        """
        Validate parameters for downloading device OS image.

        Args:
            **parameters: os parameters keyword arguments.

        Returns:
            dict: validated parameters.

        Raises:
            MissingOption: if mandatory option are missing.
            InvalidOption: if appId or network are invalid (appId is not a number or parseable string. network is not in NETWORK_TYPES)

        """

        if 'appId' not in params:
            raise exceptions.MissingOption('appId')

        try:
            params['appId'] = int(params['appId'])
        except ValueError:
            raise exceptions.InvalidOption('appId')

        if 'version' not in params:
            raise exceptions.MissingOption('version')

        if 'network' not in params:
            raise exceptions.MissingOption('network')

        if params['network'] not in NETWORK_TYPES:
            raise exceptions.InvalidOption('network')

        if params['network'] == NETWORK_WIFI:
            if 'wifiSsid' not in params:
                raise exceptions.MissingOption('wifiSsid')

            # if 'wifiKey' not in params:
            #    raise exceptions.MissingOption('wifiKey')
        return params

    def __normalize_balena_semver(self, os_version):
        """
        safeSemver and trimOsText from resin-semver in Python.
        ref: https://github.com/balena-io-modules/resin-semver/blob/master/src/index.js#L5-L24

        """

        # fix major.minor.patch.rev to use rev as build metadata
        version = re.sub(r'(\.[0-9]+)\.rev', r'\1+rev', os_version)
        # fix major.minor.patch.prod to be treat .dev & .prod as build metadata
        version = re.sub(r'([0-9]+\.[0-9]+\.[0-9]+)\.(dev|prod)', r'\1+\2', version)
        # if there are no build metadata, then treat the parenthesized value as one
        version = re.sub(r'([0-9]+\.[0-9]+\.[0-9]+(?:[-\.][0-9a-z]+)*) \(([0-9a-z]+)\)', r'\1+\2', version)
        # if there are build metadata, then treat the parenthesized value as point value
        version = re.sub(r'([0-9]+\.[0-9]+\.[0-9]+(?:[-\+\.][0-9a-z]+)*) \(([0-9a-z]+)\)', r'\1.\2', version)
        # Remove "Resin OS" and "Balena OS" text
        version = re.sub(r'(resin|balena)\s*os\s*', '', version, flags=re.IGNORECASE)
        # remove optional versioning, eg "(prod)", "(dev)"
        version = re.sub(r'\s+\(\w+\)$', '', version)
        # remove "v" prefix
        version = re.sub(r'^v', '', version)
        return version

    def get_device_os_semver_with_variant(self, os_version, os_variant=None):
        """
        Get current device os semver with variant.

        Args:
            os_version (str): current os version.
            os_variant (Optional[str]): os variant.

        Examples:
            >>> balena.models.device_os.get_device_os_semver_with_variant('balenaOS 2.29.2+rev1', 'prod')
            '2.29.2+rev1.prod'

        """

        if not os_version:
            return None

        version_info = semver.VersionInfo.parse(self.__normalize_balena_semver(os_version))

        if not version_info:
            return os_version

        tmp = []
        if version_info.prerelease:
            tmp = version_info.prerelease.split('.')
        if version_info.build:
            tmp = tmp + version_info.build.split('.')

        xstr = lambda s: '' if s is None else str(s)
        return semver.format_version(
            version_info.major,
            version_info.minor,
            version_info.patch,
            version_info.prerelease,
            xstr(version_info.build) + '.' + os_variant if os_variant and os_variant not in tmp else version_info.build
        )

    def get_supported_versions(self, device_type, auth=True):
        """
        Get OS supported versions.

        Args:
            device_type (str): device type slug.
            auth (Optional[bool]): if auth is True then auth header will be added to the request (to get private device types) otherwise no auth header and only public device types returned. Default to True.

        Returns:
            dict: the versions information, of the following structure:
                * versions - an array of strings, containing exact version numbers supported by the current environment.
                * recommended - the recommended version, i.e. the most recent version that is _not_ pre-release, can be `None`.
                * latest - the most recent version, including pre-releases.
                * default - recommended (if available) or latest otherwise.

        """

        response = self.base_request.request(
            '/device-types/v1/{device_type}/images'.format(device_type=device_type), 'GET',
            endpoint=self.settings.get('api_endpoint'), auth=auth
        )

        potential_recommended_versions = [i for i in response['versions'] if not re.search(r'(\.|\+|-)dev', i)]
        potential_recommended_versions = [i for i in potential_recommended_versions if not semver.parse(i)['prerelease']]
        recommended = potential_recommended_versions[0] if potential_recommended_versions else None

        return {
            'versions': response['versions'],
            'recommended': recommended,
            'latest': response['latest'],
            'default': recommended if recommended else response['latest']
        }

    def is_architecture_compatible_with(self, os_architecture, application_architecture):
        """
        Returns whether the specified OS architecture is compatible with the target architecture.

        Args:
            os_architecture (str): The OS's architecture as specified in its device type.
            application_architecture (str): The application's architecture as specified in its device type.

        Returns:
            bool: Whether the specified OS architecture is capable of running applications build for the target architecture.

        """

        if os_architecture != application_architecture:
            if os_architecture in ARCH_COMPATIBILITY_MAP and application_architecture in ARCH_COMPATIBILITY_MAP[os_architecture]:
                return True
            return False

        return True
