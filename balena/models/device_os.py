import re

import semver

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions
from ..utils import compare

NETWORK_WIFI = "wifi"
NETWORK_ETHERNET = "ethernet"

NETWORK_TYPES = [NETWORK_WIFI, NETWORK_ETHERNET]

ARCH_COMPATIBILITY_MAP = {"aarch64": ["armv7hf", "rpi"], "armv7hf": ["rpi"]}

VERSION_RANGE_CHAR_LIST = ["x", "X", "*"]


def cmp_to_key(mycmp):
    "Convert a cmp= function into a key= function"

    class K:
        def __init__(self, obj, *args):
            self.obj = obj

        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0

    return K


def normalize_balena_semver(os_version):
    """
    safeSemver and trimOsText from resin-semver in Python.
    ref: https://github.com/balena-io-modules/resin-semver/blob/master/src/index.js#L5-L24

    """

    # fix major.minor.patch.rev to use rev as build metadata
    version = re.sub(r"(\.[0-9]+)\.rev", r"\1+rev", os_version)
    # fix major.minor.patch.prod to be treat .dev & .prod as build metadata
    version = re.sub(r"([0-9]+\.[0-9]+\.[0-9]+)\.(dev|prod)", r"\1+\2", version)
    # if there are no build metadata, then treat the parenthesized value as one
    version = re.sub(
        r"([0-9]+\.[0-9]+\.[0-9]+(?:[-\.][0-9a-z]+)*) \(([0-9a-z]+)\)",
        r"\1+\2",
        version,
    )
    # if there are build metadata, then treat the parenthesized value as point value
    version = re.sub(
        r"([0-9]+\.[0-9]+\.[0-9]+(?:[-\+\.][0-9a-z]+)*) \(([0-9a-z]+)\)",
        r"\1.\2",
        version,
    )
    # Remove "Resin OS" and "Balena OS" text
    version = re.sub(r"(resin|balena)\s*os\s*", "", version, flags=re.IGNORECASE)
    # remove optional versioning, eg "(prod)", "(dev)"
    version = re.sub(r"\s+\(\w+\)$", "", version)
    # remove "v" prefix
    version = re.sub(r"^v", "", version)
    return version


def get_rev_version(semver_version):
    if semver_version and semver_version.build:
        rev = 0

        for metadata_part in semver_version.build.split("."):
            match = re.match(r"rev(\d+)", metadata_part)
            if match:
                rev = int(match.groups()[0])
                break

        return rev

    return 0


def is_development_version(semver_version):
    if semver_version and semver_version.build:
        return "dev" in semver_version.build

    return False


def compare_balena_version(version_a, version_b):
    """
    Based on https://github.com/balena-io-modules/balena-semver#compare

    """

    if not version_a:
        return 0 if not version_b else -1

    if not version_b:
        return 1

    normalized_version_a = normalize_balena_semver(version_a)
    normalized_version_b = normalize_balena_semver(version_b)

    is_valid_semver_version_a = semver.VersionInfo.isvalid(normalized_version_a)
    is_valid_semver_version_b = semver.VersionInfo.isvalid(normalized_version_b)

    if not is_valid_semver_version_a or not is_valid_semver_version_b:
        if is_valid_semver_version_a:
            # verison b not valid semver
            return 1

        if is_valid_semver_version_b:
            # version a not valid semver
            return -1

        return compare(is_valid_semver_version_a, is_valid_semver_version_b)

    version_a_semver_obj = semver.VersionInfo.parse(normalized_version_a)
    version_b_semver_obj = semver.VersionInfo.parse(normalized_version_b)

    semver_compare_result = version_a_semver_obj.compare(version_b_semver_obj)

    if semver_compare_result != 0:
        return semver_compare_result

    rev_result = compare(get_rev_version(version_a_semver_obj), get_rev_version(version_b_semver_obj))

    if rev_result != 0:
        return rev_result

    dev_result = compare(
        is_development_version(version_a_semver_obj),
        is_development_version(version_b_semver_obj),
    )

    if dev_result != 0:
        return dev_result

    # We can ignore the localeCompare since this is only for balena OS version.
    return compare(normalized_version_a, normalized_version_b)


def sort_version(x, y):
    """
    Sort returned objects from device_os.get_supported_versions method.
    """

    return compare_balena_version(x["raw_version"], y["raw_version"])


def bsemver_match_range(version, version_range):
    if semver.VersionInfo.isvalid(version):
        try:
            if semver.VersionInfo.isvalid(version_range):
                if version_range and semver.match(version, f">={version_range}"):
                    return True
            else:
                if version_range[-1] in VERSION_RANGE_CHAR_LIST:
                    # version range contains 'x', 'X' or '*'
                    min_ver = f"{version_range[:-1]}0"
                    max_ver = str(semver.VersionInfo.parse(min_ver).next_version("minor"))
                    if semver.match(version, f">={min_ver}") and semver.match(version, f"<{max_ver}"):
                        return True
        except Exception:
            return False
    return False


# TODO: https://github.com/balena-io/balena-sdk/pull/288
class DeviceOs:
    """
    This class implements device os model for balena python SDK.

    """

    OS_UPDATE_ACTION_NAME = "resinhup"
    RELEASE_POLICY_TAG_NAME = "release-policy"
    ESR_NEXT_TAG_NAME = "esr-next"
    ESR_CURRENT_TAG_NAME = "esr-current"
    ESR_SUNSET_TAG_NAME = "esr-sunset"
    VARIANT_TAG_NAME = "variant"
    VERSION_TAG_NAME = "version"
    BASED_ON_VERSION_TAG_NAME = "meta-balena-base"
    OS_TYPES = {"default": "default", "esr": "esr"}
    OS_VARIANTS = {"production": "prod", "development": "dev"}

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

        """  # noqa: E501

        if "version" not in options:
            raise exceptions.MissingOption("An OS version is required when calling device_os.get_config()")

        if "network" not in options:
            options["network"] = "ethernet"

        options["appId"] = app_id

        return self.base_request.request(
            "download-config",
            "POST",
            data=options,
            endpoint=self.settings.get("api_endpoint"),
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
            {
                "Content-Length": "134445838",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, Application-Record-Count, MaxDataServiceVersion, X-Requested-With, X-Balena-Client",
                "content-disposition": 'attachment; filename="balena-cloud-FooBar4-raspberry-pi2-2.43.0+rev1-v10.2.2.img.zip"',
                "X-Content-Type-Options": "nosniff",
                "Access-Control-Max-Age": "86400",
                "x-powered-by": "Express",
                "Vary": "X-HTTP-Method-Override",
                "x-transfer-length": "134445838",
                "Connection": "keep-alive",
                "Access-Control-Allow-Credentials": "true",
                "Date": "Tue, 07 Jan 2020 17:40:52 GMT",
                "X-Frame-Options": "DENY",
                "Access-Control-Allow-Methods": "GET, PUT, POST, PATCH, DELETE, OPTIONS, HEAD",
                "Content-Type": "application/zip",
                "Access-Control-Allow-Origin": "*",
            }

        """  # noqa: E501

        self.params = self.parse_params(**data)
        data["version"] = self.get_device_os_semver_with_variant(data["version"])

        response = self.base_request.request(
            "download",
            "POST",
            data=data,
            endpoint=self.settings.get("api_endpoint"),
            stream=True,
            login=True,
        )
        if raw:
            # return urllib3.HTTPResponse object
            return response.raw
        else:
            return response

    def download_unconfigured_image(self, device_type, version, login=False, raw=False):
        """
        Download an unconfigured OS image.

        Args:
            device_type (str): device type slug.
            version (str): the balenaOS version of the image. The SDK will try to parse version into semver-compatible version, unsupported (unpublished) version will result in rejection.
            login (bool): include authentication information in the request or not. Must be set to True to download private device type. Default to False.
            raw (bool): determining method returned value. Default to False.

        Returns:
            object:
                If raw is True, urllib3.HTTPResponse object is returned.
                If raw is False, original response object is returned.

        Notes:
            default OS image file name can be found in response headers.

        Examples:
            >>> response = balena.models.device_os.download_unconfigured_image('raspberrypi4-64', 'latest', login=True)
            >>> type(response)
            <class 'requests.models.Response'>
            >>> response.headers
            {'Date': 'Tue, 01 Nov 2022 11:47:52 GMT', 'Content-Type': 'application/octet-stream', 'Transfer-Encoding': 'chunked', 'Connection': 'keep-alive', 'X-Frame-Options': 'DENY', 'X-Content-Type-Options': 'nosniff', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Credentials': 'true', 'access-control-allow-methods': 'GET, PUT, POST, PATCH, DELETE, OPTIONS, HEAD', 'access-control-allow-headers': 'Content-Type, Authorization, Application-Record-Count, MaxDataServiceVersion, X-Requested-With', 'access-control-max-age': '86400', 'content-encoding': 'gzip', 'content-disposition': 'attachment; filename="raspberrypi4-64-2.105.21-v14.2.10.img"', 'x-transfer-length': '173390850'}

        """  # noqa: E501

        # TODO: change the default value for `login` argument to True in next major release
        # so that users will be authenticated by default.
        if version != "latest":
            version = self.get_device_os_semver_with_variant(version)

        response = self.base_request.request(
            "/download?deviceType={device_type}&version={version}".format(device_type=device_type, version=version),
            "GET",
            endpoint=self.settings.get("api_endpoint"),
            stream=True,
            auth=login,
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

        """  # noqa: E501

        if "appId" not in params:
            raise exceptions.MissingOption("appId")

        try:
            params["appId"] = int(params["appId"])
        except ValueError:
            raise exceptions.InvalidOption("appId")

        if "version" not in params:
            raise exceptions.MissingOption("version")

        if "network" not in params:
            raise exceptions.MissingOption("network")

        if params["network"] not in NETWORK_TYPES:
            raise exceptions.InvalidOption("network")

        if params["network"] == NETWORK_WIFI:
            if "wifiSsid" not in params:
                raise exceptions.MissingOption("wifiSsid")

            # if 'wifiKey' not in params:
            #    raise exceptions.MissingOption('wifiKey')
        return params

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

        version_info = semver.VersionInfo.parse(normalize_balena_semver(os_version))

        if not version_info:
            return os_version

        tmp = []
        if version_info.prerelease:
            tmp = version_info.prerelease.split(".")
        if version_info.build:
            tmp = tmp + version_info.build.split(".")

        builds = []
        pre_releases = []

        if version_info.build:
            builds = version_info.build.split(".")

        if version_info.prerelease:
            pre_releases = version_info.prerelease.split(".")

        if os_variant and os_variant not in pre_releases and os_variant not in builds:
            builds.append(os_variant)

        return semver.format_version(
            version_info.major,
            version_info.minor,
            version_info.patch,
            version_info.prerelease,
            ".".join(builds),
        )

    def __get_os_app_tag(self, app_tags):
        tag_map = {}

        for app_tag in app_tags:
            tag_map[app_tag["tag_key"]] = app_tag["value"]

        return {
            "os_type": tag_map[self.RELEASE_POLICY_TAG_NAME]
            if self.RELEASE_POLICY_TAG_NAME in tag_map
            else self.OS_TYPES["default"],
            "next_line_version_range": tag_map[self.ESR_NEXT_TAG_NAME] if self.ESR_NEXT_TAG_NAME in tag_map else "",
            "current_line_version_range": tag_map[self.ESR_CURRENT_TAG_NAME]
            if self.ESR_CURRENT_TAG_NAME in tag_map
            else "",
            "sunset_line_version_range": tag_map[self.ESR_SUNSET_TAG_NAME]
            if self.ESR_SUNSET_TAG_NAME in tag_map
            else "",
        }

    def __get_os_versions(self, device_type):
        # fmt: off
        raw_query = (
            "$select=is_for__device_type,is_host"
            "&$expand="
                "application_tag($select=tag_key,value),"
                "is_for__device_type($select=slug),"
                "owns__release("
                    "$select=id,raw_version,version,is_final,release_tag,known_issue_list,variant,phase"
                    "&$filter="
                        "is_final%20eq%20true%20and%20"
                        "is_invalidated%20eq%20false%20and%20"
                        "status%20eq%20'success'"
                    "&$expand=release_tag($select=tag_key,value)"
                ")"
            "&$filter="
                "is_host%20eq%20true%20and%20"
                f"is_for__device_type/any(dt:dt/slug%20in%20('{device_type}'))"
        )
        # fmt: on

        return self.base_request.request(
            "application",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    # TODO: Drop this method & just use `release.phase` in the next major
    def __get_os_version_release_line(self, phase, version, app_tags):
        if not phase:
            # All patches belong to the same line.
            if bsemver_match_range(version, app_tags["next_line_version_range"]):
                return "next"

            if bsemver_match_range(version, app_tags["current_line_version_range"]):
                return "current"

            if bsemver_match_range(version, app_tags["sunset_line_version_range"]):
                return "sunset"

            if app_tags["os_type"].lower() == self.OS_TYPES["esr"]:
                return "outdated"

        if phase == "end-of-life":
            return "outdated"

        return phase

    def __get_os_versions_from_releases(self, releases, app_tags):
        os_variant_names = self.OS_VARIANTS.keys()
        releases_with_os_versions = []

        for release in releases:
            tag_map = {}

            for release_tag in release["release_tag"]:
                tag_map[release_tag["tag_key"]] = release_tag["value"]

            variant = release["variant"]

            if release["raw_version"].startswith("0.0.0"):
                # TODO: Drop this `else` once we migrate all version & variant tags to release.semver field
                # Ideally 'production' | 'development' | None.
                full_variant_name = tag_map[self.VARIANT_TAG_NAME] if self.VARIANT_TAG_NAME in tag_map else None
                if full_variant_name:
                    if full_variant_name in os_variant_names:
                        variant = self.OS_VARIANTS[full_variant_name]
                    else:
                        variant = full_variant_name
                else:
                    variant = None

                stripped_version = tag_map[self.VERSION_TAG_NAME] if self.VERSION_TAG_NAME in tag_map else ""
                # Backfill the native release_version field
                # TODO: This potentially generates an invalid semver and we should be doing
                # something like `.join(!version.includes('+') ? '+' : '.')`,  but this needs
                # discussion since otherwise it will break all ESR released as of writing this.
                release["raw_version"] = ".".join([x for x in [stripped_version, variant] if x])
            else:
                # Use the returned version object from API so we do not need to manually parse raw_version with semver
                version = release["version"]["version"]
                non_variant_build_parts = ".".join(
                    [build for build in release["version"]["build"] if build != release["variant"]]
                )

                stripped_version = "+".join([x for x in [version, non_variant_build_parts] if x])

            based_on_version = (
                tag_map[self.BASED_ON_VERSION_TAG_NAME]
                if self.BASED_ON_VERSION_TAG_NAME in tag_map
                else stripped_version
            )
            # TODO: Drop this call & just use `release.phase` in the next major
            line = self.__get_os_version_release_line(release["phase"], stripped_version, app_tags)

            release.update(
                {
                    "os_type": app_tags["os_type"],
                    "line": line,
                    "stripped_version": stripped_version,
                    "based_on_version": based_on_version,
                    "variant": variant,
                    "formatted_version": "v{version}{line}".format(
                        version=stripped_version, line=f" ({line})" if line else ""
                    ),
                }
            )
            releases_with_os_versions.append(release)

        return releases_with_os_versions

    def __transform_host_apps(self, host_apps):
        os_versions_by_device_type = {}

        for host_app in host_apps:
            if host_app["is_host"]:
                host_app_device_type = (
                    host_app["is_for__device_type"][0]["slug"] if len(host_app["is_for__device_type"]) > 0 else None
                )

                if not host_app_device_type:
                    return {}

                if host_app_device_type not in os_versions_by_device_type:
                    os_versions_by_device_type[host_app_device_type] = []

                app_tags = self.__get_os_app_tag(host_app["application_tag"])
                os_versions_by_device_type[host_app_device_type].extend(
                    self.__get_os_versions_from_releases(host_app["owns__release"], app_tags)
                )

        for device_type in os_versions_by_device_type:
            os_versions_by_device_type[device_type].sort(reverse=True, key=cmp_to_key(sort_version))
            recommended_per_os_type = {}

            for version in os_versions_by_device_type[device_type]:
                if version["os_type"] not in recommended_per_os_type:
                    if (
                        version["variant"] != "dev"
                        and not version["known_issue_list"]
                        and not version["version"]["prerelease"]
                    ):
                        additional_format = (
                            " ({line}, recommended)".format(line=version["line"])
                            if version["line"]
                            else " (recommended)"
                        )
                        version["is_recommended"] = True
                        version["formatted_version"] = "v{version}{additional_format}".format(
                            version=version["stripped_version"],
                            additional_format=additional_format,
                        )
                        recommended_per_os_type[version["os_type"]] = True

        return os_versions_by_device_type

    def get_supported_versions(self, device_type):
        """
        Get OS supported versions.

        Args:
            device_type (str): device type slug.
            auth (Optional[bool]): if auth is True then auth header will be added to the request (to get private device types) otherwise no auth header and only public device types returned. Default to True.

        """  # noqa: E501

        host_apps = self.__get_os_versions(device_type)
        versions_by_dt = self.__transform_host_apps(host_apps)

        if device_type in versions_by_dt:
            versions = [
                x["raw_version"] for x in versions_by_dt[device_type] if x["os_type"] == self.OS_TYPES["default"]
            ]
            return versions

        return []

    def get_available_os_versions(self, device_type):
        """
        Get the supported balenaOS versions (ESR included) for the provided device type.

        Args:
            device_type (str): device type slug.

        Returns:
            list: balenaOS versions.

        """

        host_apps = self.__get_os_versions(device_type)
        versions_by_dt = self.__transform_host_apps(host_apps)

        if device_type in versions_by_dt:
            return versions_by_dt[device_type]

        return []

    def is_architecture_compatible_with(self, os_architecture, application_architecture):
        """
        Returns whether the specified OS architecture is compatible with the target architecture.

        Args:
            os_architecture (str): The OS's architecture as specified in its device type.
            application_architecture (str): The application's architecture as specified in its device type.

        Returns:
            bool: Whether the specified OS architecture is capable of running applications build for the target architecture.

        """  # noqa: E501

        if os_architecture != application_architecture:
            if (
                os_architecture in ARCH_COMPATIBILITY_MAP
                and application_architecture in ARCH_COMPATIBILITY_MAP[os_architecture]
            ):
                return True
            return False

        return True
