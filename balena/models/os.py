import re
from collections import defaultdict
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired

from semver.version import Version

from .. import exceptions
from ..balena_auth import request
from ..hup import get_hup_action_type
from ..pine import PineClient
from ..types import AnyObject
from ..utils import compare, merge, normalize_balena_semver
from ..settings import Settings
from .application import Application
from .device_type import DeviceType


class DownloadConfig(TypedDict):
    developmentMode: NotRequired[bool]
    appUpdatePollInterval: NotRequired[int]
    network: NotRequired[Literal["ethernet", "wifi"]]
    wifiKey: NotRequired[str]
    wifiSsid: NotRequired[str]
    appId: NotRequired[int]
    fileType: NotRequired[Union[Literal[".img"], Literal[".zip"], Literal[".gz"]]]
    imageType: NotRequired[Union[Literal["raw"], Literal["flasher"]]]


class ImgConfigOptions(TypedDict, total=False):
    network: Optional[Literal["ethernet", "wifi"]]
    appUpdatePollInterval: Optional[int]
    provisioningKeyName: Optional[str]
    provisioningKeyExpiryDate: Optional[str]
    wifiKey: Optional[str]
    wifiSsid: Optional[str]
    ip: Optional[str]
    gateway: Optional[str]
    netmask: Optional[str]
    deviceType: Optional[str]
    version: str
    developmentMode: Optional[bool]


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

    is_valid_semver_version_a = Version.is_valid(normalized_version_a)
    is_valid_semver_version_b = Version.is_valid(normalized_version_b)

    if not is_valid_semver_version_a or not is_valid_semver_version_b:
        if is_valid_semver_version_a:
            # verison b not valid semver
            return 1

        if is_valid_semver_version_b:
            # version a not valid semver
            return -1

        return compare(is_valid_semver_version_a, is_valid_semver_version_b)

    version_a_semver_obj = Version.parse(normalized_version_a)
    version_b_semver_obj = Version.parse(normalized_version_b)

    semver_compare_result = version_a_semver_obj.compare(version_b_semver_obj)

    if semver_compare_result != 0:
        return semver_compare_result

    rev_result = compare(
        get_rev_version(version_a_semver_obj),
        get_rev_version(version_b_semver_obj),
    )

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
    if Version.is_valid(version):
        try:
            parsed_version = Version.parse(version)
            if Version.is_valid(version_range):
                if version_range and parsed_version.match(f">={version_range}"):
                    return True
            else:
                if version_range[-1] in VERSION_RANGE_CHAR_LIST:
                    # version range contains 'x', 'X' or '*'
                    min_ver = f"{version_range[:-1]}0"
                    max_ver = str(Version.parse(min_ver).next_version("minor"))
                    if parsed_version.match(f">={min_ver}") and parsed_version.match(f"<{max_ver}"):
                        return True
        except Exception:
            return False
    return False


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

    def __init__(self, pine: PineClient, settings: Settings):
        self.__pine = pine
        self.__settings = settings
        self.__device_type = DeviceType(pine, settings)
        self.__application = Application(pine, settings, False)

    def get_available_os_versions(self, device_type: Union[str, List[str]]):
        """
        Get the supported OS versions for the provided device type(s)

        Args:
            device_type (Union[str, List[str]]): device type slug.

        Returns:
            list: balenaOS versions.

        """
        single_device_type = isinstance(device_type, str)
        device_types = device_type if isinstance(device_type, list) else [device_type]
        versions_by_dt = self.__get_all_os_versions(device_types, True)

        if single_device_type:
            return versions_by_dt.get(device_type, [])

        return versions_by_dt

    def get_all_os_versions(self, device_type: Union[str, List[str]], options: AnyObject = {}):
        """
        Get all OS versions for the provided device type(s), inlcuding invalidated ones

        Args:
            device_type (Union[str, List[str]]): device type slug.
            options (AnyObject): extra pine options to use

        Returns:
            list: balenaOS versions.

        """
        single_device_type = isinstance(device_type, str)
        device_types = device_type if isinstance(device_type, list) else [device_type]

        if options == {}:
            versions_by_dt = self.__get_all_os_versions(device_types)
        else:
            hostapps = self.__get_os_versions(device_types, options)
            versions_by_dt = self.__transform_host_apps(hostapps)

        if single_device_type:
            return versions_by_dt.get(device_type, [])

        return versions_by_dt

    def get_download_size(self, device_type: str, version: str = "latest") -> float:
        """
        Get OS download size estimate. Currently only the raw (uncompressed) size is reported.

        Args:
            device_type (str): device type slug.
            version (str): semver-compatible version or 'latest', defaults to 'latest'.
            * The version **must** be the exact version number.

        Returns:
            float: OS image download size, in bytes.
        """
        slug = self.__device_type.get(device_type, {"$select": "slug"})["slug"]
        return float(
            request(
                method="GET",
                settings=self.__settings,
                path=f"/device-types/v1/{slug}/images/{version}/download-size",
            )["size"]
        )

    def get_max_satisfying_version(
        self,
        device_type: str,
        version_or_range: str = "latest",
        os_type: Optional[Literal["default", "esr"]] = None,
    ) -> Optional[str]:
        """
        Get OS download size estimate. Currently only the raw (uncompressed) size is reported.

        Args:
            device_type (str): device type slug.
            version_or_range (str): can be one of the exact version number,
            in which case it is returned if the version is supported,
            or `None` is returned otherwise,
            * a [semver](https://www.npmjs.com/package/semver)-compatible
            range specification, in which case the most recent satisfying version is returned
            if it exists, or `None` is returned,
            `'latest'` in which case the most recent version is returned, including pre-releases,
            `'recommended'` in which case the recommended version is returned, i.e. the most
            recent version excluding pre-releases, which can be `None` if only pre-release versions
            are available,
            `'default'` in which case the recommended version is returned if available,
            or `latest` is returned otherwise.
            Defaults to `'latest'`
            os_type (Optional[Literal["default", "esr"]]): The used OS type.

        Returns:
            float: OS image download size, in bytes.
        """

        slug = self.__device_type.get(device_type, {"$select": "slug"})["slug"]
        os_versions: List[Any] = self.get_available_os_versions(slug)  # type: ignore

        if os_type is not None:
            os_versions = [osv for osv in os_versions if osv["os_type"] == os_type]

        if version_or_range == "recommended":
            return next(
                (v.get("raw_version") for v in os_versions if v.get("is_recommended")),
                None,
            )

        if version_or_range == "latest":
            return os_versions[0].get("raw_version") if os_versions else None

        if version_or_range == "default":
            return next(
                (v["raw_version"] for v in os_versions if v.get("is_recommended")),
                os_versions[0]["raw_version"] if os_versions else None,
            )

        versions = [v.get("raw_version") for v in os_versions]

        if version_or_range in versions:
            return version_or_range

        parsed_versions = [Version.parse(v) for v in versions if Version.is_valid(v)]
        satisfying_versions = [v for v in parsed_versions if v.match(version_or_range)]
        if not satisfying_versions:
            return None
        return str(max(satisfying_versions))

    def download(
        self,
        device_type: str,
        version: str = "latest",
        options: DownloadConfig = {},
    ):
        """
        Get OS download size estimate. Currently only the raw (uncompressed) size is reported.

        Args:
            device_type (str): device type slug.
            version (str): semver-compatible version or 'latest', defaults to 'latest'.
            * The version **must** be the exact version number.
            options (DownloadConfig): OS configuration options to use.

        Returns:
            float: OS image download size, in bytes.

        Example:
            >>> with b.models.device_os.download("raspberrypi3") as stream:
            ...    stream.raise_for_status()
            ...    with open("my-image-filename", "wb") as f:
            ...        for chunk in stream.iter_content(chunk_size=8192):
            ...            f.write(chunk)
        """
        slug = self.__device_type.get(device_type, {"$select": "slug"})["slug"]

        if version == "latest":
            versions = [v for v in self.get_available_os_versions(slug) if v["os_type"] in self.OS_TYPES["default"]]
            version = next(
                (v["raw_version"] for v in versions if v.get("is_recommended")),
                versions[0]["raw_version"] if versions else None,  # type: ignore
            )
        else:
            version = normalize_balena_semver(version)

        return request(
            method="GET",
            settings=self.__settings,
            path="/download",
            qs={**options, "deviceType": slug, "version": version},
            return_raw=True,
            stream=True,
        )

    def get_config(self, slug_or_uuid_or_id: Union[str, int], options: ImgConfigOptions):
        """
        Download application config.json.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (ImgConfigOptions): OS configuration dict to use. The available options
            are listed below:
                network (Optional[Literal["ethernet", "wifi"]]): The network type that
                the device will use, one of 'ethernet' or 'wifi'.
                appUpdatePollInterval (Optional[int]): How often the OS checks for updates, in minutes.
                provisioningKeyName (Optional[str]): Name assigned to API key
                provisioningKeyExpiryDate (Optional[str]): Expiry Date assigned to API key
                wifiKey (Optional[str]): The key for the wifi network the device will connect to.
                wifiSsid (Optional[str]): The ssid for the wifi network the device will connect to.
                ip (Optional[str]): static ip address
                gateway (Optional[str]): static ip gateway.
                netmask (Optional[str]): static ip netmask.
                deviceType (Optional[str]): The device type.
                version (str): Required: the OS version of the image.
                developmentMode (Optional[bool]): If the device should be in development mode.

        Returns:
            dict: application config.json content.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        """

        if options.get("version") is None:
            raise Exception("An OS version is required when calling os.getConfig")

        options["network"] = options.get("network", "ethernet")
        app_id = self.__application.get_id(slug_or_uuid_or_id)

        try:
            return request(
                method="POST",
                settings=self.__settings,
                path="/download-config",
                body={**options, "appId": app_id},
            )
        except exceptions.RequestError as e:
            if e.status_code == 404:
                raise exceptions.ApplicationNotFound(slug_or_uuid_or_id)
            raise e

    def is_supported_os_update(self, device_type: str, current_version: str, target_version: str) -> bool:
        """
         Returns the supported OS update targets for the provided device type.

        Args:
            device_type (str): device type slug.
            current_version (str): emver-compatible version for the starting OS version
            target_version (str): semver-compatible version for the target OS version
        """
        try:
            action_type = get_hup_action_type(device_type, current_version, target_version)
            if action_type is not None:
                return True
            return False
        except exceptions.OsUpdateError:
            return False

    def get_supported_os_update_versions(self, device_type: str, current_version: str):
        """
        Get OS supported versions.

        Args:
            device_type (str): device type slug.
            current_version (str): device type slug.
        """
        slug = self.__device_type.get(device_type, {"$select": "slug"})["slug"]
        all_versions = self.get_available_os_versions(slug)
        all_versions = [v.get("raw_version") for v in all_versions if v.get("os_type") == self.OS_TYPES["default"]]

        current = next(
            (v for v in all_versions if str(Version.parse(v)) == str(Version.parse(current_version))),
            None,
        )

        versions = [v for v in all_versions if self.is_supported_os_update(device_type, current_version, v)]
        recommended = next((v for v in versions if not Version.parse(v).prerelease), None)

        return {"versions": versions, "recommended": recommended, "current": current}

    def is_architecture_compatible_with(self, os_architecture: str, application_architecture: str):
        """
        Returns whether the specified OS architecture is compatible with the target architecture.

        Args:
            os_architecture (str): The OS's architecture as specified in its device type.
            application_architecture (str): The application's architecture as specified in its device type.

        Returns:
            bool: Whether the specified OS architecture is capable of
                  running applications build for the target architecture.
        """

        if os_architecture != application_architecture:
            if (
                os_architecture in ARCH_COMPATIBILITY_MAP
                and application_architecture in ARCH_COMPATIBILITY_MAP[os_architecture]
            ):
                return True
            return False

        return True

    def __tags_to_dict(self, tags: List[Any]) -> Dict[str, str]:
        tag_map = {}

        for app_tag in tags:
            tag_map[app_tag["tag_key"]] = app_tag["value"]

        return tag_map

    def __get_os_app_tags(self, app_tags: List[Any]):
        tag_map = self.__tags_to_dict(app_tags)
        return {
            "os_type": tag_map.get(self.RELEASE_POLICY_TAG_NAME, self.OS_TYPES["default"]),
            "next_line_version_range": tag_map.get(self.ESR_NEXT_TAG_NAME, ""),
            "current_line_version_range": tag_map.get(self.ESR_CURRENT_TAG_NAME, ""),
            "sunset_line_version_range": tag_map.get(self.ESR_SUNSET_TAG_NAME, ""),
        }

    def __get_os_versions(self, device_types: List[str], options: AnyObject = {}):
        owns_release = merge(
            {
                "$select": [
                    "id",
                    "known_issue_list",
                    "raw_version",
                    "variant",
                    "phase",
                ],
                "$expand": {"release_tag": {"$select": ["tag_key", "value"]}},
            },
            options,
        )

        return self.__pine.get(
            {
                "resource": "application",
                "options": {
                    "$select": "is_for__device_type",
                    "$expand": {
                        "application_tag": {"$select": ["tag_key", "value"]},
                        "is_for__device_type": {"$select": "slug"},
                        "owns__release": owns_release,
                    },
                    "$filter": {
                        "is_host": True,
                        "is_for__device_type": {
                            "$any": {
                                "$alias": "dt",
                                "$expr": {"dt": {"slug": {"$in": device_types}}},
                            }
                        },
                    },
                },
            }
        )

    def __get_all_os_versions(self, device_types: List[str], listed_by_default: bool = False):
        listed_by_filter = (
            {
                "$filter": {
                    "is_final": True,
                    "is_invalidated": False,
                    "status": "success",
                }
            }
            if listed_by_default
            else {}
        )
        hostapps = self.__get_os_versions(device_types, listed_by_filter)
        return self.__transform_host_apps(hostapps)

    # TODO: Drop this method & just use `release.phase` in the next major
    def __get_os_version_release_line(self, phase: Optional[str], version: str, app_tags: Dict[str, str]):
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

    def __get_os_versions_from_releases(self, releases: List[Any], app_tags: Any):
        os_variant_names = self.OS_VARIANTS.keys()
        releases_with_os_versions = []

        for release in releases:
            tag_map = self.__tags_to_dict(release.get("release_tag", []))

            release_semver_obj = (
                Version.parse(release["raw_version"]) if not release["raw_version"].startswith("0.0.0") else None
            )

            variant = release.get("variant")
            if variant == "":
                variant = None

            stripped_version = None
            if release_semver_obj is None:
                full_variant_name = tag_map.get(self.VARIANT_TAG_NAME)
                if isinstance(full_variant_name, str):
                    if full_variant_name in os_variant_names:
                        variant = self.OS_VARIANTS[full_variant_name]
                    else:
                        variant = full_variant_name
                else:
                    variant = None
                stripped_version = tag_map.get(self.VERSION_TAG_NAME, "")

                release["raw_version"] = ".".join([x for x in [stripped_version, variant] if x])
            else:
                version = str(release_semver_obj.finalize_version())
                builds = (release_semver_obj.build or "").split(".")
                non_variant_build_parts = ".".join([build for build in builds if build != release["variant"]])

                stripped_version = "+".join([x for x in [version, non_variant_build_parts] if x])

            # TODO: Drop this call & just use `release.phase` in the next major
            line = self.__get_os_version_release_line(release["phase"], stripped_version, app_tags)

            release.update(
                {
                    "variant": variant,
                    "os_type": app_tags.get("os_type"),
                    "line": line,
                    "raw_version": release["raw_version"],
                    "stripped_version": stripped_version,
                    "based_on_version": tag_map.get(self.BASED_ON_VERSION_TAG_NAME, stripped_version),
                }
            )
            releases_with_os_versions.append(release)

        return releases_with_os_versions

    def __transform_host_apps(self, host_apps):
        os_versions_by_device_type = defaultdict(list)

        for host_app in host_apps:
            host_app_device_type = host_app.get("is_for__device_type", [{}])[0].get("slug")
            if host_app_device_type is None:
                continue

            app_tags = self.__get_os_app_tags(host_app.get("application_tag", []))

            os_versions_by_device_type[host_app_device_type] += self.__get_os_versions_from_releases(
                host_app.get("owns__release", []), app_tags
            )

        for device_type in os_versions_by_device_type:
            os_versions_by_device_type[device_type].sort(reverse=True, key=cmp_to_key(sort_version))
            recommended_per_os_type: Dict[str, bool] = {}

            for version in os_versions_by_device_type[device_type]:
                if version["os_type"] not in recommended_per_os_type:
                    if (
                        version["variant"] != "dev"
                        and not version["known_issue_list"]
                        and not Version.parse(version["raw_version"]).prerelease
                    ):
                        additional_format = (
                            f" ({version['line']}, recommended)" if version.get("line") else " (recommended)"
                        )
                        version["is_recommended"] = True
                        version["formatted_version"] = f"v{version['stripped_version']}{additional_format}"
                        recommended_per_os_type[version["os_type"]] = True

        return os_versions_by_device_type
