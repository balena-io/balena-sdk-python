import numbers
import re
from collections import defaultdict
from typing import Any, Callable, Dict, Literal, Optional, TypeVar

from semver.version import Version

from .exceptions import RequestError, SupervisorLocked

SUPERVISOR_LOCKED_STATUS_CODE = 423


def is_id(value: Any) -> bool:
    """
    Return True, if the input value is a valid ID. False otherwise.

    """

    if isinstance(value, numbers.Number):
        try:
            int(value)  # type: ignore
            return True
        except ValueError:
            return False
    return False


def is_full_uuid(value: Any) -> bool:
    """
    Return True, if the input value is a valid UUID. False otherwise.

    """

    if isinstance(value, str):
        if len(value) == 32 or len(value) == 62:
            try:
                str(value)
                return True
            except ValueError:
                return False
    return False


def compare(a, b):
    """

    Return 1 if a is greater than b, 0 if a is equal to b and -1 otherwise.

    """

    if a > b:
        return 1

    if b > a:
        return -1

    return 0


known_pine_option_keys = set(["$select", "$expand", "$filter", "$orderby", "$top", "$skip", "$count"])


def merge(defaults, extras=None, replace_selects=False):
    if extras is None:
        return defaults

    unknown_pine_option = next((key for key in extras if key not in known_pine_option_keys), None)
    if unknown_pine_option is not None:
        raise ValueError(f"Unknown pine option: {unknown_pine_option}")

    result = {**defaults}

    if extras.get("$select"):
        extra_select = (
            extras["$select"]
            if isinstance(extras["$select"], list) or extras["$select"] == "*"
            else [extras["$select"]]
        )
        if replace_selects:
            result["$select"] = extra_select
        elif extra_select == "*":
            result["$select"] = "*"
        else:
            existing_select = result.get("$select")
            existing_select = [existing_select] if not isinstance(existing_select, list) else existing_select
            extra_select = extra_select or []
            merged_select = existing_select + extra_select
            result["$select"] = list(set(merged_select))

    for key in known_pine_option_keys:
        if key in extras:
            result[key] = extras[key]

    if extras.get("$filter"):
        result["$filter"] = (
            {"$and": [defaults.get("$filter", {}), extras["$filter"]]} if defaults.get("$filter") else extras["$filter"]
        )

    if extras.get("$expand"):
        result["$expand"] = merge_expand_options(defaults.get("$expand"), extras["$expand"], replace_selects)

    return result


def merge_expand_options(default_expand=None, extra_expand=None, replace_selects=False):
    if default_expand is None:
        return extra_expand

    default_expand = convert_expand_to_object(default_expand, True)
    extra_expand = convert_expand_to_object(extra_expand)

    for expand_key in extra_expand:
        default_expand[expand_key] = merge(
            default_expand.get(expand_key, {}), extra_expand[expand_key], replace_selects
        )

    return default_expand


def convert_expand_to_object(expand_option, clone_if_needed=False):
    if expand_option is None:
        return {}

    if isinstance(expand_option, str):
        return {expand_option: {}}

    if isinstance(expand_option, list):
        return {k: v for d in expand_option for k, v in (d.items() if isinstance(d, dict) else {d: {}}.items())}

    unknown_pine_option = next((key for key in expand_option if key not in known_pine_option_keys), None)
    if unknown_pine_option is not None:
        raise ValueError(f"Unknown pine expand options: {unknown_pine_option}")

    return {**expand_option} if clone_if_needed else expand_option


def get_current_service_details_pine_expand(
    expand_release: bool,
) -> Dict[str, Any]:
    return {
        "image_install": {
            "$select": ["id", "download_progress", "status", "install_date"],
            "$filter": {
                "status": {
                    "$ne": "deleted",
                },
            },
            "$expand": {
                "image": {
                    "$select": ["id"],
                    "$expand": {
                        "is_a_build_of__service": {
                            "$select": ["id", "service_name"],
                        },
                    },
                },
                **(
                    {
                        "is_provided_by__release": {
                            "$select": ["id", "commit", "raw_version"],
                        },
                    }
                    if expand_release
                    else {}
                ),
            },
        },
    }


def get_single_install_summary(raw_data: Any) -> Any:
    # TODO: Please compare me to node-sdk version
    """
    Builds summary data for an image install or gateway download

    """

    image = raw_data["image"][0]
    service = image["is_a_build_of__service"][0]
    release = None

    if "is_provided_by__release" in raw_data:
        release = raw_data["is_provided_by__release"][0]

    install = {
        "service_name": service["service_name"],
        "image_id": image["id"],
        "service_id": service["id"],
    }

    if release:
        install["commit"] = release["commit"]

    raw_data.pop("is_provided_by__release", None)
    raw_data.pop("image", None)
    install.update(raw_data)

    return install


def generate_current_service_details(raw_device: Any) -> Any:
    # TODO: Please compare me to node-sdk version
    grouped_services = defaultdict(list)

    for obj in [get_single_install_summary(i) for i in raw_device.get("image_install", [])]:
        grouped_services[obj.pop("service_name", None)].append(obj)

    raw_device["current_services"] = dict(grouped_services)
    raw_device["current_gateway_downloads"] = [
        get_single_install_summary(i) for i in raw_device.get("gateway_download", [])
    ]
    raw_device.pop("image_install", None)
    raw_device.pop("gateway_download", None)

    return raw_device


def is_provisioned(device: Any) -> bool:
    return (
        device.get("supervisor_version") is not None
        and len(device.get("supervisor_version")) > 0
        and device.get("last_connectivity_event") is not None
    )


def normalize_device_os_version(device: Any) -> Any:
    if device.get("os_version") is not None and len(device.get("os_version")) == 0 and is_provisioned(device):
        device["os_version"] = "Resin OS 1.0.0-pre"

    return device


T = TypeVar("T")


def with_supervisor_locked_error(fn: Callable[[], T]) -> T:
    try:
        return fn()
    except RequestError as e:
        if e.status_code == SUPERVISOR_LOCKED_STATUS_CODE:
            raise SupervisorLocked()
        raise e


def normalize_balena_semver(os_version: str) -> str:
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


def ensure_version_compatibility(
    version: str,
    min_version: str,
    version_type: Literal["supervisor", "host OS"],
) -> None:
    version = normalize_balena_semver(version)

    if version and Version.parse(version) < Version.parse(min_version):
        raise ValueError(f"Incompatible {version_type} version: {version} - must be >= {min_version}")


def get_device_os_semver_with_variant(os_version: str, os_variant: Optional[str] = None):
    if not os_version:
        return None

    version_info = Version.parse(normalize_balena_semver(os_version))

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

    return str(
        Version(
            version_info.major,
            version_info.minor,
            version_info.patch,
            version_info.prerelease,
            ".".join(builds),
        )
    )
