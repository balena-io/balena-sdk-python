import numbers
import re
from collections import defaultdict
from copy import deepcopy
from typing import Any, Callable, Dict, Literal, TypeVar

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


def merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries, with conflicts resolved in favor of dict2.
    """
    result = deepcopy(dict1)
    for key, value in dict2.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


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
    groupedServices = defaultdict(list)

    for obj in [
        get_single_install_summary(i)
        for i in raw_device.get("image_install", [])
    ]:
        groupedServices[obj.pop("service_name", None)].append(obj)

    raw_device["current_services"] = dict(groupedServices)
    raw_device["current_gateway_downloads"] = [
        get_single_install_summary(i)
        for i in raw_device.get("gateway_download", [])
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
    if (
        device.get("os_version") is not None
        and len(device.get("os_version")) == 0
        and is_provisioned(device)
    ):
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


def ensure_version_compatibility(
    version: str,
    min_version: str,
    version_type: Literal["supervisor", "host OS"],
) -> None:

    version = normalize_balena_semver(version)

    if version and Version.parse(version) < Version.parse(min_version):
        raise ValueError(
            f"Incompatible {version_type} version: {version} - must be >= {min_version}"
        )
