from datetime import datetime
from math import isinf
from typing import List, Literal, Optional, Union
from urllib.parse import urljoin

from .. import exceptions
from ..balena_auth import request
from ..dependent_resource import DependentResource
from ..pine import PineClient
from ..settings import Settings
from ..types import AnyObject, ApplicationInviteOptions, ApplicationMembershipRoles, ResourceKey, ShutdownOptions
from ..types.models import (
    ApplicationInviteType,
    ApplicationMembershipType,
    TypeApplication,
    BaseTagType,
    EnvironmentVariableBase,
)
from ..utils import (
    generate_current_service_details,
    get_current_service_details_pine_expand,
    is_id,
    merge,
    normalize_device_os_version,
    with_supervisor_locked_error,
)
from .device_type import DeviceType


class Application:
    """
    This class implements application model for balena python SDK.
    """

    def __init__(self, pine: PineClient, settings: Settings, load_inner_models=True):
        if load_inner_models:
            self.__device_type = DeviceType(pine, settings)
            self.__release = Release(pine, settings)

        self.__pine = pine
        self.__settings = settings
        self.tags = ApplicationTag(pine, self)
        self.config_var = ApplicationConfigVariable(pine, self)
        self.env_var = ApplicationEnvVariable(pine, self)
        self.build_var = BuildEnvVariable(pine, self)
        self.membership = ApplicationMembership(pine, self)
        self.invite = ApplicationInvite(pine, self, settings)

    def __get_access_filter(self):
        return {
            "is_directly_accessible_by__user": {
                "$any": {
                    "$alias": "dau",
                    "$expr": {
                        "1": 1,
                    },
                },
            },
        }

    def __get_device_type_id(self, device_type: str) -> int:
        dt = self.__device_type.get(
            device_type,
            {
                "$select": "id",
                "$expand": {
                    "is_default_for__application": {
                        "$select": "is_archived",
                        "$filter": {
                            "is_host": True,
                        },
                    },
                },
            },
        )

        host_apps = dt.get("is_default_for__application", [])
        if len(host_apps) > 0 and all(map(lambda ha: ha["is_archived"], host_apps)):
            raise exceptions.BalenaDiscontinuedDeviceType(device_type)

        return dt["id"]

    def __get_organization_id(self, organization: Union[str, int]) -> int:
        id_filter = {"handle": organization}
        if is_id(organization):
            id_filter = {"id": organization}

        org = self.__pine.get(
            {
                "resource": "organization",
                "id": id_filter,
                "options": {"$select": ["id"]},
            }
        )

        if org is None:
            raise exceptions.OrganizationNotFound(organization)

        return org["id"]

    def __normalize_application(self, application: TypeApplication) -> TypeApplication:
        owned_devices = application.get("owns__device")
        if isinstance(owned_devices, list):
            application["owns__device"] = list(map(normalize_device_os_version, owned_devices))
        return application

    def get_id(self, slug_or_uuid_or_id: Union[str, int]) -> int:
        """
        Given an application slug or uuid or id, returns it numeric id.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)

        Returns:
            int: The id.

        Examples:
            >>> balena.models.application.get_dashboard_url(1476418)

        """
        if is_id(slug_or_uuid_or_id):
            return int(slug_or_uuid_or_id)
        app = self.get(slug_or_uuid_or_id, {"$select": "id"})
        return app["id"]

    def get_dashboard_url(self, app_id: int) -> str:
        """
        Get Dashboard URL for a specific application.

        Args:
            app_id (int): application id.

        Returns:
            str: Dashboard URL for the specific application.

        Examples:
            >>> balena.models.application.get_dashboard_url(1476418)
        """
        try:
            if isinf(int(app_id)):
                raise exceptions.InvalidParameter("app_id", app_id)
        except ValueError:
            raise exceptions.InvalidParameter("app_id", app_id)

        return urljoin(
            self.__settings.get("api_endpoint").replace("api", "dashboard"),
            f"/apps/{app_id}",
        )

    def get_all(
        self,
        options: AnyObject = {},
        context: Optional[str] = "directly_accessible",
    ) -> List[TypeApplication]:
        """
        Get all applications

        Args:
            options (AnyObject): extra pine options to use
            context (Optional[str]): extra access filters, None or 'directly_accessible'

        Returns:
            List[APIKeyType]: user API key

        Examples:
            >>> balena.models.application.get_all()
        """

        apps = self.__pine.get(
            {
                "resource": "application",
                "options": merge(
                    {
                        **({"$filter": self.__get_access_filter()} if context == "directly_accessible" else {}),
                        "$orderby": "app_name asc",
                    },
                    options,
                ),
            }
        )

        return list(map(self.__normalize_application, apps))

    def get_all_directly_accessible(
        self,
        options: AnyObject = {},
    ) -> List[TypeApplication]:
        """
        Get all applications directly accessible by the user

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[APIKeyType]: user API key

        Examples:
            >>> balena.models.application.get_all_directly_accessible()
        """

        return self.get_all(options, "directly_accessible")

    def get(
        self,
        slug_or_uuid_or_id: Union[str, int],
        options: AnyObject = {},
        context: Optional[str] = "directly_accessible",
    ) -> TypeApplication:
        """
        Get a single application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use
            context (Optional[str]): extra access filters, None or 'directly_accessible'

        Returns:
            TypeApplication: application info.

        Examples:
            >>> balena.models.application.get("myorganization/myapp")
            >>> balena.models.application.get(123)

        """

        access_filter = None
        if context == "directly_accessible":
            access_filter = self.__get_access_filter()

        application = None
        if is_id(slug_or_uuid_or_id):
            application = self.__pine.get(
                {
                    "resource": "application",
                    "id": slug_or_uuid_or_id,
                    "options": merge(
                        {} if access_filter is None else {"$filter": access_filter},
                        options,
                    ),
                }
            )
        elif isinstance(slug_or_uuid_or_id, str):
            lower_case_slug_or_uuid = slug_or_uuid_or_id.lower()

            if access_filter is not None:
                app_filter = {
                    **access_filter,
                    "$or": {
                        "slug": lower_case_slug_or_uuid,
                        "uuid": lower_case_slug_or_uuid,
                    },
                }
            else:
                app_filter = {
                    "$or": {
                        "slug": lower_case_slug_or_uuid,
                        "uuid": lower_case_slug_or_uuid,
                    }
                }
            applications = self.__pine.get(
                {
                    "resource": "application",
                    "options": merge({"$filter": app_filter}, options),
                }
            )

            if len(applications) > 1:
                raise exceptions.AmbiguousApplication(slug_or_uuid_or_id)
            try:
                application = applications[0]
            except IndexError:
                raise exceptions.ApplicationNotFound(slug_or_uuid_or_id)

        if application is None:
            raise exceptions.ApplicationNotFound(slug_or_uuid_or_id)

        return self.__normalize_application(application)

    def get_directly_accessible(
        self,
        slug_or_uuid_or_id: Union[str, int],
        options: AnyObject = {},
    ) -> TypeApplication:
        """
        Get a single application directly accessible by the user

        Args:
            slug_or_uuid_or_id (str): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            TypeApplication: application info.

        Examples:
            >>> balena.models.application.get_directly_accessible("myorganization/myapp")
            >>> balena.models.application.get_directly_accessible(123)
        """
        return self.get(slug_or_uuid_or_id, options, "directly_accessible")

    def get_with_device_service_details(
        self,
        slug_or_uuid_or_id: Union[str, int],
        options: AnyObject = {},
    ) -> TypeApplication:
        """
        This method does not map exactly to the underlying model: it runs a
        larger prebuilt query, and reformats it into an easy to use and
        understand format. If you want more control, or to see the raw model
        directly, use `application.get(uuidOrId, options)` instead.

        Args:
            slug_or_uuid_or_id (str): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            TypeApplication: application info.

        Examples:
            >>> balena.models.application.get_with_device_service_details('my_org_handle/my_app_name')
        """
        service_options = merge(
            {"$expand": [{"owns__device": {"$expand": get_current_service_details_pine_expand(True)}}]},
            options,
        )

        app = self.get(slug_or_uuid_or_id, service_options)

        devices = app.get("owns__device")
        if app is not None and devices is not None:
            app["owns__device"] = list(map(generate_current_service_details, devices))

        return app

    def get_by_name(
        self,
        app_name: str,
        options: AnyObject = {},
        context: Optional[str] = "directly_accessible",
    ) -> TypeApplication:
        """
         Get a single application using the appname.

        Args:
            slug_or_uuid_or_id (str): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use
            context (Optional[str]): extra access filters, None or 'directly_accessible'

        Returns:
            TypeApplication: application info.

        Examples:
            >>> balena.models.application.get("myapp")
        """
        apps = self.__pine.get(
            {
                "resource": "application",
                "options": merge(
                    {
                        "$filter": {
                            **(self.__get_access_filter() if context == "directly_accessible" else {}),
                            "app_name": app_name,
                        }
                    },
                    options,
                ),
            }
        )

        if len(apps) == 0:
            raise exceptions.ApplicationNotFound(app_name)

        if len(apps) > 1:
            raise exceptions.AmbiguousApplication(app_name)

        return self.__normalize_application(apps[0])

    def get_by_owner(self, app_name: str, owner: str, options: AnyObject = {}) -> TypeApplication:
        """
        Get a single application using the appname and the handle of the owning organization.

        Args:
            app_name (str): application name.
            owner (str): The handle of the owning organization.
            options (AnyObject): extra pine options to use.

        Returns:
            TypeApplication: application info.

        Examples:
            >>> balena.models.application.get_by_owner('foo', 'my_org')
        """

        slug = f"{owner.lower()}/{app_name.lower()}"
        app = self.__pine.get(
            {
                "resource": "application",
                "id": {"slug": slug},
                "options": options,
            }
        )

        if app is None:
            raise exceptions.ApplicationNotFound(slug)

        return self.__normalize_application(app)

    def has(self, slug_or_uuid_or_id: Union[str, int]) -> bool:
        """
        Check if an application exists.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)

        Returns:
            bool: True if application exists, False otherwise.

        Examples:
            >>> balena.models.application.has('my_org/foo')
        """

        try:
            self.get(slug_or_uuid_or_id, {"$select": ["id"]})
            return True
        except exceptions.ApplicationNotFound:
            return False

    def has_any(self) -> bool:
        """
        Check if the user has any applications.

        Returns:
            bool: True if user has any applications, False otherwise.

        Examples:
            >>> balena.models.application.has_any()
        """

        applications = self.get_all(
            {"$select": ["id"]},
            "directly_accessible",
        )
        return len(applications) != 0

    def create(
        self,
        name: str,
        device_type: str,
        organization: Union[str, int],
        application_class: Optional[Literal["app", "fleet", "block"]] = None,
    ) -> TypeApplication:
        """
        Create an application.

        Args:
            name (str): application name.
            device_type (str): device type (slug).
            organization (Union[str, int]): handle or id of the organization that the application will belong to.
            application_class (Optional[Literal["app", "fleet", "block"]]): application class.

        Returns:
            TypeApplication: application info.

        Examples:
            >>> balena.models.application.create('foo', 'raspberry-pi', 12345)
            >>> balena.models.application.create('foo', 'raspberry-pi', 12345, 'block')
        """

        if organization is None:
            raise exceptions.InvalidParameter("organization", organization)

        # TODO: run these two in parallel
        device_type_id = self.__get_device_type_id(device_type)
        organization_id = self.__get_organization_id(organization)

        body = {
            "app_name": name,
            "is_for__device_type": device_type_id,
            "organization": organization_id,
        }

        if application_class is not None:
            body["is_of__class"] = application_class

        return self.__pine.post({"resource": "application", "body": body})

    # TODO: enable batch operations
    def remove(self, slug_or_uuid_or_id: Union[str, int]) -> None:
        """
        Remove application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).

        Examples:
            >>> balena.models.application.remove('my_org/my_app')
            >>> balena.models.application.remove('c184556293854781aea71b0bdae10e45')
            >>> balena.models.application.remove(123)
        """

        try:
            application_id = self.get_id(slug_or_uuid_or_id)
            self.__pine.delete({"resource": "application", "id": application_id})
        except exceptions.RequestError as e:
            if e.status_code == 404:
                raise exceptions.ApplicationNotFound(slug_or_uuid_or_id)
            raise e

    def rename(self, slug_or_uuid_or_id: Union[str, int], new_name: str) -> None:
        """
        Rename application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).
            new_name (str): new application name.

        Examples:
            >>> balena.models.application.rename(1681618, 'py-test-app')
        """

        try:
            application_id = self.get_id(slug_or_uuid_or_id)
            self.__pine.patch(
                {
                    "resource": "application",
                    "id": application_id,
                    "body": {"app_name": new_name},
                }
            )
        except exceptions.RequestError as e:
            if e.status_code == 404:
                raise exceptions.ApplicationNotFound(slug_or_uuid_or_id)
            raise e

    def restart(self, slug_or_uuid_or_id: Union[str, int]):
        """
        Restart application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).

        Examples:
            >>> balena.models.application.restart('myorg/RPI1')
        """

        def __restart():
            try:
                application_id = self.get_id(slug_or_uuid_or_id)
                request(method="POST", path=f"/applcation/{application_id}/restart", settings=self.__settings)
            except exceptions.RequestError as e:
                if e.status_code == 404:
                    raise exceptions.ApplicationNotFound(slug_or_uuid_or_id)
                raise e

        with_supervisor_locked_error(__restart)

    def generate_provisioning_key(
        self,
        slug_or_uuid_or_id: Union[str, int],
        key_name: Optional[str] = None,
        description: Optional[str] = None,
        expiry_date: Optional[str] = None,
    ) -> str:
        """
        Generate a device provisioning key for a specific application.

        Args:
            slug_or_uuid_or_id (str): application slug (string), uuid (string) or id (number)
            key_name (Optional[str]): provisioning key name.
            description (Optional[str]): description for provisioning key.
            expiry_date (Optional[str]): expiry date for provisioning key, for example: `2030-01-01T00:00:00Z`.

        Returns:
            str: device provisioning key.

        Examples:
            >>> balena.models.application.generate_provisioning_key(5685)
        """
        try:
            application_id = self.get_id(slug_or_uuid_or_id)
            return request(
                method="POST",
                path="/api-key/v1/",
                settings=self.__settings,
                body={
                    "actorType": "application",
                    "actorTypeId": application_id,
                    "roles": ["provisioning-api-key"],
                    "name": key_name,
                    "description": description,
                    "expiryDate": expiry_date,
                },
            ).strip('"')
        except exceptions.RequestError as e:
            if e.status_code == 404:
                raise exceptions.ApplicationNotFound(slug_or_uuid_or_id)
            raise e

    def purge(self, app_id: int) -> None:
        """
        Purge devices by application id

        Args:
            app_id (int): application id (number)

        Examples:
            >>> balena.models.application.purge(5685)
        """
        with_supervisor_locked_error(
            lambda: request(
                method="POST",
                path="/supervisor/v1/purge",
                settings=self.__settings,
                body={"appId": app_id, "data": {"appId": f"{app_id}"}},
            )
        )

    def shutdown(self, app_id: int, options: ShutdownOptions = {}) -> None:
        """
        Shutdown devices by application id

        Args:
            app_id (int): application id (number)
            options (ShutdownOptions): override update lock

        Examples:
            >>> balena.models.application.shutdown(5685)
            >>> balena.models.application.shutdown(5685, {"force": True})
        """
        with_supervisor_locked_error(
            lambda: request(
                method="POST",
                path="/supervisor/v1/shutdown",
                settings=self.__settings,
                body={
                    "appId": app_id,
                    "data": {"force": bool(options.get("force"))},
                },
            )
        )

    def reboot(self, app_id: int, options: ShutdownOptions = {}) -> None:
        """
        Reboots devices by application id

        Args:
            app_id (int): application id (number)
            options (ShutdownOptions): override update lock

        Examples:
            >>> balena.models.application.reboot(5685)
            >>> balena.models.application.reboot(5685, {"force": True})
        """
        with_supervisor_locked_error(
            lambda: request(
                method="POST",
                path="/supervisor/v1/reboot",
                settings=self.__settings,
                body={
                    "appId": app_id,
                    "data": {"force": bool(options.get("force"))},
                },
            )
        )

    def will_track_new_releases(self, slug_or_uuid_or_id: Union[str, int]) -> bool:
        """
         Get whether the application is configured to receive updates whenever a new release is available.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).

        Returns:
            bool: is tracking the latest release.

        Examples:
            >>> balena.models.application.will_track_new_releases(5685)
        """

        app = self.get(slug_or_uuid_or_id, {"$select": "should_track_latest_release"})
        return bool(app.get("should_track_latest_release"))

    def is_tracking_latest_release(self, slug_or_uuid_or_id: Union[str, int]) -> bool:
        """
        Get whether the application is up to date and is tracking the latest finalized release for updates

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).

        Returns:
            bool: is tracking the latest release.

        Examples:
            >>> balena.models.application.is_tracking_latest_release(5685)
        """
        app_options = {
            "$select": "should_track_latest_release",
            "$expand": {
                "should_be_running__release": {"$select": "id"},
                "owns__release": {
                    "$select": "id",
                    "$top": 1,
                    "$filter": {
                        "is_final": True,
                        "is_passing_tests": True,
                        "is_invalidated": False,
                        "status": "success",
                    },
                    "$orderby": "created_at desc",
                },
            },
        }

        app = self.get(slug_or_uuid_or_id, app_options)
        tracked_release = app["should_be_running__release"][0]
        latest_release = app["owns__release"][0]

        return bool(
            app.get("should_track_latest_release")
            and (not latest_release or tracked_release.get("id") == latest_release["id"])
        )

    def pin_to_release(self, slug_or_uuid_or_id: Union[str, int], full_release_hash: str) -> None:
        """
        Configures the application to run a particular release
        and not get updated when the latest release changes.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).
            full_release_hash (str) : the hash of a successful release (string)

        Examples:
            >>> balena.models.application.set_to_release(5685, '7dba4e0c461215374edad74a5b78f470b894b5b7')
        """

        application_id = self.get_id(slug_or_uuid_or_id)
        release = self.__release.get(
            full_release_hash,
            {
                "$select": "id",
                "$top": 1,
                "$filter": {
                    "belongs_to__application": application_id,
                    "status": "success",
                },
            },
        )

        self.__pine.patch(
            {
                "resource": "application",
                "id": application_id,
                "body": {
                    "should_be_running__release": release["id"],
                    "should_track_latest_release": False,
                },
            }
        )

    def get_target_release_hash(self, slug_or_uuid_or_id: Union[str, int]) -> Optional[str]:
        """
        Get the hash of the current release for a specific application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)

        Returns:
            Optional[str]: The release hash of the current release or None.

        Examples:
            >>> balena.models.application.get_target_release_hash(5685)
        """
        app_options = {
            "$select": "id",
            "$expand": {"should_be_running__release": {"$select": "commit"}},
        }
        application = self.get(slug_or_uuid_or_id, app_options)

        return application.get("should_be_running__release", [{}])[0].get("commit")

    def track_latest_release(self, slug_or_uuid_or_id: Union[str, int]) -> None:
        """
        Configure a specific application to track the latest available release.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)

        Examples:
            >>> balena.models.application.track_latest_release(5685)
        """

        app_options = {
            "$select": "id",
            "$expand": {
                "owns__release": {
                    "$select": "id",
                    "$top": 1,
                    "$filter": {
                        "is_final": True,
                        "is_passing_tests": True,
                        "is_invalidated": False,
                        "status": "success",
                    },
                    "$orderby": "created_at desc",
                }
            },
        }

        application = self.get(slug_or_uuid_or_id, app_options)
        body = {"should_track_latest_release": True}
        latest_release = application.get("owns__release", [None])[0]
        if latest_release is not None:
            body["should_be_running__release"] = latest_release.get("id")

        self.__pine.patch(
            {
                "resource": "application",
                "id": application["id"],
                "body": body,
            }
        )

    def enable_device_urls(self, slug_or_uuid_or_id: Union[str, int]) -> None:
        """
        Enable device urls for all devices that belong to an application

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).

        Examples:
            >>> balena.models.application.enable_device_urls(5685)
        """

        app = self.get(slug_or_uuid_or_id, {"$select": "id"})
        self.__pine.patch(
            {
                "resource": "device",
                "body": {"is_web_accessible": True},
                "options": {"$filter": {"belongs_to__application": app["id"]}},
            }
        )

    def disable_device_urls(self, slug_or_uuid_or_id: Union[str, int]) -> None:
        """
        Disable device urls for all devices that belong to an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).

        Examples:
            >>> balena.models.application.disable_device_urls(5685)
        """

        app = self.get(slug_or_uuid_or_id, {"$select": "id"})
        self.__pine.patch(
            {
                "resource": "device",
                "body": {"is_web_accessible": False},
                "options": {"$filter": {"belongs_to__application": app["id"]}},
            }
        )

    def grant_support_access(self, slug_or_uuid_or_id: Union[str, int], expiry_timestamp: int):
        """
        Grant support access to an application until a specified time.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).
            expiry_timestamp (int): a timestamp in ms for when the support access will expire.

        Examples:
            >>> balena.models.application.grant_support_access(5685, 1511974999000)
        """

        if expiry_timestamp is None or expiry_timestamp <= int(
            (datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000
        ):
            raise exceptions.InvalidParameter("expiry_timestamp", expiry_timestamp)

        try:
            application_id = self.get_id(slug_or_uuid_or_id)
            self.__pine.patch(
                {
                    "resource": "application",
                    "id": application_id,
                    "body": {"is_accessible_by_support_until__date": expiry_timestamp},
                }
            )
        except exceptions.RequestError as e:
            if e.status_code == 404:
                raise exceptions.ApplicationNotFound(slug_or_uuid_or_id)
            raise e

    def revoke_support_access(self, slug_or_uuid_or_id: Union[str, int]):
        """
        Revoke support access to an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).

        Examples:
            >>> balena.models.application.revoke_support_access(5685)
        """

        try:
            application_id = self.get_id(slug_or_uuid_or_id)
            self.__pine.patch(
                {
                    "resource": "application",
                    "id": application_id,
                    "body": {"is_accessible_by_support_until__date": None},
                }
            )
        except exceptions.RequestError as e:
            if e.status_code == 404:
                raise exceptions.ApplicationNotFound(slug_or_uuid_or_id)
            raise e


class ApplicationTag(DependentResource[BaseTagType]):
    """
    This class implements application tag model for balena python SDK.

    """

    def __init__(self, pine: PineClient, application: Application):
        self.__application = application
        super(ApplicationTag, self).__init__(
            "application_tag",
            "tag_key",
            "application",
            lambda id: self.__application.get(id, {"$select": "id"})["id"],
            pine,
        )

    def get_all_by_application(self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}) -> List[BaseTagType]:
        """
        Get all application tags for an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.application.tags.get_all_by_application(1005160)
        """
        return super(ApplicationTag, self)._get_all_by_parent(slug_or_uuid_or_id, options)

    def set(self, slug_or_uuid_or_id: Union[str, int], tag_key: str, value: str) -> None:
        """
        Set an application tag (update tag value if it exists).

        Args:
            slug_or_uuid_or_id (int): application slug (string), uuid (string) or id (number)
            tag_key (str): tag key.
            value (str): tag value.

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.application.tags.set(1005767, 'tag1', 'Python SDK')
        """
        super(ApplicationTag, self)._set(slug_or_uuid_or_id, tag_key, value)

    def remove(self, slug_or_uuid_or_id: Union[str, int], tag_key: str) -> None:
        """
        Remove an application tag.

        Args:
            slug_or_uuid_or_id (int): application slug (string), uuid (string) or id (number)
            tag_key (str): tag key.

        Examples:
            >>> balena.models.application.tags.remove(1005767, 'tag1')
        """
        super(ApplicationTag, self)._remove(slug_or_uuid_or_id, tag_key)


class ApplicationConfigVariable(DependentResource[EnvironmentVariableBase]):
    """
    This class implements application config variable model for balena python SDK.

    """

    def __init__(self, pine: PineClient, application: Application):
        self.__application = application
        super(ApplicationConfigVariable, self).__init__(
            "application_config_variable",
            "name",
            "application",
            lambda id: self.__application.get(id, {"$select": "id"})["id"],
            pine,
        )

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[EnvironmentVariableBase]:
        """
        Get all application config variables by application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: application config variables.

        Examples:
            >>> balena.models.application.config_var.get_all_by_application(9020)
        """
        return super(ApplicationConfigVariable, self)._get_all_by_parent(slug_or_uuid_or_id, options)

    def get(self, slug_or_uuid_or_id: Union[str, int], env_var_name: str) -> Optional[str]:
        """
        Get application config variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            env_var_name (str): environment variable name.

        Examples:
            >>> balena.models.application.config_var.get('8deb12','test_env4')
        """
        return super(ApplicationConfigVariable, self)._get(slug_or_uuid_or_id, env_var_name)

    def set(self, slug_or_uuid_or_id: Union[str, int], env_var_name: str, value: str) -> None:
        """
        Set the value of a specific application config variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Examples:
            >>> balena.models.application.config_var.set('8deb12','test_env', 'testing1')
        """
        super(ApplicationConfigVariable, self)._set(slug_or_uuid_or_id, env_var_name, value)

    def remove(self, slug_or_uuid_or_id: Union[str, int], key: str) -> None:
        """
        Remove an application config variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)

        Examples:
            >>> balena.models.application.config_var.remove(2184)
        """
        super(ApplicationConfigVariable, self)._remove(slug_or_uuid_or_id, key)


class ApplicationEnvVariable(DependentResource[EnvironmentVariableBase]):
    """
    This class implements application environment variable model for balena python SDK.

    """

    def __init__(self, pine: PineClient, application: Application):
        self.__application = application
        super(ApplicationEnvVariable, self).__init__(
            "application_environment_variable",
            "name",
            "application",
            lambda id: self.__application.get(id, {"$select": "id"})["id"],
            pine,
        )

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[EnvironmentVariableBase]:
        """
        Get all application environment variables by application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: application environment variables.

        Examples:
            >>> balena.models.application.env_var.get_all_by_application(9020)
            >>> balena.models.application.env_var.get_all_by_application("myorg/myslug")
        """
        return super(ApplicationEnvVariable, self)._get_all_by_parent(slug_or_uuid_or_id, options)

    def get(self, slug_or_uuid_or_id: Union[str, int], env_var_name: str) -> Optional[str]:
        """
        Get application environment variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            env_var_name (str): environment variable name.

        Examples:
            >>> balena.models.application.env_var.get('8deb12','test_env4')
        """
        return super(ApplicationEnvVariable, self)._get(slug_or_uuid_or_id, env_var_name)

    def set(self, slug_or_uuid_or_id: Union[str, int], env_var_name: str, value: str) -> None:
        """
        Set the value of a specific application environment variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Examples:
            >>> balena.models.application.env_var.set('8deb12','test_env4', 'testing1')
        """
        super(ApplicationEnvVariable, self)._set(slug_or_uuid_or_id, env_var_name, value)

    def remove(self, slug_or_uuid_or_id: Union[str, int], key: str) -> None:
        """
        Remove an application environment variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)

        Examples:
            >>> balena.models.application.env_var.remove(2184)
        """
        super(ApplicationEnvVariable, self)._remove(slug_or_uuid_or_id, key)


class BuildEnvVariable(DependentResource[EnvironmentVariableBase]):
    """
    This class implements build environment variable model for balena python SDK.

    """

    def __init__(self, pine: PineClient, application: Application):
        self.__application = application
        super(BuildEnvVariable, self).__init__(
            "build_environment_variable",
            "name",
            "application",
            lambda id: self.__application.get(id, {"$select": "id"})["id"],
            pine,
        )

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[EnvironmentVariableBase]:
        """
        Get all build environment variables by application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: build environment variables.

        Examples:
            >>> balena.models.application.build_var.get_all_by_application(9020)
            >>> balena.models.application.build_var.get_all_by_application("myorg/myslug")
        """
        return super(BuildEnvVariable, self)._get_all_by_parent(slug_or_uuid_or_id, options)

    def get(self, slug_or_uuid_or_id: Union[str, int], env_var_name: str) -> Optional[str]:
        """
        Get build environment variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            env_var_name (str): environment variable name.

        Examples:
            >>> balena.models.application.build_var.get('8deb12','test_env4')
        """
        return super(BuildEnvVariable, self)._get(slug_or_uuid_or_id, env_var_name)

    def set(self, slug_or_uuid_or_id: Union[str, int], env_var_name: str, value: str) -> None:
        """
        Set the value of a specific build environment variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Examples:
            >>> balena.models.application.build_var.set('8deb12','test_env4', 'testing1')
        """
        super(BuildEnvVariable, self)._set(slug_or_uuid_or_id, env_var_name, value)

    def remove(self, slug_or_uuid_or_id: Union[str, int], key: str) -> None:
        """
        Remove an build environment variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)

        Examples:
            >>> balena.models.application.build_var.remove(2184)
        """
        super(BuildEnvVariable, self)._remove(slug_or_uuid_or_id, key)


class ApplicationInvite:
    """
    This class implements application invite model for balena python SDK.

    """

    def __init__(self, pine: PineClient, application: Application, settings: Settings):
        self.__application = application
        self.__pine = pine
        self.__settings = settings
        self.RESOURCE = "invitee__is_invited_to__application"

    def get_all(self, options: AnyObject = {}) -> List[ApplicationInviteType]:
        """
        Get all invites.

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[ApplicationInviteType]: list contains info of invites.

        Examples:
            >>> balena.models.application.invite.get_all()
        """
        return self.__pine.get({"resource": self.RESOURCE, "options": options})

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[ApplicationInviteType]:
        """
        Get all invites by application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).
            options (AnyObject): extra pine options to use

        Returns:
            List[ApplicationInviteType]: list contains info of invites.

        Examples:
            >>> balena.models.application.invite.get_all_by_application(1681618)
        """
        app = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})
        return self.get_all(
            merge(
                {"$filter": {"is_invited_to__application": app["id"]}},
                options,
            )
        )

    def create(
        self,
        slug_or_uuid_or_id: Union[str, int],
        options: ApplicationInviteOptions,
    ) -> ApplicationInviteType:
        """
        Creates a new invite for an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).
            options (ApplicationInviteOptions): Application Invite options dict to use.
                invitee (str): the email/balena_username of the invitee.
                role_name (Optional[str]): the role name to be granted to the invitee.
                One of "observer", "developer", "operator". Defaults to "developer"
                message (Optional[str]): the message to send along with the invite.

        Returns:
            dict: application invite.

        Examples:
            >>> balena.models.application.invite.create(1681618, 'invitee@example.org', 'developer', 'Test invite')
        """
        invitee = options.get("invitee")
        if invitee is None:
            raise exceptions.InvalidParameter("options.invitee", None)

        role_name = options.get("roleName", "developer")

        # TODO: paralelize me
        app = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})
        roles = self.__pine.get(
            {
                "resource": "application_membership_role",
                "options": {
                    "$top": 1,
                    "$select": "id",
                    "$filter": {"name": role_name},
                },
            }
        )

        body = {
            "invitee": invitee,
            "is_invited_to__application": app["id"],
            "message": options.get("message"),
        }

        if roles is not None:
            role_id = (roles[0] if len(roles) > 0 else {}).get("id", None)
            if role_id is None:
                raise exceptions.BalenaApplicationMembershipRoleNotFound(role_name)
            body["application_membership_role"] = role_id

        return self.__pine.post({"resource": self.RESOURCE, "body": body})

    def revoke(self, invite_id: int) -> None:
        """
        Revoke an invite.

        Args:
            invite_id (int): application invite id.

        Examples:
            >>> balena.models.application.invite.revoke(5860)
        """
        self.__pine.delete({"resource": self.RESOURCE, "id": invite_id})

    def accept(self, invite_token: str) -> None:
        """
        Accepts an invite.

        Args:
            invite_token (str): invitationToken - invite token.

        Examples:
            >>> balena.models.application.invite.accept("qwerty-invitation-token")
        """
        try:
            request(method="POST", settings=self.__settings, path=f"/user/v1/invitation/{invite_token}")
        except exceptions.RequestError as e:
            if e.status_code == 401:
                raise exceptions.NotLoggedIn()
            raise e


class ApplicationMembership:
    """
    This class implements application membership model for balena python SDK.
    """

    def __init__(self, pine: PineClient, application: Application):
        self.__application = application
        self.__pine = pine
        self.RESOURCE = "user__is_member_of__application"

    def __get_role_id(self, role_name: str) -> Optional[int]:
        role = self.__pine.get(
            {
                "resource": "application_membership_role",
                "id": {"name": role_name},
                "options": {"$select": "id"},
            }
        )

        if role is None:
            raise exceptions.BalenaApplicationMembershipRoleNotFound(role_name)

        return role["id"]

    def get_all(self, options: AnyObject = {}) -> List[ApplicationMembershipType]:
        """
        Get all application memberships.

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[ApplicationMembershipType]: list contains info of application memberships.

        Examples:
            >>> balena.models.application.membership.get_all()
        """

        return self.__pine.get({"resource": self.RESOURCE, "options": options})

    def get(self, membership_id: ResourceKey, options: AnyObject = {}) -> ApplicationMembershipType:
        """
        Get a single application membership.

        Args:
            membership_id (ResourceKey): the id or an object with the unique `user` & `is_member_of__application`
            numeric pair of the membership
            options (AnyObject): extra pine options to use

        Returns:
            ApplicationMembershipType: application membership.

        Examples:
            >>> balena.models.application.membership.get(55074)
            >>> balena.models.application.membership.get({"user": 123, "is_member_of__application": 125})
        """

        if not isinstance(membership_id, int) and not isinstance(membership_id, dict):
            raise exceptions.InvalidParameter("membershipId", membership_id)

        result = self.__pine.get(
            {
                "resource": self.RESOURCE,
                "id": membership_id,  # type: ignore
                "options": options,
            }
        )

        if result is None:
            raise exceptions.ApplicationMembershipNotFound(str(membership_id))

        return result

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[ApplicationMembershipType]:
        """
        Get all memberships by application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).
            options (AnyObject): extra pine options to use

        Returns:
            list: list contains info of application memberships.

        Examples:
            >>> balena.models.application.membership.get_all_by_application(1681618)
        """
        app = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})
        return self.get_all(
            merge(
                {"$filter": {"is_member_of__application": app["id"]}},
                options,
            )
        )

    def create(
        self,
        slug_or_uuid_or_id: Union[str, int],
        username: str,
        role_name: ApplicationMembershipRoles = "developer",
    ) -> ApplicationMembershipType:
        """
        Creates a new membership for an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).
            username (str): the username of the balena user that will become a member.
            role_name (Optional[str]): the role name to be granted to the membership.

        Returns:
            ApplicationMembershipType: application membership.

        Examples:
            >>> balena.models.application.membership.create(1681618, 'testuser')
        """

        app = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})
        role_id = self.__get_role_id(role_name)
        body = {
            "username": username,
            "is_member_of__application": app["id"],
            "application_membership_role": role_id,
        }

        return self.__pine.post({"resource": self.RESOURCE, "body": body})

    def change_role(self, membership_id: ResourceKey, role_name: str) -> None:
        """
        Changes the role of an application member.

        Args:
            membership_id (ResourceKey): the id or an object with the unique `user` & `is_member_of__application`
            numeric pair of the membership
            role_name (str): the role name to be granted to the membership.

        Examples:
            >>> balena.models.application.membership.change_role(55074, 'observer')
        """

        role_id = self.__get_role_id(role_name)
        self.__pine.patch(
            {
                "resource": self.RESOURCE,
                "id": membership_id,  # type: ignore
                "body": {"application_membership_role": role_id},
            }
        )

    def remove(self, membership_id: ResourceKey) -> None:
        """
        Remove a membership.

        Args:
            membership_id (ResourceKey): the id or an object with the unique `user` & `is_member_of__application`
        """
        self.__pine.delete({"resource": self.RESOURCE, "id": membership_id})  # type: ignore


from .release import Release  # noqa: E402
