import binascii
import os
from datetime import datetime
from typing import Any, Callable, List, Optional, TypedDict, Union
from urllib.parse import urljoin

from semver.version import Version

from .. import exceptions
from ..auth import Auth
from ..balena_auth import request
from ..base_request import BaseRequest
from ..pine import pine
from ..resources import Message
from ..settings import Settings, settings
from ..types import AnyObject
from ..types.models import DeviceMetricsType, TypeDevice
from ..utils import (
    ensure_version_compatibility,
    generate_current_service_details,
    get_current_service_details_pine_expand,
    is_full_uuid,
    is_id,
    is_provisioned,
    merge,
    normalize_device_os_version,
)
from .application import Application, application
from .config import Config
from .device_os import DeviceOs, normalize_balena_semver
from .device_type import DeviceType
from .history import DeviceHistory
from .hup import Hup
from .organization import Organization
from .release import Release

LOCAL_MODE_MIN_OS_VERSION = "2.0.0"
LOCAL_MODE_MIN_SUPERVISOR_VERSION = "4.0.0"
LOCAL_MODE_ENV_VAR = "RESIN_SUPERVISOR_LOCAL_MODE"
OVERRIDE_LOCK_ENV_VAR = "RESIN_OVERRIDE_LOCK"
MIN_SUPERVISOR_MC_API = "7.0.0"
MIN_OS_MC = "2.12.0"


class LocationType(TypedDict):
    latitude: Union[str, int]
    longitude: Union[str, int]


class RegisterResponse(TypedDict):
    id: int
    uuid: str
    api_key: str


class LocalModeResponse(TypedDict):
    message: str
    supported: bool


class HUPStatusResponse(TypedDict):
    status: str
    lastRun: int
    action: str
    parameters: AnyObject


# TODO: support both device uuid and device id
class DeviceStatus:
    """
    Balena device statuses.
    """

    IDLE = "Idle"
    CONFIGURING = "Configuring"
    UPDATING = "Updating"
    OFFLINE = "Offline"
    POST_PROVISIONING = "Post Provisioning"
    INACTIVE = "Inactive"


class Device:
    """
    This class implements device model for balena python SDK.
    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.config = Config()
        self.settings = Settings()
        self.application = Application()
        self.auth = Auth()
        self.release = Release()
        self.device_os = DeviceOs()
        self.device_type = DeviceType()
        self.hup = Hup()
        self.history = DeviceHistory()
        self.organization = Organization()
        self.__local_mode_select = [
            "id",
            "os_version",
            "os_variant",
            "supervisor_version",
            "last_connectivity_event",
        ]

    def __upsert_device_config_variable(
        self, device_id: int, name: str, value: str
    ):
        pine.upsert(
            {
                "resource": "device_config_variable",
                "id": {"device": device_id, "name": name},
                "body": {"value": value},
            }
        )

    def __get_applied_device_config_variable_value(
        self, uuid_or_id: Union[str, int], name: str
    ):
        options = {
            "$expand": {
                "device_config_variable": {
                    "$select": "value",
                    "$filter": {"name": name},
                },
                "belongs_to__application": {
                    "$select": "id",
                    "$expand": {
                        "application_config_variable": {
                            "$select": "value",
                            "$filter": {"name": name},
                        }
                    },
                },
            }
        }

        result = self.get(uuid_or_id, options)

        device_config = next(iter(result["device_config_variable"]), None)
        app_config = next(
            iter(
                result["belongs_to__application"][0][
                    "application_config_variable"
                ]
            ),
            None,
        )

        if device_config is not None:
            return device_config.get("value")  # type: ignore

        if app_config is not None:
            return app_config.get("value")  # type: ignore

        return None

    def __set(
        self,
        uuid_or_id_or_ids: Union[str, int, List[int]],
        body: Any,
        fn: Callable = pine.patch,
    ) -> None:
        if isinstance(uuid_or_id_or_ids, (int, str)):
            is_potentially_full_uuid = is_full_uuid(uuid_or_id_or_ids)
            if is_potentially_full_uuid or is_id(uuid_or_id_or_ids):
                fn(
                    {
                        "resource": "device",
                        "id": uuid_or_id_or_ids
                        if is_id(uuid_or_id_or_ids)
                        else {"uuid": uuid_or_id_or_ids},
                        "body": body,
                    }
                )
            else:
                fn(
                    {
                        "resource": "device",
                        "options": {
                            "$filter": {
                                "uuid": {"$startswith": uuid_or_id_or_ids}
                            }
                        },
                        "body": body,
                    }
                )

        else:
            chunk_size = 200
            chunked_devices = [
                uuid_or_id_or_ids[i : i + chunk_size]  # noqa: E203
                for i in range(0, len(uuid_or_id_or_ids), chunk_size)
            ]
            for chunk in chunked_devices:
                fn(
                    {
                        "resource": "device",
                        "options": {"$filter": {"id": {"$in": chunk}}},
                        "body": body,
                    }
                )

    def __check_local_mode_supported(self, device: TypeDevice):
        if not is_provisioned(device):
            raise exceptions.LocalModeError(Message.DEVICE_NOT_PROVISIONED)

        if not (
            Version.parse(normalize_balena_semver(device["os_version"]))
            >= Version.parse(LOCAL_MODE_MIN_OS_VERSION)
        ):
            raise exceptions.LocalModeError(
                Message.DEVICE_OS_NOT_SUPPORT_LOCAL_MODE
            )

        if not (
            Version.parse(normalize_balena_semver(device["supervisor_version"]))
            >= Version.parse(LOCAL_MODE_MIN_SUPERVISOR_VERSION)
        ):
            raise exceptions.LocalModeError(
                Message.DEVICE_SUPERVISOR_NOT_SUPPORT_LOCAL_MODE
            )

        if device["os_variant"] != "dev":
            raise exceptions.LocalModeError(
                Message.DEVICE_OS_TYPE_NOT_SUPPORT_LOCAL_MODE
            )

    def __check_os_update_target(
        self, device_info: TypeDevice, target_os_version: str
    ):
        if "uuid" not in device_info or not device_info["uuid"]:
            raise exceptions.OsUpdateError(
                "The uuid of the device is not available"
            )

        uuid = device_info["uuid"]
        if "is_online" not in device_info or not device_info["is_online"]:
            raise exceptions.OsUpdateError(f"The device is offline: {uuid}")

        if "os_version" not in device_info or not device_info["os_version"]:
            raise exceptions.OsUpdateError(
                f"The current os version of the device is not available: {uuid}"
            )

        if (
            "is_of__device_type" not in device_info
            or not device_info["is_of__device_type"]
        ):
            raise exceptions.OsUpdateError(
                f"The device type of the device is not available: {uuid}"
            )

        if "os_variant" not in device_info:
            raise exceptions.OsUpdateError(
                f"The os variant of the device is not available: {uuid}"
            )

        current_os_version = self.device_os.get_device_os_semver_with_variant(
            device_info["os_version"], device_info["os_variant"]
        )

        self.hup.get_hup_action_type(
            device_info["is_of__device_type"][0]["slug"],
            current_os_version,
            target_os_version,
        )

    def get_dashboard_url(self, uuid: str):
        """
        Get balena Dashboard URL for a specific device.

        Args:
            uuid (str): device uuid.

        Examples:
            >>> balena.models.device.get_dashboard_url('19619a6317072b65a240b451f45f855d')
        """

        if not isinstance(uuid, str) or len(uuid) == 0:
            raise ValueError("Device UUID must be a non empty string")
        dashboard_url = settings.get("api_endpoint").replace("api", "dashboard")
        return urljoin(dashboard_url, f"/devices/{uuid}/summary")

    def get_all(self, options: AnyObject = {}) -> List[TypeDevice]:
        """
        This method returns all devices that the current user can access.
        In order to have the following computed properties in the result
        you have to explicitly define them in a `$select` in the extra options:
         - overall_status
         - overall_progress
         - is_frozen

         Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[TypeDevice]: list contains info of devices.

        Examples:
            >>> balena.models.device.get_all()
        """
        devices = pine.get(
            {
                "resource": "device",
                "options": merge({"$orderby": "device_name asc"}, options),
            }
        )

        return list(map(normalize_device_os_version, devices))

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[TypeDevice]:
        """
        Get devices by application slug, uuid or id.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[TypeDevice]: list contains info of devices.

        Examples:
            >>> balena.models.device.get_all_by_application('my_org/RPI1')
        """

        app = application.get(slug_or_uuid_or_id, {"$select": "id"})

        return self.get_all(
            merge(
                {"$filter": {"belongs_to__application": app["id"]}},
                options,
            )
        )

    def get_all_by_organization(
        self, handle_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[TypeDevice]:
        """
        Get devices by organization slug, uuid or id.

        Args:
            handle_or_id (Union[str, int]): organization handle (string) or id (number).
            options (AnyObject): extra pine options to use

        Returns:
            List[TypeDevice]: list contains info of devices.

        Examples:
            >>> balena.models.device.get_all_by_organization('my_org')
            >>> balena.models.device.get_all_by_organization(123)
        """
        org = self.organization.get(handle_or_id, {"$select": "id"})
        return self.get_all(
            merge(
                {
                    "$filter": {
                        "belongs_to__application": {
                            "$any": {
                                "$alias": "bta",
                                "$expr": {"bta": {"organization": org["id"]}},
                            }
                        }
                    }
                },
                options,
            )
        )

    def get(
        self, uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> TypeDevice:
        """
        This method returns a single device by id or uuid.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            options (AnyObject): extra pine options to use

        Returns:
            TypeDevice: device info.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.get('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            >>> balena.models.device.get('8deb12')
            >>> balena.models.device.get(12345)
        """

        if uuid_or_id is None:
            raise exceptions.DeviceNotFound(uuid_or_id)

        is_potentially_full_uuid = is_full_uuid(uuid_or_id)
        if is_potentially_full_uuid or is_id(uuid_or_id):
            device = pine.get(
                {
                    "resource": "device",
                    "id": {"uuid": uuid_or_id}
                    if is_potentially_full_uuid
                    else uuid_or_id,
                    "options": options,
                }
            )
        else:
            devices = pine.get(
                {
                    "resource": "device",
                    "options": merge(
                        {"$filter": {"uuid": {"$startswith": uuid_or_id}}},
                        options,
                    ),
                }
            )

            if len(devices) > 1:
                raise exceptions.AmbiguousDevice(uuid_or_id)
            try:
                device = devices[0]
            except IndexError:
                raise exceptions.DeviceNotFound(uuid_or_id)

        if device is None:
            raise exceptions.DeviceNotFound(uuid_or_id)

        return normalize_device_os_version(device)

    def get_with_service_details(
        self, uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> TypeDevice:
        """
        This method does not map exactly to the underlying model: it runs a
        larger prebuilt query, and reformats it into an easy to use and
        understand format. If you want more control, or to see the raw model
        directly, use `device.get(uuidOrId, options)` instead.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            options (AnyObject): extra pine options to use

        Returns:
            dict: device info with associated services details.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.get_with_service_details('0fcd753af396247e035de53b4e43eec3')
        """

        device = self.get(
            uuid_or_id,
            merge(
                {"$expand": get_current_service_details_pine_expand(True)},
                options,
            ),
        )

        return generate_current_service_details(device)

    def get_by_name(
        self, name: str, options: AnyObject = {}
    ) -> List[TypeDevice]:
        """
        Get devices by device name.

        Args:
            name (str): device name.

        Returns:
            List[TypeDevice]: list contains info of devices.

        Examples:
            >>> balena.models.device.get_by_name('floral-mountain')
        """

        devices = self.get_all(
            merge({"$filter": {"device_name": name}}, options)
        )

        if len(devices) == 0:
            raise exceptions.DeviceNotFound(name)

        return devices

    def get_name(self, uuid_or_id: Union[str, int]) -> str:
        """
        Get device name by device uuid.

        Args:
            uuid (str): device uuid (string) or id (int)

        Returns:
            str: device name.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        return self.get(uuid_or_id, {"$select": "device_name"})["device_name"]

    def get_application_name(self, uuid_or_id: Union[str, int]) -> str:
        """
        Get application name by device uuid.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            str: application name.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        device = self.get(uuid_or_id, {
            "$select": "id",
            "$expand": {"belongs_to__application": {"$select": "app_name"}},
        })
        return device["belongs_to__application"][0]["app_name"]

    def has(self, uuid_or_id: Union[str, int]) -> bool:
        """
        Check if a device exists.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            bool: True if device exists, False otherwise.
        """

        try:
            self.get(uuid_or_id, {"$select": ["id"]})
            return True
        except exceptions.DeviceNotFound:
            return False

    def is_online(self, uuid_or_id: Union[str, int]) -> bool:
        """
        Check if a device is online.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            bool: True if the device is online, False otherwise.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        return self.get(uuid_or_id, {"$select": "is_online"})["is_online"]

    def get_local_ip_address(self, uuid_or_id: Union[str, int]) -> List[str]:
        """
        Get the local IP addresses of a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            List[str]: IP addresses of a device.

        Raises:
            DeviceNotFound: if device couldn't be found.
            DeviceOffline: if device is offline.

        """

        device = self.get(uuid_or_id, {"$select": ["is_online", "ip_address"]})

        if not device.get("is_online"):
            raise exceptions.DeviceOffline(uuid_or_id)

        ip_address = device.get("ip_address")
        if ip_address is None:
            return []

        return ip_address.split(" ")

    def get_mac_address(self, uuid_or_id: Union[str, int]) -> List[str]:
        """
        Get the MAC addresses of a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            List[str]: MAC addresses of a device.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """
        device = self.get(uuid_or_id, {"$select": ["mac_address"]})

        mac = device.get("mac_address")
        if mac is None:
            return []

        return mac.split(" ")

    def get_metrics(self, uuid_or_id: Union[str, int]) -> DeviceMetricsType:
        """
        Gets the metrics related information for a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            dict: metrics of the device.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        metrics = [
            "memory_usage",
            "memory_total",
            "storage_block_device",
            "storage_usage",
            "storage_total",
            "cpu_usage",
            "cpu_temp",
            "cpu_id",
            "is_undervolted",
        ]
        device = self.get(uuid_or_id, {"$select": metrics})
        return {k: device.get(k, "") for k in metrics}  # type: ignore

    def remove(self, uuid_or_id_or_ids: Union[str, int, List[int]]):
        """
        Remove device(s).

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int])
        """

        self.__set(uuid_or_id_or_ids, body=None, fn=pine.delete)

    def deactivate(self, uuid_or_id_or_ids: Union[str, int, List[int]]) -> None:
        """
        Deactivates a device.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int])

        Examples:
            >>> balena.models.device.deactivate('44cc9d1861b9f992808c506276e5d31c')
            >>> balena.models.device.deactivate([123, 234])
        """
        self.__set(uuid_or_id_or_ids, {"is_active": False})

    def rename(self, uuid_or_id_or_ids: Union[str, int], new_name: str) -> None:
        """
        Renames a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (str) or id (int)
            new_name (str): device new name.

        Examples:
            >>> balena.models.device.rename(123, 'python-sdk-test-device')
        """
        self.__set(uuid_or_id_or_ids, {"device_name": new_name})

    def note(
        self, uuid_or_id_or_ids: Union[str, int, List[int]], note: str
    ) -> None:
        """
        Note a device.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int])
            note (str): device note.

        Examples:
            >>> balena.models.device.note(123, 'test note')
        """
        self.__set(uuid_or_id_or_ids, {"note": note})

    def set_custom_location(
        self,
        uuid_or_id_or_ids: Union[str, int, List[int]],
        location: LocationType,
    ) -> None:
        """
        Set a custom location for a device.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int])
            location (dict): device custom location { 'latitude': Union[int,, str], 'longitude': Union[int, str]}.

        Examples:
            >>> balena.models.device.set_custom_location(123, {'latitude': '21.032777','longitude': '105.831586'})
        """
        self.__set(
            uuid_or_id_or_ids,
            {
                "custom_latitude": str(location["latitude"]),
                "custom_longitude": str(location["longitude"]),
            },
        )

    def unset_custom_location(
        self, uuid_or_id_or_ids: Union[str, int, List[int]]
    ) -> None:
        """
        Clear the custom location of a device.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int])

        Examples:
            >>> balena.models.device.unset_custom_location(123)
        """

        self.set_custom_location(
            uuid_or_id_or_ids, {"latitude": "", "longitude": ""}
        )

    # TODO: enable device batching
    def move(
        self,
        uuid_or_id: Union[str, int],
        app_slug_or_uuid_or_id: Union[str, int],
    ):
        """
        Move a device to another application.

        Args:
            uuid_or_id (Union[str, int]): device uuid (str) or id (int).
            app_slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).

        Examples:
            >>> balena.models.device.move(123, 'RPI1Test')
        """
        application_options = {
            "$select": "id",
            "$expand": {
                "is_for__device_type": {
                    "$select": "is_of__cpu_architecture",
                    "$expand": {"is_of__cpu_architecture": {"$select": "slug"}},
                }
            },
        }

        app = self.application.get(app_slug_or_uuid_or_id, application_options)
        app_cpu_arch_slug = app["is_for__device_type"][0][
            "is_of__cpu_architecture"
        ][0]["slug"]

        device_options = {
            "$select": "is_of__device_type",
            "$expand": {
                "is_of__device_type": {
                    "$select": "is_of__cpu_architecture",
                    "$expand": {
                        "is_of__cpu_architecture": {
                            "$select": "slug",
                        }
                    },
                }
            },
        }

        device = self.get(uuid_or_id, device_options)
        device_cpu_arch_slug = device["is_of__device_type"][0][
            "is_of__cpu_architecture"
        ][0]["slug"]

        if not self.device_os.is_architecture_compatible_with(
            app_cpu_arch_slug, device_cpu_arch_slug
        ):
            raise exceptions.IncompatibleApplication(app_slug_or_uuid_or_id)

        self.__set(uuid_or_id, {"belongs_to__application": app["id"]})

    def identify(self, uuid_or_id: Union[str, int]) -> None:
        """
        Identify device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (str) or id (int).

        Examples:
            >>> balena.models.device.identify('8deb12a5')
        """

        device = self.get(uuid_or_id, {"$select": "uuid"})
        device_uuid = device["uuid"]

        request(
            method="POST",
            body={"uuid": device_uuid},
            path="/supervisor/v1/blink",
        )

    def restart_application(self, uuid_or_id: Union[str, int]):
        """
        This function restarts the Docker container running
        the application on the device, but doesn't reboot
        the device itself.

        Args:
            uuid_or_id (Union[str, int]): device uuid (str) or id (int).

        Examples:
            >>> balena.models.device.restart_application('8deb12a58')
            >>> balena.models.device.restart_application(1234)
        """

        device = self.get(
            uuid_or_id,
            {
                "$select": ["id", "supervisor_version"],
                "$expand": {"belongs_to__application": {"$select": "id"}},
            },
        )
        device_id = device["id"]

        if not Version.is_valid(device["supervisor_version"]) or (
            Version.parse(device["supervisor_version"]) < Version.parse("7.0.0")
        ):
            return request(
                method="POST",
                path=f"device/{device_id}/restart",
            )

        app_id = device["belongs_to__application"][0]["id"]
        return request(
            method="POST",
            path="/supervisor/v1/restart",
            body={
                "deviceId": device_id,
                "appId": app_id,
                "data": {
                    "appId": app_id,
                },
            },
        )

    def get_supervisor_state(self, uuid_or_id: Union[str, int]) -> Any:
        """
        Get the supervisor state on a device

        Args:
            uuid_or_id (Union[str, int]): device uuid (str) or id (int).

        Returns:
            dict: supervisor state.

        Examples:
            >>> balena.models.device.get_supervisor_state('b6070f4fea')
        """

        uuid = self.get(uuid_or_id, {"$select": "uuid"})["uuid"]

        response = request(
            method="POST",
            path="/supervisor/v1/device",
            body={"uuid": uuid, "method": "GET"},
        )

        if isinstance(response, dict):
            return response

        raise Exception(response)

    def get_supervisor_target_state(self, uuid_or_id: Union[str, int]) -> Any:
        """
        Get the supervisor target state on a device

        Args:
            uuid_or_id (Union[str, int]): device uuid (str) or id (int).

        Returns:
            DeviceStateType: supervisor target state.

        Examples:
            >>> balena.models.device.get_supervisor_target_state('b6070f4fea5edf808b576123157fe5ec')
        """
        device = self.get(uuid_or_id, {"$select": "uuid"})
        device_uuid = device["uuid"]

        return request(
            method="GET",
            path=f"/device/v2/{device_uuid}/state",
        )

    def generate_uuid(self) -> str:
        """
        Generate a random device UUID.

        Returns:
            str: a generated UUID.

        Examples:
            >>> balena.models.device.generate_uuid()
        """

        # From balena-sdk
        # I'd be nice if the UUID matched the output of a SHA-256 function,
        # but although the length limit of the CN attribute in a X.509
        # certificate is 64 chars, a 32 byte UUID (64 chars in hex) doesn't
        # pass the certificate validation in OpenVPN This either means that
        # the RFC counts a final NULL byte as part of the CN or that the
        # OpenVPN/OpenSSL implementation has a bug.
        return binascii.hexlify(os.urandom(31)).decode()

    def register(
        self,
        application_slug_or_uuid_or_id: Union[int, str],
        uuid: str,
        device_type_slug: Optional[str] = None,
    ) -> RegisterResponse:
        """
        Register a new device with a balena application.

        Args:
            application_slug_or_uuid_or_id (str): application slug (string), uuid (string) or id (number).
            uuid (str): device uuid.
            device_type_slug (Optional[str]): device type slug or alias.

        Returns:
            dict: dictionary contains device info.

        Examples:
            >>> device_uuid = balena.models.device.generate_uuid()
            >>> balena.models.device.register('RPI1',device_uuid)
        """

        device_type_options = {
            "$select": "slug",
            "$expand": {"is_of__cpu_architecture": {"$select": "slug"}},
        }

        application_options = {
            "$select": "id",
            "$expand": {"is_for__device_type": device_type_options},
        }

        # TODO: paralelize this 4 requests
        user_id = self.auth.get_user_id()
        api_key = self.application.generate_provisioning_key(
            application_slug_or_uuid_or_id
        )

        app = self.application.get(
            application_slug_or_uuid_or_id, application_options
        )
        if isinstance(device_type_slug, str):
            device_type = self.device_type.get(
                device_type_slug,
                {
                    "$select": "slug",
                    "$expand": {"is_of__cpu_architecture": {"$select": "slug"}},
                },
            )
        else:
            device_type = None

        if device_type is not None:
            is_compatible_parameter = (
                self.device_os.is_architecture_compatible_with(
                    device_type["is_of__cpu_architecture"][0]["slug"],
                    app["is_for__device_type"][0]["is_of__cpu_architecture"][0][
                        "slug"
                    ],
                )
            )

            if not is_compatible_parameter:
                app_type_slug = app["is_for__device_type"][0][
                    "is_of__cpu_architecture"
                ][0]["slug"]

                err_msg = f"{device_type_slug} is not compactible with application {app_type_slug} device typ"
                raise exceptions.InvalidDeviceType(err_msg)

            device_type = device_type["slug"]
        else:
            device_type = app["is_for__device_type"][0]["slug"]

        return request(  # type: ignore
            method="POST",
            path="/device/register",
            body={
                "user": user_id,
                "application": app["id"],
                "uuid": uuid,
                "device_type": device_type,
            },
            token=api_key,
        )

    # TODO: normalize response error code on no device for key response
    def generate_device_key(
        self,
        uuid_or_id: Union[str, int],
        name: Optional[str] = None,
        description: Optional[str] = None,
        expiry_date: Optional[str] = None,
    ) -> str:
        """
        Generate a device key.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            name (Optional[str]): device key name.
            description (Optional[str]): description for device key.
            expiry_date (Optional[str]): expiry date for device key, for example: `2030-01-01T00:00:00Z`.

        Examples:
            >>> balena.models.device.generate_device_key('df0926')
        """

        if is_id(uuid_or_id):
            device_id = uuid_or_id
        else:
            device_id = self.get(uuid_or_id, {"$select": "id"})["id"]

        return request(
            method="POST",
            path=f"/api-key/device/{device_id}/device-key",
            body={
                "name": name,
                "description": description,
                "expiryDate": expiry_date,
            },
        )

    def has_device_url(self, uuid_or_id: Union[str, int]) -> bool:
        """
        Check if a device is web accessible with device urls

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Examples:
            >>> balena.models.device.has_device_url('8deb12a')
        """

        return self.get(uuid_or_id, {"$select": "is_web_accessible"})[
            "is_web_accessible"
        ]

    def get_device_url(self, uuid_or_id: Union[str, int]) -> str:
        """
        Get a device url for a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Examples:
            >>> balena.models.device.get_device_url('8deb12a')
        """
        device = self.get(
            uuid_or_id, {"$select": ["uuid", "is_web_accessible"]}
        )
        if not device["is_web_accessible"]:
            raise exceptions.DeviceNotWebAccessible(uuid_or_id)

        device_url_base = self.config.get_all()["deviceUrlsBase"]  # type: ignore
        uuid = device["uuid"]
        return f"https://{uuid}.{device_url_base}"

    def enable_device_url(
        self, uuid_or_id_or_ids: Union[str, int, List[int]]
    ) -> None:
        """
        Enable device url for a device.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int]).

        Examples:
            >>> balena.models.device.enable_device_url('8deb12a58')
            >>> balena.models.device.enable_device_url([123, 345])
        """
        self.__set(uuid_or_id_or_ids, {"is_web_accessible": True})

    def disable_device_url(
        self, uuid_or_id_or_ids: Union[str, int, List[int]]
    ) -> None:
        """
        Disable device url for a device.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int]).

        Examples:
            >>> balena.models.device.disable_device_url('8deb12a58')
            >>> balena.models.device.disable_device_url([123, 345])
        """
        self.__set(uuid_or_id_or_ids, {"is_web_accessible": False})

    # TODO: refactor once config_var uses proper upsert
    def enable_local_mode(self, uuid_or_id: Union[str, int]) -> None:
        """
        Enable local mode.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Examples:
            >>> balena.models.device.enable_local_mode('b6070f4f')
        """

        device = self.get(uuid_or_id, {"$select": self.__local_mode_select})

        self.__check_local_mode_supported(device)
        self.__upsert_device_config_variable(
            device["id"], LOCAL_MODE_ENV_VAR, "1"
        )

    # TODO: refactor once config_var uses proper upsert
    def disable_local_mode(self, uuid_or_id: Union[str, int]) -> None:
        """
        Disable local mode.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            None.

        Examples:
            >>> balena.models.device.disable_local_mode('b6070f4f')
        """

        device = self.get(uuid_or_id, {"$select": "id"})
        self.__upsert_device_config_variable(
            device["id"], LOCAL_MODE_ENV_VAR, "0"
        )

    # TODO: refactor once config_var does the id checking
    def is_in_local_mode(self, uuid_or_id: Union[str, int]) -> bool:
        """
        Check if local mode is enabled on the device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            bool: True if local mode enabled, otherwise False.

        Examples:
            >>> balena.models.device.is_in_local_mode('b6070f4f')
        """

        device = self.get(uuid_or_id, {"$select": "id"})
        result = pine.get(
            {
                "resource": "device_config_variable",
                "id": {"device": device["id"], "name": LOCAL_MODE_ENV_VAR},
            }
        )

        return result is not None and result.get("value") == "1"

    def get_local_mode_support(
        self, uuid_or_id: Union[str, int]
    ) -> LocalModeResponse:
        """
        Returns whether local mode is supported and a message describing the reason why local mode is not supported.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            dict: local mode support information ({'supported': True/False, 'message': '...'}).

        Examples:
            >>> balena.models.device.get_local_mode_support('b6070f4')
        """

        device = self.get(uuid_or_id, {"$select": self.__local_mode_select})
        try:
            self.__check_local_mode_supported(device)
            return {"supported": True, "message": "Supported"}
        except exceptions.LocalModeError as e:
            return {"supported": False, "message": e.message}

    def enable_lock_override(self, uuid_or_id: Union[str, int]) -> None:
        """
        Enable lock override.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
        """

        device = self.get(uuid_or_id, {"$select": "id"})
        self.__upsert_device_config_variable(
            device["id"], OVERRIDE_LOCK_ENV_VAR, "1"
        )

    def disable_lock_override(self, uuid_or_id: Union[str, int]) -> None:
        """
        Disable lock override.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
        """

        device = self.get(uuid_or_id, {"$select": "id"})
        self.__upsert_device_config_variable(
            device["id"], OVERRIDE_LOCK_ENV_VAR, "0"
        )

    def has_lock_override(self, uuid_or_id: Union[str, int]) -> bool:
        """
        Check if a device has the lock override enabled.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            bool: lock override status.
        """

        return (
            self.__get_applied_device_config_variable_value(
                uuid_or_id, OVERRIDE_LOCK_ENV_VAR
            )
            == "1"
        )

    def get_status(self, uuid_or_id: Union[str, int]) -> str:
        """
        Get the status of a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            str: status of a device.

        Examples:
            >>> balena.models.device.get_status('8deb12')
        """

        return self.get(uuid_or_id, {"$select": "overall_status"})[
            "overall_status"
        ]

    def grant_support_access(
        self,
        uuid_or_id_or_ids: Union[str, int, List[int]],
        expiry_timestamp: int,
    ) -> None:
        """
        Grant support access to a device until a specified time.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int])
            expiry_timestamp (int): a timestamp in ms for when the support access will expire.

        Examples:
            >>> balena.models.device.grant_support_access('49b2a7', 1511974999000)
        """

        if expiry_timestamp is None or expiry_timestamp <= int(
            (datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds()
            * 1000
        ):
            raise exceptions.InvalidParameter(
                "expiry_timestamp", expiry_timestamp
            )

        self.__set(
            uuid_or_id_or_ids,
            {"is_accessible_by_support_until__date": expiry_timestamp},
        )

    def revoke_support_access(
        self, uuid_or_id_or_ids: Union[str, int, List[int]]
    ) -> None:
        """
        Revoke support access to a device.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int])

        Examples:
            >>> balena.models.device.revoke_support_access('49b2a7')
        """
        self.__set(
            uuid_or_id_or_ids,
            {"is_accessible_by_support_until__date": None},
        )

    def is_tracking_application_release(
        self, uuid_or_id: Union[str, int]
    ) -> bool:
        """
        Get whether the device is configured to track the current application release.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            bool: is tracking the current application release.
        """

        return not bool(
            self.get(uuid_or_id, {"$select": "should_be_running__release"})[
                "should_be_running__release"
            ]
        )

    # TODO: enable device batching
    def pin_to_release(
        self,
        uuid_or_id: Union[str, int],
        full_release_hash_or_id: Union[str, int],
    ) -> None:
        """
        Configures the device to run a particular release
        and not get updated when the current application release changes.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            full_release_hash_or_id (Union[str, int]) : the hash of a successful release (string) or id (number)

        Examples:
            >>> balena.models.device.set_to_release('49b2a', '45c90004de73557ded7274d4896a6db90ea61e36')
        """

        device = self.get(
            uuid_or_id,
            {
                "$select": "id",
                "$expand": {"belongs_to__application": {"$select": "id"}},
            },
        )
        app_id = device["belongs_to__application"][0]["id"]
        release_options = {
            "$top": 1,
            "$select": "id",
            "$filter": {
                "status": "success",
                "belongs_to__application": app_id,
            },
            "$orderby": "created_at desc",
        }
        if is_id(full_release_hash_or_id):
            release_options["$filter"]["id"] = full_release_hash_or_id
        else:
            release_options["$filter"]["commit"] = full_release_hash_or_id

        release = self.release.get(full_release_hash_or_id, release_options)
        pine.patch(
            {
                "resource": "device",
                "id": device["id"],
                "body": {"should_be_running__release": release["id"]},
            }
        )

    def track_application_release(
        self, uuid_or_id_or_ids: Union[str, int, List[int]]
    ) -> None:
        """
        Configure a specific device to track the current application release.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int])
        """

        self.__set(uuid_or_id_or_ids, {"should_be_running__release": None})

    # TODO: enable device batching
    def set_supervisor_release(
        self,
        uuid_or_id: Union[str, int],
        supervisor_version_or_id: Union[str, int],
    ) -> None:
        """
        Set a specific device to run a particular supervisor release.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            supervisor_version_or_id (Union[str, int]): the version of a released supervisor (string) or id (number)

        Examples:
            >>> balena.models.device.set_supervisor_release('f55dcdd9ad', 'v13.0.0')
        """
        device = self.get(
            uuid_or_id,
            {
                "$select": ["id", "supervisor_version", "os_version"],
                "$expand": {"is_of__device_type": {"$select": "slug"}},
            },
        )
        device_type_slug = device["is_of__device_type"][0]["slug"]

        release_options = {
            "$top": 1,
            "$select": "id",
            "$filter": {
                "is_for__device_type": {
                    "$any": {
                        "$alias": "dt",
                        "$expr": {
                            "dt": {
                                "slug": device_type_slug,
                            },
                        },
                    },
                },
            },
        }

        if is_id(supervisor_version_or_id):
            release_options["$filter"]["id"] = supervisor_version_or_id
        else:
            release_options["$filter"][
                "supervisor_version"
            ] = supervisor_version_or_id

        try:
            release = pine.get(
                {"resource": "supervisor_release", "options": release_options}
            )[0]
        except IndexError:
            raise Exception(
                f"Supervisor release not found {supervisor_version_or_id}"
            )

        ensure_version_compatibility(
            device["supervisor_version"], MIN_SUPERVISOR_MC_API, "supervisor"
        )
        ensure_version_compatibility(device["os_version"], MIN_OS_MC, "host OS")

        pine.patch(
            {
                "resource": "device",
                "id": device["id"],
                "body": {
                    "should_be_managed_by__supervisor_release": release["id"]
                },
            }
        )

    def start_os_update(
        self, uuid: str, target_os_version: str
    ) -> HUPStatusResponse:
        """
        Start an OS update on a device.

        Args:
            uuid (str): device uuid.
            target_os_version (str): semver-compatible version for the target device.
                Unsupported (unpublished) version will result in rejection.
                The version **must** be the exact version number, a "prod" variant
                and greater than the one running on the device.

        Returns:
            HUPStatusResponse: action response.

        Examples:
            >>> balena.models.device.start_os_update('b6070f4', '2.29.2+rev1.prod')
            >>> balena.models.device.start_os_update('b6070f4', '2.89.0+rev1')
        """

        if target_os_version is None or uuid is None:
            raise exceptions.InvalidParameter("target_os_version or UUID", None)

        device = self.get(
            uuid,
            {
                "$select": ["uuid", "is_online", "os_version", "os_variant"],
                "$expand": {"is_of__device_type": {"$select": "slug"}},
            },
        )

        self.__check_os_update_target(device, target_os_version)

        all_versions = self.device_os.get_available_os_versions(
            device["is_of__device_type"][0]["slug"]
        )
        if not [
            v for v in all_versions if target_os_version == v["raw_version"]
        ]:
            raise exceptions.InvalidParameter(
                "target_os_version", target_os_version
            )

        data = {"parameters": {"target_version": target_os_version}}

        url_base = self.config.get_all()["deviceUrlsBase"]  # type: ignore
        action_api_version = settings.get("device_actions_endpoint_version")

        return request(  # type: ignore
            method="POST",
            path=f"{device['uuid']}/{self.device_os.OS_UPDATE_ACTION_NAME}",
            body=data,
            endpoint=f"https://actions.{url_base}/{action_api_version}/",
        )

    def get_os_update_status(self, uuid) -> HUPStatusResponse:
        """
        Get the OS update status of a device.

        Args:
            uuid (str): device uuid.

        Returns:
            HUPStatusResponse: action response.

        Examples:
            >>> balena.models.device.get_os_update_status('b6070f4f')
        """

        device = self.get(uuid, {"$select": "uuid"})
        url_base = self.config.get_all()["deviceUrlsBase"]  # type: ignore
        action_api_version = settings.get("device_actions_endpoint_version")

        return request(  # type: ignore
            method="GET",
            path=f"{device['uuid']}/{self.device_os.OS_UPDATE_ACTION_NAME}",
            endpoint=f"https://actions.{url_base}/{action_api_version}/",
        )
