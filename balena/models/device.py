import binascii
import datetime
import os
from typing import Any, Callable, List, Optional, TypedDict, Union, cast
from urllib.parse import urljoin

from deprecated import deprecated
import requests
from semver.version import Version
from json.decoder import JSONDecodeError

from .. import exceptions
from ..auth import Auth
from ..balena_auth import request
from ..dependent_resource import DependentResource
from ..hup import get_hup_action_type
from ..pine import PineClient
from ..resources import Message
from ..settings import Settings
from ..types import AnyObject
from ..types.models import BaseTagType, DeviceMetricsType, EnvironmentVariableBase, TypeDevice, TypeDeviceWithServices
from ..utils import (
    ensure_version_compatibility,
    generate_current_service_details,
    get_current_service_details_pine_expand,
    get_device_os_semver_with_variant,
    is_full_uuid,
    is_id,
    is_provisioned,
    merge,
    with_supervisor_locked_error,
)
from .application import Application
from .config import Config
from .device_type import DeviceType
from .history import DeviceHistory
from .organization import Organization
from .os import DeviceOs, normalize_balena_semver
from .release import Release

LOCAL_MODE_MIN_OS_VERSION = "2.0.0"
LOCAL_MODE_MIN_SUPERVISOR_VERSION = "4.0.0"
LOCAL_MODE_ENV_VAR = "RESIN_SUPERVISOR_LOCAL_MODE"
OVERRIDE_LOCK_ENV_VAR = "RESIN_OVERRIDE_LOCK"
MIN_SUPERVISOR_MC_API = "7.0.0"
MIN_OS_MC = "2.12.0"
MIN_SUPERVISOR_APPS_API = "1.8.0-alpha.0"


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


class SupervisorStateType(TypedDict):
    api_port: str
    ip_address: str
    os_version: str
    supervisor_version: str
    update_pending: bool
    update_failed: bool
    update_downloaded: bool
    status: str
    commit: str
    download_progress: str


class Device:
    """
    This class implements device model for balena python SDK.
    """

    def __init__(self, pine: PineClient, settings: Settings):
        self.__pine = pine
        self.__settings = settings
        self.__config = Config(settings)
        self.__auth = Auth(pine, settings)
        self.__application = Application(pine, settings)
        self.__release = Release(pine, settings)
        self.__device_os = DeviceOs(pine, settings)
        self.__device_type = DeviceType(pine, settings)
        self.__organization = Organization(pine, settings)
        self.__LOCAL_MODE_SELECT = [
            "id",
            "os_version",
            "os_variant",
            "supervisor_version",
            "last_connectivity_event",
        ]

        self.tags = DeviceTag(pine, self, self.__application)
        self.config_var = DeviceConfigVariable(pine, self, self.__application)
        self.env_var = DeviceEnvVariable(pine, self, self.__application)
        self.service_var = DeviceServiceEnvVariable(pine, self, self.__application)
        self.history = DeviceHistory(pine, settings)

        self.__supervisor_address = os.environ.get("BALENA_SUPERVISOR_ADDRESS")
        self.__supervisor_api_key = os.environ.get("BALENA_SUPERVISOR_API_KEY")
        self.__on_device_app_id = os.environ.get("BALENA_APP_ID")
        self.__local_device_uuid = os.environ.get("BALENA_DEVICE_UUID")

        self.__on_device = all([self.__supervisor_address, self.__supervisor_api_key, self.__on_device_app_id])

    def __get_applied_device_config_variable_value(self, uuid_or_id: Union[str, int], name: str):
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
            iter(result["belongs_to__application"][0]["application_config_variable"]),
            None,
        )

        if device_config is not None:
            return device_config.get("value")

        if app_config is not None:
            return app_config.get("value")

        return None

    def __set(
        self,
        uuid_or_id_or_ids: Union[str, int, List[int]],
        body: Any,
        fn: Optional[Callable] = None,
    ) -> None:
        if fn is None:
            fn = self.__pine.patch

        if isinstance(uuid_or_id_or_ids, (int, str)):
            is_potentially_full_uuid = is_full_uuid(uuid_or_id_or_ids)
            if is_potentially_full_uuid or is_id(uuid_or_id_or_ids):
                fn(
                    {
                        "resource": "device",
                        "id": uuid_or_id_or_ids if is_id(uuid_or_id_or_ids) else {"uuid": uuid_or_id_or_ids},
                        "body": body,
                    }
                )
            else:
                if len(uuid_or_id_or_ids) < 6:
                    raise exceptions.InvalidParameter("UUID must have at least 6 characeters", None)

                affected = self.__pine.get({
                    "resource": "device",
                    "options": {
                        "$top": 2,
                        "$select": "id",
                        "$filter": {"uuid": {"$startswith": uuid_or_id_or_ids}}}
                    })
                if len(affected) > 1:
                    raise exceptions.AmbiguousDevice(uuid_or_id_or_ids)

                fn(
                    {
                        "resource": "device",
                        "options": {"$filter": {"uuid": {"$startswith": uuid_or_id_or_ids}}},
                        "body": body,
                    }
                )

        else:
            chunk_size = 200
            chunked_devices = [
                uuid_or_id_or_ids[i : i + chunk_size]  # noqa: E203 type: ignore
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
            Version.parse(normalize_balena_semver(device["os_version"])) >= Version.parse(LOCAL_MODE_MIN_OS_VERSION)
        ):
            raise exceptions.LocalModeError(Message.DEVICE_OS_NOT_SUPPORT_LOCAL_MODE)

        if not (
            Version.parse(normalize_balena_semver(device["supervisor_version"]))
            >= Version.parse(LOCAL_MODE_MIN_SUPERVISOR_VERSION)
        ):
            raise exceptions.LocalModeError(Message.DEVICE_SUPERVISOR_NOT_SUPPORT_LOCAL_MODE)

        if device["os_variant"] != "dev":
            raise exceptions.LocalModeError(Message.DEVICE_OS_TYPE_NOT_SUPPORT_LOCAL_MODE)

    def __check_os_update_target(self, device_info: TypeDevice, target_os_version: str):
        if "uuid" not in device_info or not device_info["uuid"]:
            raise exceptions.OsUpdateError("The uuid of the device is not available")

        uuid = device_info["uuid"]
        if "is_online" not in device_info or not device_info["is_online"]:
            raise exceptions.OsUpdateError(f"The device is offline: {uuid}")

        if "os_version" not in device_info or not device_info["os_version"]:
            raise exceptions.OsUpdateError(f"The current os version of the device is not available: {uuid}")

        if "is_of__device_type" not in device_info or not device_info["is_of__device_type"]:
            raise exceptions.OsUpdateError(f"The device type of the device is not available: {uuid}")

        if "os_variant" not in device_info:
            raise exceptions.OsUpdateError(f"The os variant of the device is not available: {uuid}")

        current_os_version = get_device_os_semver_with_variant(device_info["os_version"], device_info["os_variant"])

        get_hup_action_type(
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
        dashboard_url = cast(str, self.__settings.get("api_endpoint")).replace("api", "dashboard")
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
        devices = self.__pine.get(
            {
                "resource": "device",
                "options": merge({"$orderby": "device_name asc"}, options),
            }
        )

        return devices

    def get_all_by_application(self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}) -> List[TypeDevice]:
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

        app = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})

        return self.get_all(
            merge(
                {"$filter": {"belongs_to__application": app["id"]}},
                options,
            )
        )

    def get_all_by_organization(self, handle_or_id: Union[str, int], options: AnyObject = {}) -> List[TypeDevice]:
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
        org = self.__organization.get(handle_or_id, {"$select": "id"})
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

    def get(self, uuid_or_id: Union[str, int], options: AnyObject = {}) -> TypeDevice:
        """
        This method returns a single device by id or uuid.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            options (AnyObject): extra pine options to use

        Returns:
            TypeDevice: device info.

        Examples:
            >>> balena.models.device.get('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            >>> balena.models.device.get('8deb12')
            >>> balena.models.device.get(12345)
        """

        if uuid_or_id is None:
            raise exceptions.DeviceNotFound(uuid_or_id)

        if uuid_or_id == '':
            raise exceptions.InvalidParameter("UUID can not be empty", None)

        is_potentially_full_uuid = is_full_uuid(uuid_or_id)
        if is_potentially_full_uuid or is_id(uuid_or_id):
            device = self.__pine.get(
                {
                    "resource": "device",
                    "id": {"uuid": uuid_or_id} if is_potentially_full_uuid else uuid_or_id,
                    "options": options,
                }
            )
        else:
            devices = self.__pine.get(
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

        return device

    def get_with_service_details(self, uuid_or_id: Union[str, int], options: AnyObject = {}) -> TypeDeviceWithServices:
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

    def get_by_name(self, name: str, options: AnyObject = {}) -> List[TypeDevice]:
        """
        Get devices by device name.

        Args:
            name (str): device name.

        Returns:
            List[TypeDevice]: list contains info of devices.

        Examples:
            >>> balena.models.device.get_by_name('floral-mountain')
        """

        devices = self.get_all(merge({"$filter": {"device_name": name}}, options))

        if len(devices) == 0:
            raise exceptions.DeviceNotFound(name)

        return devices

    def get_name(self, uuid_or_id: Union[str, int]) -> str:
        """
        Get device name by device uuid.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            str: device name.

        """

        return self.get(uuid_or_id, {"$select": "device_name"})["device_name"]

    def get_application_name(self, uuid_or_id: Union[str, int]) -> str:
        """
        Get application name by device uuid.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            str: application name.
        """

        device = self.get(
            uuid_or_id,
            {
                "$select": "id",
                "$expand": {"belongs_to__application": {"$select": "app_name"}},
            },
        )
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
        """

        return self.get(uuid_or_id, {"$select": "is_online"})["is_online"]

    def get_local_ip_address(self, uuid_or_id: Union[str, int]) -> List[str]:
        """
        Get the local IP addresses of a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            List[str]: IP addresses of a device.
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
        return {k: device.get(k, "") for k in metrics}

    def remove(self, uuid_or_id_or_ids: Union[str, int, List[int]]):
        """
        Remove device(s).

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int])
        """
        self.__set(uuid_or_id_or_ids, body=None, fn=self.__pine.delete)

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

    def rename(self, uuid_or_id: Union[str, int], new_name: str) -> None:
        """
        Renames a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (str) or id (int)
            new_name (str): device new name.

        Examples:
            >>> balena.models.device.rename(123, 'python-sdk-test-device')
        """
        self.__set(uuid_or_id, {"device_name": new_name})

    def set_note(self, uuid_or_id_or_ids: Union[str, int, List[int]], note: str) -> None:
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

    def unset_custom_location(self, uuid_or_id_or_ids: Union[str, int, List[int]]) -> None:
        """
        Clear the custom location of a device.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int])

        Examples:
            >>> balena.models.device.unset_custom_location(123)
        """

        self.set_custom_location(uuid_or_id_or_ids, {"latitude": "", "longitude": ""})

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

        app = self.__application.get(app_slug_or_uuid_or_id, application_options)
        app_cpu_arch_slug = app["is_for__device_type"][0]["is_of__cpu_architecture"][0]["slug"]

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
        device_cpu_arch_slug = device["is_of__device_type"][0]["is_of__cpu_architecture"][0]["slug"]

        if not self.__device_os.is_architecture_compatible_with(app_cpu_arch_slug, device_cpu_arch_slug):
            raise exceptions.IncompatibleApplication(app_slug_or_uuid_or_id)

        self.__set(uuid_or_id, {"belongs_to__application": app["id"]})

    def __supervisor_request(self, method: str, path: str, body: Optional[AnyObject] = None):
        params = {"apikey": self.__supervisor_api_key}
        req = with_supervisor_locked_error(
            lambda: requests.request(
                method=method, url=urljoin(self.__supervisor_address, path), json=body, params=params  # type: ignore
            )
        )

        if req.ok:
            try:
                return req.json()
            except JSONDecodeError:
                return req.content.decode()
        else:
            raise exceptions.RequestError(body=req.content.decode(), status_code=req.status_code)

    def __should_run_on_device(self, uuid_or_id: Optional[Union[str, int]]) -> bool:
        return self.__on_device and (uuid_or_id is None or uuid_or_id == self.__local_device_uuid)

    def ping(self, uuid_or_id: Optional[Union[str, int]] = None) -> None:
        """
        Ping a device.
        This is useful to signal that the supervisor is alive and responding.

        Args:
            uuid_or_id (Optional[Union[str, int]]): device uuid (str) or id (int) or None for SDK running on device.

        Examples:
            >>> balena.models.device.ping('8f66ec7')
            >>> balena.models.device.ping(1234)
        """

        path = "/ping"
        if self.__should_run_on_device(uuid_or_id):
            self.__supervisor_request("GET", path)
            return

        if uuid_or_id is None:
            raise exceptions.LocalSupervisorNotFound()

        device_options = {
            "$select": "id",
            "$expand": {"belongs_to__application": {"$select": "id"}},
        }

        device = self.get(uuid_or_id, device_options)
        request(
            method="POST",
            path=f"/supervisor/{path}",
            settings=self.__settings,
            body={
                "method": "GET",
                "deviceId": device["id"],
                "appId": device["belongs_to__application"][0]["id"],
            },
        )

    def identify(self, uuid_or_id: Optional[Union[str, int]] = None) -> None:
        """
        Identify device.

        Args:
            uuid_or_id (Optional[Union[str, int]]): device uuid (str) or id (int) or None for SDK running on device.

        Examples:
            >>> balena.models.device.identify('8deb12a5')
        """

        path = "/v1/blink"
        if self.__should_run_on_device(uuid_or_id):
            self.__supervisor_request("POST", path)
            return

        if uuid_or_id is None:
            raise exceptions.LocalSupervisorNotFound()

        device = self.get(uuid_or_id, {"$select": "uuid"})
        device_uuid = device["uuid"]

        request(
            method="POST",
            settings=self.__settings,
            body={"uuid": device_uuid},
            path=f"/supervisor{path}",
        )

    def restart_application(self, uuid_or_id: Optional[Union[str, int]] = None) -> None:
        """
        This function restarts the Docker container running
        the application on the device, but doesn't reboot
        the device itself.

        Args:
            uuid_or_id (Optional[Union[str, int]]): device uuid (str) or id (int) or None for SDK running on device.

        Examples:
            >>> balena.models.device.restart_application('8deb12a58')
            >>> balena.models.device.restart_application(1234)
        """

        path = "/v1/restart"
        if self.__should_run_on_device(uuid_or_id):
            self.__supervisor_request("POST", path, {"appId": self.__on_device_app_id})
            return

        if uuid_or_id is None:
            raise exceptions.LocalSupervisorNotFound()

        restart_request = {
            "$select": ["id", "supervisor_version"],
            "$expand": {"belongs_to__application": {"$select": "id"}},
        }

        def __restart_application():
            device = self.get(uuid_or_id, restart_request)
            device_id = device["id"]

            if not Version.is_valid(device["supervisor_version"]) or (
                Version.parse(device["supervisor_version"]) < Version.parse("7.0.0")
            ):
                return request(
                    method="POST",
                    path=f"device/{device_id}/restart",
                    settings=self.__settings,
                )

            app_id = device["belongs_to__application"][0]["id"]

            return request(
                method="POST",
                path=f"/supervisor{path}",
                settings=self.__settings,
                body={
                    "deviceId": device_id,
                    "appId": app_id,
                    "data": {
                        "appId": app_id,
                    },
                },
            )

        with_supervisor_locked_error(__restart_application)

    def __should_force(self, force: bool):
        if not isinstance(force, bool):
            raise ValueError(f"The `force` flag must be of type bool, got {type(force)} instead.")

        should_force = {}
        if force:
            should_force = {"force": force}

        return should_force

    def reboot(self, uuid_or_id: Optional[Union[str, int]] = None, force: bool = False) -> None:
        """
        Reboot the device.

        Args:
            uuid_or_id (Optional[Union[str, int]]): device uuid (str) or id (int) or None for SDK running on device.
            force (Optional[bool]): If force is True, the update lock will be overridden.

        Examples:
            >>> balena.models.device.reboot('8f66ec7')
        """

        path = "/v1/reboot"
        should_force = self.__should_force(force)

        if self.__should_run_on_device(uuid_or_id):
            self.__supervisor_request("POST", path, should_force)
            return

        if uuid_or_id is None:
            raise exceptions.LocalSupervisorNotFound()

        def __reboot():
            device_id = uuid_or_id if is_id(uuid_or_id) else self.get(uuid_or_id, {"$select": "id"})["id"]

            return request(
                method="POST",
                path=f"/supervisor{path}",
                settings=self.__settings,
                body={"deviceId": device_id, "data": should_force},
            )

        with_supervisor_locked_error(__reboot)

    def shutdown(self, uuid_or_id: Optional[Union[str, int]] = None, force: bool = False) -> None:
        """
        Shutdown the device.

        Args:
            uuid_or_id (Optional[Union[str, int]]): device uuid (str) or id (int) or None for SDK running on device.
            force (Optional[bool]): If force is True, the update lock will be overridden.

        Examples:
            >>> balena.models.device.shutdown('8f66ec7')
        """

        path = "/v1/shutdown"
        should_force = self.__should_force(force)

        if self.__should_run_on_device(uuid_or_id):
            self.__supervisor_request("POST", path, should_force)
            return

        if uuid_or_id is None:
            raise exceptions.LocalSupervisorNotFound()

        def __shutdown():
            device = self.get(
                uuid_or_id,
                {
                    "$select": "id",
                    "$expand": {"belongs_to__application": {"$select": "id"}},
                },
            )

            return request(
                method="POST",
                path=f"/supervisor{path}",
                settings=self.__settings,
                body={
                    "deviceId": device["id"],
                    "appId": device["belongs_to__application"][0]["id"],
                    "data": should_force,
                },
            )

        with_supervisor_locked_error(__shutdown)

    def purge(self, uuid_or_id: Optional[Union[str, int]] = None) -> None:
        """
        Purge device.
        This function clears the user application's `/data` directory.

        Args:
            uuid_or_id (Optional[Union[str, int]]): device uuid (str) or id (int) or None for SDK running on device.

        Examples:
            >>> balena.models.device.purge('8f66ec7')
        """

        path = "/v1/purge"
        if self.__should_run_on_device(uuid_or_id):
            self.__supervisor_request("POST", path, {"appId": self.__on_device_app_id})
            return

        if uuid_or_id is None:
            raise exceptions.LocalSupervisorNotFound()

        def __purge():
            device = self.get(
                uuid_or_id,
                {
                    "$select": "id",
                    "$expand": {"belongs_to__application": {"$select": "id"}},
                },
            )

            app_id = device["belongs_to__application"][0]["id"]

            return request(
                method="POST",
                path=f"/supervisor{path}",
                settings=self.__settings,
                body={
                    "deviceId": device["id"],
                    "appId": app_id,
                    "data": {"appId": app_id},
                },
            )

        with_supervisor_locked_error(__purge)

    def update(self, uuid_or_id: Optional[Union[str, int]] = None, force: bool = False) -> None:
        """
        update the device.

        Args:
            uuid_or_id (Optional[Union[str, int]]): device uuid (str) or id (int) or None for SDK running on device.
            force (Optional[bool]): If force is True, the update lock will be overridden.

        Examples:
            >>> balena.models.device.update('8f66ec7')
        """

        path = "/v1/update"
        should_force = self.__should_force(force)

        if self.__should_run_on_device(uuid_or_id):
            self.__supervisor_request("POST", path, should_force)
            return

        if uuid_or_id is None:
            raise exceptions.LocalSupervisorNotFound()

        device = self.get(
            uuid_or_id,
            {
                "$select": "id",
                "$expand": {"belongs_to__application": {"$select": "id"}},
            },
        )

        return request(
            method="POST",
            path=f"/supervisor{path}",
            settings=self.__settings,
            body={
                "deviceId": device["id"],
                "appId": device["belongs_to__application"][0]["id"],
                "data": should_force,
            },
        )

    def get_supervisor_state(self, uuid_or_id: Optional[Union[str, int]] = None) -> SupervisorStateType:
        """
        Get the supervisor state on a device

        Args:
            uuid_or_id (Optional[Union[str, int]]): device uuid (str) or id (int) or None for SDK running on device.

        Returns:
            dict: supervisor state.

        Examples:
            >>> balena.models.device.get_supervisor_state('b6070f4fea')
        """

        path = "/v1/device"
        if self.__should_run_on_device(uuid_or_id):
            return self.__supervisor_request("GET", path)  # type: ignore

        if uuid_or_id is None:
            raise exceptions.LocalSupervisorNotFound()

        uuid = self.get(uuid_or_id, {"$select": "uuid"})["uuid"]

        response = request(
            method="POST",
            path=f"/supervisor{path}",
            settings=self.__settings,
            body={"uuid": uuid, "method": "GET"},
        )

        if isinstance(response, dict):
            return response

        raise Exception(response)

    def start_service(self, uuid_or_id: Optional[Union[str, int]], image_id: int) -> None:
        """
        Start a service on device.

        Args:
            uuid_or_id (Optional[Union[str, int]]): device uuid (str) or id (int) or None for SDK running on device.
            image_id (int): id of the image to start

        Examples:
            >>> balena.models.device.start_service('f3887b1', 1234)
            >>> balena.models.device.start_service(None, 1234)  # if running on the device
        """

        if self.__should_run_on_device(uuid_or_id):
            self.__supervisor_request(
                "POST", f"/v2/applications/{self.__on_device_app_id}/start-service", {"imageId": image_id}
            )
            return

        if uuid_or_id is None:
            raise exceptions.LocalSupervisorNotFound()

        device = self.get(
            uuid_or_id,
            {
                "$select": ["id", "supervisor_version"],
                "$expand": {"belongs_to__application": {"$select": "id"}},
            },
        )
        ensure_version_compatibility(device["supervisor_version"], MIN_SUPERVISOR_MC_API, "supervisor")
        app_id = device["belongs_to__application"][0]["id"]
        request(
            method="POST",
            path=f"/supervisor/v2/applications/{app_id}/start-service",
            settings=self.__settings,
            body={
                "deviceId": device["id"],
                "appId": app_id,
                "data": {"appId": app_id, "imageId": image_id},
            },
        )

    def stop_service(self, uuid_or_id: Optional[Union[str, int]], image_id: int) -> None:
        """
        Stop a service on device.

        Args:
            uuid_or_id (Optional[Union[str, int]]): device uuid (str) or id (int) or None for SDK running on device.
            image_id (int): id of the image to stop

        Examples:
            >>> balena.models.device.stop_service('f3887b1', 392229)
            >>> balena.models.device.stop_service(None, 392229)  # if running on the device
        """

        if self.__should_run_on_device(uuid_or_id):
            self.__supervisor_request(
                "POST", f"/v2/applications/{self.__on_device_app_id}/stop-service", {"imageId": image_id}
            )
            return

        if uuid_or_id is None:
            raise exceptions.LocalSupervisorNotFound()

        def __stop_service():
            device = self.get(
                uuid_or_id,
                {
                    "$select": ["id", "supervisor_version"],
                    "$expand": {"belongs_to__application": {"$select": "id"}},
                },
            )
            ensure_version_compatibility(
                device["supervisor_version"],
                MIN_SUPERVISOR_MC_API,
                "supervisor",
            )
            app_id = device["belongs_to__application"][0]["id"]
            request(
                method="POST",
                path=f"/supervisor/v2/applications/{app_id}/stop-service",
                settings=self.__settings,
                body={
                    "deviceId": device["id"],
                    "appId": app_id,
                    "data": {"appId": app_id, "imageId": image_id},
                },
            )

        with_supervisor_locked_error(__stop_service)

    def restart_service(self, uuid_or_id: Optional[Union[str, int]], image_id: int) -> None:
        """
        Restart a service on device.

        Args:
            uuid_or_id (Optional[Union[str, int]]): device uuid (str) or id (int) or None for SDK running on device.
            image_id (int): id of the image to restart

        Examples:
            >>> balena.models.device.restart_service('f3887b', 392229)
            >>> balena.models.device.restart_service(None, 392229)  # if running on the device

        """

        if self.__should_run_on_device(uuid_or_id):
            self.__supervisor_request(
                "POST", f"/v2/applications/{self.__on_device_app_id}/restart-service", {"imageId": image_id}
            )
            return

        if uuid_or_id is None:
            raise exceptions.LocalSupervisorNotFound()

        def __restart_service():
            device = self.get(
                uuid_or_id,
                {
                    "$select": ["id", "supervisor_version"],
                    "$expand": {"belongs_to__application": {"$select": "id"}},
                },
            )
            ensure_version_compatibility(
                device["supervisor_version"],
                MIN_SUPERVISOR_MC_API,
                "supervisor",
            )
            app_id = device["belongs_to__application"][0]["id"]
            request(
                method="POST",
                path=f"/supervisor/v2/applications/{app_id}/restart-service",
                settings=self.__settings,
                body={
                    "deviceId": device["id"],
                    "appId": app_id,
                    "data": {"appId": app_id, "imageId": image_id},
                },
            )

        with_supervisor_locked_error(__restart_service)

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
            settings=self.__settings,
            path=f"/device/v2/{device_uuid}/state",
        )

    def get_supervisor_target_state_for_app(
        self, slug_or_uuid_or_id: Union[str, int], release: Optional[Union[str, int]] = None
    ) -> Any:
        """
        Get the supervisor target state on a device

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
             release (Optional[Union[str, int]]): (optional) release uuid (default tracked)
        Returns:
            DeviceStateType: supervisor target state.

        Examples:
            >>> balena.models.device.get_supervisor_target_state_for_app('myorg/myapp')
        """
        uuid = self.__application.get(slug_or_uuid_or_id, {"$select": "uuid"})["uuid"]

        path = f"/device/v3/fleet/{uuid}/state/?releaseUuid="
        if release:
            path += str(release)

        return request(method="GET", settings=self.__settings, path=path)

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
            application_slug_or_uuid_or_id (Union[int, str]): application slug (string), uuid (string) or id (number).
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
        user_id = self.__auth.get_user_info()["id"]
        api_key = self.__application.generate_provisioning_key(application_slug_or_uuid_or_id)

        app = self.__application.get(application_slug_or_uuid_or_id, application_options)
        if isinstance(device_type_slug, str):
            device_type = self.__device_type.get(
                device_type_slug,
                {
                    "$select": "slug",
                    "$expand": {"is_of__cpu_architecture": {"$select": "slug"}},
                },
            )
        else:
            device_type = None

        if device_type is not None:
            is_compatible_parameter = self.__device_os.is_architecture_compatible_with(
                device_type["is_of__cpu_architecture"][0]["slug"],
                app["is_for__device_type"][0]["is_of__cpu_architecture"][0]["slug"],
            )

            if not is_compatible_parameter:
                app_type_slug = app["is_for__device_type"][0]["is_of__cpu_architecture"][0]["slug"]

                err_msg = f"{device_type_slug} is not compactible with application {app_type_slug} device typ"
                raise exceptions.InvalidDeviceType(err_msg)

            device_type = device_type["slug"]
        else:
            device_type = app["is_for__device_type"][0]["slug"]

        return request(
            method="POST",
            path="/device/register",
            settings=self.__settings,
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
            settings=self.__settings,
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

        return self.get(uuid_or_id, {"$select": "is_web_accessible"})["is_web_accessible"]

    def get_device_url(self, uuid_or_id: Union[str, int]) -> str:
        """
        Get a device url for a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Examples:
            >>> balena.models.device.get_device_url('8deb12a')
        """
        device = self.get(uuid_or_id, {"$select": ["uuid", "is_web_accessible"]})
        if not device["is_web_accessible"]:
            raise exceptions.DeviceNotWebAccessible(uuid_or_id)

        device_url_base = self.__config.get_all()["deviceUrlsBase"]
        uuid = device["uuid"]
        return f"https://{uuid}.{device_url_base}"

    def enable_device_url(self, uuid_or_id_or_ids: Union[str, int, List[int]]) -> None:
        """
        Enable device url for a device.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int]).

        Examples:
            >>> balena.models.device.enable_device_url('8deb12a58')
            >>> balena.models.device.enable_device_url([123, 345])
        """
        self.__set(uuid_or_id_or_ids, {"is_web_accessible": True})

    def disable_device_url(self, uuid_or_id_or_ids: Union[str, int, List[int]]) -> None:
        """
        Disable device url for a device.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int]).

        Examples:
            >>> balena.models.device.disable_device_url('8deb12a58')
            >>> balena.models.device.disable_device_url([123, 345])
        """
        self.__set(uuid_or_id_or_ids, {"is_web_accessible": False})

    def enable_local_mode(self, uuid_or_id: Union[str, int]) -> None:
        """
        Enable local mode.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Examples:
            >>> balena.models.device.enable_local_mode('b6070f4f')
        """

        device = self.get(uuid_or_id, {"$select": self.__LOCAL_MODE_SELECT})
        self.__check_local_mode_supported(device)
        self.config_var.set(uuid_or_id, LOCAL_MODE_ENV_VAR, "1")

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
        self.config_var.set(uuid_or_id, LOCAL_MODE_ENV_VAR, "0")

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
        result = self.__pine.get(
            {
                "resource": "device_config_variable",
                "id": {"device": device["id"], "name": LOCAL_MODE_ENV_VAR},
            }
        )

        return result is not None and result.get("value") == "1"

    def get_local_mode_support(self, uuid_or_id: Union[str, int]) -> LocalModeResponse:
        """
        Returns whether local mode is supported and a message describing the reason why local mode is not supported.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            dict: local mode support information ({'supported': True/False, 'message': '...'}).

        Examples:
            >>> balena.models.device.get_local_mode_support('b6070f4')
        """

        device = self.get(uuid_or_id, {"$select": self.__LOCAL_MODE_SELECT})
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
        self.config_var.set(uuid_or_id, OVERRIDE_LOCK_ENV_VAR, "1")

    def disable_lock_override(self, uuid_or_id: Union[str, int]) -> None:
        """
        Disable lock override.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
        """
        self.config_var.set(uuid_or_id, OVERRIDE_LOCK_ENV_VAR, "0")

    def has_lock_override(self, uuid_or_id: Union[str, int]) -> bool:
        """
        Check if a device has the lock override enabled.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            bool: lock override status.
        """

        return self.__get_applied_device_config_variable_value(uuid_or_id, OVERRIDE_LOCK_ENV_VAR) == "1"

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

        return self.get(uuid_or_id, {"$select": "overall_status"})["overall_status"]

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
            (datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(0)).total_seconds() * 1000
        ):
            raise exceptions.InvalidParameter("expiry_timestamp", expiry_timestamp)

        self.__set(
            uuid_or_id_or_ids,
            {"is_accessible_by_support_until__date": expiry_timestamp},
        )

    def revoke_support_access(self, uuid_or_id_or_ids: Union[str, int, List[int]]) -> None:
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

    def is_tracking_application_release(self, uuid_or_id: Union[str, int]) -> bool:
        """
        Get whether the device is configured to track the current application release.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Returns:
            bool: is tracking the current application release.
        """

        return not bool(self.get(uuid_or_id, {"$select": "is_pinned_on__release"})["is_pinned_on__release"])

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

        release = self.__release.get(full_release_hash_or_id, release_options)
        self.__pine.patch(
            {
                "resource": "device",
                "id": device["id"],
                "body": {"is_pinned_on__release": release["id"]},
            }
        )

    def track_application_release(self, uuid_or_id_or_ids: Union[str, int, List[int]]) -> None:
        """
        Configure a specific device to track the current application release.

        Args:
            uuid_or_id_or_ids (Union[str, int, List[int]]): device uuid (str) or id (int) or ids (List[int])
        """

        self.__set(uuid_or_id_or_ids, {"is_pinned_on__release": None})

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
                "$expand": {"is_of__device_type": {"$select": "is_of__cpu_architecture"}},
            },
        )
        cpu_arch_id = device["is_of__device_type"][0]["is_of__cpu_architecture"]["__id"]

        release_options = {
            "$top": 1,
            "$select": "id",
            "$filter": {"id" if is_id(supervisor_version_or_id) else "raw_version": supervisor_version_or_id},
        }

        try:
            release = self.__device_os.get_supervisor_releases_for_cpu_architecture(cpu_arch_id, release_options)[0]
        except IndexError:
            raise Exception(f"Supervisor release not found {supervisor_version_or_id}")

        ensure_version_compatibility(device["supervisor_version"], MIN_SUPERVISOR_MC_API, "supervisor")
        ensure_version_compatibility(device["os_version"], MIN_OS_MC, "host OS")
        self.__pine.patch(
            {
                "resource": "device",
                "id": device["id"],
                "body": {"should_be_managed_by__release": release["id"]},
            }
        )

    def start_os_update(
        self,
        uuid_or_id: Union[str, int],
        target_os_version: str,
        *,  # Force keyword arguments after this point
        run_detached: Optional[bool] = False
    ) -> HUPStatusResponse:
        """
        Start an OS update on a device.

        If using run_detached option, monitor progress with device.get() --
        status, provisioning_state and provisioning_progress entries.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int).
            target_os_version (str): semver-compatible version for the target device.
                Unsupported (unpublished) version will result in rejection.
                The version **must** be the exact version number, a "prod" variant
                and greater than the one running on the device.
            run_detached (Optional[bool]): run the update in detached mode.
                Default behaviour is run_detached=False but is DEPRECATED and will be
                removed in a future release. Use run_detached=True for more reliable updates.

        Returns:
            HUPStatusResponse: action response.

        Examples:
            >>> balena.models.device.start_os_update('b6070f4', '2.29.2+rev1.prod')
            >>> balena.models.device.start_os_update('b6070f4', '2.89.0+rev1')
            >>> balena.models.device.start_os_update('b6070f4', '2.89.0+rev1', run_detached=True)
        """

        if target_os_version is None or uuid_or_id is None:
            raise exceptions.InvalidParameter("target_os_version or UUID", None)

        device = self.get(
            uuid_or_id,
            {
                "$select": ["uuid", "is_online", "os_version", "os_variant"],
                "$expand": {"is_of__device_type": {"$select": "slug"}},
            },
        )

        self.__check_os_update_target(device, target_os_version)

        all_versions = self.__device_os.get_available_os_versions(device["is_of__device_type"][0]["slug"])
        if not [v for v in all_versions if target_os_version == v["raw_version"]]:
            raise exceptions.InvalidParameter("target_os_version", target_os_version)

        data = {"parameters": {"target_version": target_os_version}}

        url_base = self.__config.get_all()["deviceUrlsBase"]
        if not isinstance(run_detached, bool):
            raise ValueError(f"run_detached must be True or False, got {type(run_detached)}: {run_detached}")
        action_api_version = "v2" if run_detached is True else self.__settings.get("device_actions_endpoint_version")

        return request(
            method="POST",
            settings=self.__settings,
            path=f"{device['uuid']}/{self.__device_os.OS_UPDATE_ACTION_NAME}",
            body=data,
            endpoint=f"https://actions.{url_base}/{action_api_version}/",
        )

    @deprecated(
        """
        This will be removed in a future major release. This will no longer return a
        useful status for runDetached=true updates.
        """
    )
    def get_os_update_status(self, uuid_or_id: Union[str, int]) -> HUPStatusResponse:
        """
        ***Deprecated***
        Get the OS update status of a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int).

        Returns:
            HUPStatusResponse: action response.

        Examples:
            >>> balena.models.device.get_os_update_status('b6070f4f')
        """

        device = self.get(uuid_or_id, {"$select": "uuid"})
        url_base = self.__config.get_all()["deviceUrlsBase"]
        action_api_version = self.__settings.get("device_actions_endpoint_version")

        return request(
            method="GET",
            settings=self.__settings,
            path=f"{device['uuid']}/{self.__device_os.OS_UPDATE_ACTION_NAME}",
            endpoint=f"https://actions.{url_base}/{action_api_version}/",
        )

    @deprecated("This is not supported on multicontainer devices, and will be removed in a future major release")
    def get_application_info(self, uuid_or_id: Union[str, int]) -> Any:
        """
        ***Deprecated***
        Return information about the application running on the device.
        This function requires supervisor v1.8 or higher.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int).

        Returns:
            dict: dictionary contains application information.

        Examples:
            >>> balena.models.device.get_application_info('7f66ec')
        """

        device = self.get(
            uuid_or_id,
            {
                "$select": ["id", "supervisor_version"],
                "$expand": {"belongs_to__application": {"$select": "id"}},
            },
        )

        ensure_version_compatibility(device["supervisor_version"], MIN_SUPERVISOR_APPS_API, "supervisor")
        app_id = device["belongs_to__application"][0]["id"]

        return request(
            method="POST",
            path=f"/supervisor/v1/apps/{app_id}",
            settings=self.__settings,
            body={"deviceId": device["id"], "appId": app_id, "method": "GET"},
        )

    @deprecated("This is not supported on multicontainer devices, and will be removed in a future major release")
    def start_application(self, uuid_or_id: Union[str, int]) -> None:
        """
        ***Deprecated***
        Starts a user application container, usually after it has been stopped with `stop_application()`.
        This function requires supervisor v1.8 or higher.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int).

        Returns:
            dict: dictionary contains started application container id.

        Examples:
            >>> balena.models.device.start_application('8f66ec7')
        """

        device = self.get(
            uuid_or_id,
            {
                "$select": ["id", "supervisor_version"],
                "$expand": {"belongs_to__application": {"$select": "id"}},
            },
        )

        ensure_version_compatibility(device["supervisor_version"], MIN_SUPERVISOR_APPS_API, "supervisor")
        app_id = device["belongs_to__application"][0]["id"]
        request(
            method="POST",
            path=f"/supervisor/v1/apps/{app_id}/start",
            settings=self.__settings,
            body={
                "deviceId": device["id"],
                "appId": app_id,
            },
        )

    @deprecated("This is not supported on multicontainer devices, and will be removed in a future major release")
    def stop_application(self, uuid_or_id: Union[str, int]):
        """
        ***Deprecated***
        Temporarily stops a user application container.
        Application container will not be removed after invoking this function and a
        reboot or supervisor restart will cause the container to start again.
        This function requires supervisor v1.8 or higher.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int).

        Returns:
            dict: dictionary contains stopped application container id.

        Examples:
            >>> balena.models.device.stop_application('8f66ec')
        """

        def __stop_aplication():
            device = self.get(
                uuid_or_id,
                {
                    "$select": ["id", "supervisor_version"],
                    "$expand": {"belongs_to__application": {"$select": "id"}},
                },
            )

            ensure_version_compatibility(
                device["supervisor_version"],
                MIN_SUPERVISOR_APPS_API,
                "supervisor",
            )
            app_id = device["belongs_to__application"][0]["id"]
            request(
                method="POST",
                path=f"/supervisor/v1/apps/{app_id}/stop",
                settings=self.__settings,
                body={
                    "deviceId": device["id"],
                    "appId": app_id,
                },
            )

        with_supervisor_locked_error(__stop_aplication)


class DeviceTag(DependentResource[BaseTagType]):
    """
    This class implements device tag model for balena python SDK.

    """

    def __init__(self, pine: PineClient, device: Device, application: Application):
        self.__device = device
        self.__application = application
        super(DeviceTag, self).__init__(
            "device_tag", "tag_key", "device", lambda id: self.__device.get(id, {"$select": "id"})["id"], pine
        )

    def get_all_by_application(self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}) -> List[BaseTagType]:
        """
        Get all device tags for an application.

        Args:
            slug_or_uuid_or_id (int): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.device.tags.get_all_by_application(1005160)
        """

        app_id = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]
        return super(DeviceTag, self)._get_all(
            merge(
                {
                    "$filter": {
                        "device": {
                            "$any": {
                                "$alias": "d",
                                "$expr": {"d": {"belongs_to__application": app_id}},
                            }
                        }
                    }
                },
                options,
            )
        )

    def get_all_by_device(self, uuid_or_id: Union[str, int], options: AnyObject = {}) -> List[BaseTagType]:
        """
        Get all device tags for a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.device.tags.get_all_by_device('a03ab646c')
        """

        id = self.__device.get(uuid_or_id, {"$select": "id"})["id"]
        return super(DeviceTag, self)._get_all_by_parent(id, options)

    def get_all(self, options: AnyObject = {}) -> List[BaseTagType]:
        """
        Get all device tags.

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.device.tags.get_all()
        """

        return super(DeviceTag, self)._get_all(options)

    def get(self, uuid_or_id: Union[str, int], tag_key: str) -> Optional[str]:
        """
        Get a device tag (update tag value if it exists).
        ___Note___: Notice that when using the device ID rather than UUID,
        it will avoid one extra API roundtrip.

        Args:
            uuid_or_id (Union[str, int]): device uuid or device id.
            tag_key (str): tag key.

        Returns:
            Optional[str]: tag value

        Examples:
            >>> balena.models.device.tags.get('f5213eac0d63ac4', 'testtag')
        """

        # Trying to avoid an extra HTTP request
        # when the provided parameter looks like an id.
        # Note that this throws an exception for missing names/uuids,
        # but not for missing ids
        device_id = uuid_or_id if is_id(uuid_or_id) else self.__device.get(uuid_or_id, {"$select": "id"})["id"]
        return super(DeviceTag, self)._get(device_id, tag_key)

    def set(self, uuid_or_id: Union[str, int], tag_key: str, value: str) -> None:
        """
        Set a device tag (update tag value if it exists).
        ___Note___: Notice that when using the device ID rather than UUID,
        it will avoid one extra API roundtrip.

        Args:
            uuid_or_id (Union[str, int]): device uuid or device id.
            tag_key (str): tag key.
            value (str): tag value.

        Examples:
            >>> balena.models.device.tags.set('f5213eac0d63ac4', 'testtag', 'test1')
            >>> balena.models.device.tags.set('f5213eac0d63ac4', 'testtag', 'test2')
        """

        # Trying to avoid an extra HTTP request
        # when the provided parameter looks like an id.
        # Note that this throws an exception for missing names/uuids,
        # but not for missing ids
        device_id = uuid_or_id if is_id(uuid_or_id) else self.__device.get(uuid_or_id, {"$select": "id"})["id"]
        super(DeviceTag, self)._set(device_id, tag_key, value)

    def remove(self, uuid_or_id: Union[str, int], tag_key: str) -> None:
        """
        Remove a device tag.

        Args:
            uuid_or_id (Union[str, int]): device uuid or device id.
            tag_key (str): tag key.

        Examples:
            >>> balena.models.device.tags.remove('f5213eac0d63ac477', 'testtag')
        """

        device_id = uuid_or_id if is_id(uuid_or_id) else self.__device.get(uuid_or_id, {"$select": "id"})["id"]
        super(DeviceTag, self)._remove(device_id, tag_key)


class DeviceConfigVariable(DependentResource[EnvironmentVariableBase]):
    """
    This class implements device config variable model for balena python SDK.

    """

    def __init__(self, pine: PineClient, device: Device, application: Application):
        self.__device = device
        self.__application = application
        super(DeviceConfigVariable, self).__init__(
            "device_config_variable", "name", "device", lambda id: self.__device.get(id, {"$select": "id"})["id"], pine
        )

    def get_all_by_device(self, uuid_or_id: Union[str, int], options: AnyObject = {}) -> List[EnvironmentVariableBase]:
        """
        Get all device config variables belong to a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: device config variables.

        Examples:
            >>> balena.models.device.config_var.get_all_by_device('f5213ea')
        """
        return super(DeviceConfigVariable, self)._get_all_by_parent(uuid_or_id, options)

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[EnvironmentVariableBase]:
        """
        Get all device config variables for an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: list of device environment variables.

        Examples:
            >>> balena.models.device.config_var.device.get_all_by_application(5780)
        """
        app_id = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]
        return super(DeviceConfigVariable, self)._get_all(
            merge(
                {
                    "$filter": {
                        "device": {
                            "$any": {
                                "$alias": "d",
                                "$expr": {
                                    "d": {
                                        "belongs_to__application": app_id,
                                    },
                                },
                            },
                        },
                    },
                    "$orderby": "name asc",
                },
                options,
            )
        )

    def get(self, uuid_or_id: Union[str, int], env_var_name: str) -> Optional[str]:
        """
        Get a device config variable.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            env_var_name (str): environment variable name.

        Examples:
            >>> balena.models.device.config_var.device.get('8deb12','test_env4')
        """
        return super(DeviceConfigVariable, self)._get(uuid_or_id, env_var_name)

    def set(self, uuid_or_id: Union[str, int], env_var_name: str, value: str) -> None:
        """
        Set the value of a device config variable.
        Note that config variables must start with BALENA_ and RESIN_ prefixes.
        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Examples:
            >>> balena.models.device.config_var.set('8deb12','BALENA_test_env4', 'testing1')
        """
        super(DeviceConfigVariable, self)._set(uuid_or_id, env_var_name, value)

    def remove(self, uuid_or_id: Union[str, int], key: str) -> None:
        """
        Remove a device environment variable.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            key (str): environment variable name.

        Examples:
            >>> balena.models.device.config_var.device.remove(2184, 'test_env4')
        """
        super(DeviceConfigVariable, self)._remove(uuid_or_id, key)


class DeviceEnvVariable(DependentResource[EnvironmentVariableBase]):
    """
    This class implements device environment variable model for balena python SDK.

    """

    def __init__(self, pine: PineClient, device: Device, application: Application):
        self.__device = device
        self.__application = application
        super(DeviceEnvVariable, self).__init__(
            "device_environment_variable",
            "name",
            "device",
            lambda id: self.__device.get(id, {"$select": "id"})["id"],
            pine,
        )

    def get_all_by_device(self, uuid_or_id: Union[str, int], options: AnyObject = {}) -> List[EnvironmentVariableBase]:
        """
        Get all device environment variables.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: device environment variables.

        Examples:
            >>> balena.models.device.env_var.get_all_by_device('8deb12a')
        """
        return super(DeviceEnvVariable, self)._get_all_by_parent(uuid_or_id, options)

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[EnvironmentVariableBase]:
        """
        Get all device environment variables for an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: list of device environment variables.

        Examples:
            >>> balena.models.device.env_var.get_all_by_application(5780)
        """
        app_id = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]
        return super(DeviceEnvVariable, self)._get_all(
            merge(
                {
                    "$filter": {
                        "device": {
                            "$any": {
                                "$alias": "d",
                                "$expr": {
                                    "d": {
                                        "belongs_to__application": app_id,
                                    },
                                },
                            },
                        },
                    },
                    "$orderby": "name asc",
                },
                options,
            )
        )

    def get(self, uuid_or_id: Union[str, int], env_var_name: str) -> Optional[str]:
        """
        Get device environment variable.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            env_var_name (str): environment variable name.

        Examples:
            >>> balena.models.device.env_var.get('8deb12', 'test_env4')
        """
        return super(DeviceEnvVariable, self)._get(uuid_or_id, env_var_name)

    def set(self, uuid_or_id: Union[str, int], env_var_name: str, value: str) -> None:
        """
        Set the value of a specific environment variable.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Examples:
            >>> balena.models.device.env_var.set('8deb12', 'test_env4', 'testing1')
        """
        super(DeviceEnvVariable, self)._set(uuid_or_id, env_var_name, value)

    def remove(self, uuid_or_id: Union[str, int], key: str) -> None:
        """
        Remove a device environment variable.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            key (str): environment variable name.

        Examples:
            >>> balena.models.device.env_var.remove(2184, 'test_env4')
        """
        super(DeviceEnvVariable, self)._remove(uuid_or_id, key)


class DeviceServiceEnvVariable:
    """
    This class implements device service variable model for balena python SDK.
    """

    def __init__(self, pine: PineClient, device: Device, application: Application):
        self.__pine = pine
        self.__device = device
        self.__application = application

    def get_all_by_device(self, uuid_or_id: Union[str, int], options: AnyObject = {}) -> List[EnvironmentVariableBase]:
        """
        Get all device environment variables.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: device service environment variables.

        Examples:
            >>> balena.models.device.service_var.get_all_by_device(8deb12a)
        """
        device_id = self.__device.get(uuid_or_id, {"$select": "id"})["id"]
        return self.__pine.get(
            {
                "resource": "device_service_environment_variable",
                "options": merge(
                    {
                        "$filter": {
                            "service_install": {
                                "$any": {
                                    "$alias": "si",
                                    "$expr": {"si": {"device": device_id}},
                                }
                            }
                        }
                    },
                    options,
                ),
            }
        )

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[EnvironmentVariableBase]:
        """
        Get all device service environment variables belong to an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: device service environment variables.

        Examples:
            >>> balena.models.device.service_var.get_all_by_application(1043050)
        """
        app_id = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]

        return self.__pine.get(
            {
                "resource": "device_service_environment_variable",
                "options": merge(
                    {
                        "$filter": {
                            "service_install": {
                                "$any": {
                                    "$alias": "si",
                                    "$expr": {
                                        "si": {
                                            "device": {
                                                "$any": {
                                                    "$alias": "d",
                                                    "$expr": {"d": {"belongs_to__application": app_id}},
                                                }
                                            }
                                        }
                                    },
                                }
                            }
                        },
                        "$orderby": "name asc",
                    },
                    options,
                ),
            }
        )

    def get(self, uuid_or_id: Union[str, int], service_name_or_id: Union[str, int], key: str) -> Optional[str]:
        """
        Get the overriden value of a service variable on a device

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            service_name_or_id (Union[str, int]): service name (string) or service id (number)
            key (str): variable name

        Returns:
           Optional[str]: device service environment variables.

        Examples:
            >>> balena.models.device.service_var.get('8deb12a', 'myservice', 'VAR')
            >>> balena.models.device.service_var.get('8deb12a', 1234, 'VAR')
        """
        device_id = self.__device.get(uuid_or_id, {"$select": "id"})["id"]

        installs_service = (
            service_name_or_id
            if isinstance(service_name_or_id, int)
            else {"$any": {"$alias": "is", "$expr": {"is": {"service_name": service_name_or_id}}}}
        )

        variables = self.__pine.get(
            {
                "resource": "device_service_environment_variable",
                "options": {
                    "$select": "value",
                    "$filter": {
                        "service_install": {
                            "$any": {
                                "$alias": "si",
                                "$expr": {"si": {"device": device_id, "installs__service": installs_service}},
                            }
                        },
                        "name": key,
                    },
                },
            }
        )

        if isinstance(variables, list) and len(variables) == 1:
            return variables[0].get("value")

    def set(self, uuid_or_id: Union[str, int], service_name_or_id: Union[str, int], key: str, value: str) -> None:
        """
        Set the overriden value of a service variable on a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            service_name_or_id (Union[str, int]): service name (string) or service id (number)
            key (str): variable name
            value (str): variable value

        Examples:
            >>> balena.models.device.service_var.set('7cf02a6', 'myservice', 'VAR', 'override')
            >>> balena.models.device.service_var.set('7cf02a6', 123, 'VAR', 'override')
        """

        if is_id(uuid_or_id):
            device_filter = uuid_or_id
        elif is_full_uuid(uuid_or_id):
            device_filter = {"$any": {"$alias": "d", "$expr": {"d": {"uuid": uuid_or_id}}}}
        else:
            device_filter = self.__device.get(uuid_or_id, {"$select": "id"})["id"]

        installs_service = (
            service_name_or_id
            if isinstance(service_name_or_id, int)
            else {"$any": {"$alias": "s", "$expr": {"s": {"service_name": service_name_or_id}}}}
        )

        service_installs = self.__pine.get(
            {
                "resource": "service_install",
                "options": {
                    "$select": "id",
                    "$filter": {
                        "device": device_filter,
                        "installs__service": installs_service,
                    },
                },
            }
        )

        if (
            service_installs is None
            or (isinstance(service_installs, list) and len(service_installs) == 0)
            or service_installs[0] is None
        ):
            raise exceptions.ServiceNotFound(service_name_or_id)

        if len(service_installs) > 1:
            raise exceptions.AmbiguousDevice(uuid_or_id)

        self.__pine.upsert(
            {
                "resource": "device_service_environment_variable",
                "id": {
                    "service_install": service_installs[0]["id"],
                    "name": key,
                },
                "body": {"value": value},
            }
        )

    def remove(self, uuid_or_id: Union[str, int], service_name_or_id: Union[str, int], key: str) -> None:
        """
        Remove a device service environment variable.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            service_name_or_id (Union[str, int]): service name (string) or service id (number)
            key (str): variable name

        Examples:
            >>> balena.models.device.service_var.set('7cf02a6', 'myservice', 'VAR')
            >>> balena.models.device.service_var.remove('7cf02a6', 28970, 'VAR')
        """

        device_id = self.__device.get(uuid_or_id, {"$select": "id"})["id"]
        installs_service = (
            service_name_or_id
            if isinstance(service_name_or_id, int)
            else {"$any": {"$alias": "is", "$expr": {"is": {"service_name": service_name_or_id}}}}
        )

        self.__pine.delete(
            {
                "resource": "device_service_environment_variable",
                "options": {
                    "$filter": {
                        "service_install": {
                            "$any": {
                                "$alias": "si",
                                "$expr": {
                                    "si": {
                                        "device": device_id,
                                        "installs__service": installs_service,
                                    }
                                },
                            }
                        },
                        "name": key,
                    }
                },
            }
        )
