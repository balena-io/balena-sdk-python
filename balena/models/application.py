try:  # Python 3 imports
    from urllib.parse import urljoin
except ImportError:  # Python 2 imports
    from urlparse import urljoin

from ..auth import Auth
from ..base_request import BaseRequest
from ..settings import Settings
from .device_type import DeviceType
from .release import Release
from .. import exceptions
from ..utils import is_id

from datetime import datetime
import json
from math import isinf
from collections import defaultdict


def _get_role_by_name(role_name):
    """

    Get application membership role

    Args:
        role_name (str): role name.

    Returns:
        int: application membership role id.

    """

    base_request = BaseRequest()
    settings = Settings()

    params = {"filter": "name", "eq": role_name}

    roles = base_request.request(
        "application_membership_role",
        "GET",
        params=params,
        endpoint=settings.get("pine_endpoint"),
    )["d"]

    if not roles:
        raise exceptions.BalenaApplicationMembershipRoleNotFound(role_name=role_name)
    else:
        return roles[0]["id"]


# TODO: support both app_id and app_name
class Application:
    """
    This class implements application model for balena python SDK.

    The returned objects properties are
    `__metadata, actor, app_name, application_type, commit, depends_on__application, device_type,
    id, is_accessible_by_support_until__date, should_track_latest_release, slug, user`.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.auth = Auth()
        self.device_type = DeviceType()
        self.release = Release()
        self.invite = ApplicationInvite()
        self.membership = ApplicationMembership()

    def __get_single_install_summary(self, raw_data):
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

    def __generate_current_service_details(self, raw_data):
        groupedServices = defaultdict(list)

        for obj in [self.__get_single_install_summary(i) for i in raw_data["image_install"]]:
            groupedServices[obj.pop("service_name", None)].append(obj)

        raw_data["current_services"] = dict(groupedServices)
        raw_data["current_gateway_downloads"] = [
            self.__get_single_install_summary(i) for i in raw_data["gateway_download"]
        ]
        raw_data.pop("image_install", None)
        raw_data.pop("gateway_download", None)

        return raw_data

    def get_all(self):
        """
        Get all applications (including collaborator applications).

        Returns:
            list: list contains info of applications.

        Examples:
            >>> balena.models.application.get_all()
            [
                {
                    "depends_on__application": None,
                    "should_track_latest_release": True,
                    "app_name": "foo",
                    "application_type": {
                        "__deferred": {"uri": "/resin/application_type(5)"},
                        "__id": 5,
                    },
                    "__metadata": {"type": "", "uri": "/resin/application(12345)"},
                    "is_accessible_by_support_until__date": None,
                    "actor": 12345,
                    "id": 12345,
                    "user": {"__deferred": {"uri": "/resin/user(12345)"}, "__id": 12345},
                    "device_type": "raspberrypi3",
                    "commit": None,
                    "slug": "my_user/foo",
                },
                {
                    "depends_on__application": None,
                    "should_track_latest_release": True,
                    "app_name": "bar",
                    "application_type": {
                        "__deferred": {"uri": "/resin/application_type(5)"},
                        "__id": 5,
                    },
                    "__metadata": {"type": "", "uri": "/resin/application(12346)"},
                    "is_accessible_by_support_until__date": None,
                    "actor": 12345,
                    "id": 12346,
                    "user": {"__deferred": {"uri": "/resin/user(12345)"}, "__id": 12345},
                    "device_type": "raspberrypi3",
                    "commit": None,
                    "slug": "my_user/bar",
                },
            ]

        """

        return self.base_request.request("my_application", "GET", endpoint=self.settings.get("pine_endpoint"))["d"]

    def get(self, name):
        """
        Get a single application.

        Args:
            name (str): application name.

        Returns:
            dict: application info.

        Raises:
            ApplicationNotFound: if application couldn't be found.
            AmbiguousApplication: when more than one application is returned.

        Examples:
            >>> balena.models.application.get('foo')
            {
                "depends_on__application": None,
                "should_track_latest_release": True,
                "app_name": "foo",
                "application_type": {
                    "__deferred": {"uri": "/resin/application_type(5)"},
                    "__id": 5,
                },
                "__metadata": {"type": "", "uri": "/resin/application(12345)"},
                "is_accessible_by_support_until__date": None,
                "actor": 12345,
                "id": 12345,
                "user": {"__deferred": {"uri": "/resin/user(12345)"}, "__id": 12345},
                "device_type": "raspberrypi3",
                "commit": None,
                "slug": "my_user/foo",
            }

        """

        params = {"filter": "app_name", "eq": name}
        try:
            apps = self.base_request.request(
                "application",
                "GET",
                params=params,
                endpoint=self.settings.get("pine_endpoint"),
            )["d"]
            if len(apps) > 1:
                raise exceptions.AmbiguousApplication(name)
            return apps[0]
        except IndexError:
            raise exceptions.ApplicationNotFound(name)

    def get_with_device_service_details(self, name, expand_release=False):
        """
        Get a single application along with its associated services' essential details.

        Args:
            name (str): application name.
            expand_release (Optional[bool]): Set this to True then the commit of service details will be included.

        Returns:
            dict: application info.

        Raises:
            ApplicationNotFound: if application couldn't be found.
            AmbiguousApplication: when more than one application is returned.

        Examples:
            >>> balena.models.application.get('test-app')
            {
                "depends_on__application": None,
                "should_track_latest_release": True,
                "app_name": "test-app",
                "application_type": {
                    "__deferred": {"uri": "/resin/application_type(5)"},
                    "__id": 5,
                },
                "__metadata": {"type": "", "uri": "/resin/application(1252573)"},
                "is_accessible_by_support_until__date": None,
                "actor": 3259381,
                "slug": "nghiant27101/test-app",
                "owns__device": [
                    {
                        "os_variant": "prod",
                        "__metadata": {"type": "", "uri": "/resin/device(1460194)"},
                        "is_managed_by__service_instance": {
                            "__deferred": {"uri": "/resin/service_instance(117953)"},
                            "__id": 117953,
                        },
                        "should_be_running__release": None,
                        "belongs_to__user": {
                            "__deferred": {"uri": "/resin/user(5227)"},
                            "__id": 5227,
                        },
                        "is_web_accessible": False,
                        "device_type": "raspberrypi3",
                        "belongs_to__application": {
                            "__deferred": {"uri": "/resin/application(1252573)"},
                            "__id": 1252573,
                        },
                        "id": 1460194,
                        "is_locked_until__date": None,
                        "logs_channel": None,
                        "uuid": "b6070f4fea5edf808b576123157fe5ec",
                        "is_managed_by__device": None,
                        "should_be_managed_by__supervisor_release": None,
                        "actor": 3505229,
                        "note": None,
                        "os_version": "balenaOS 2.29.2+rev2",
                        "longitude": "105.8516",
                        "last_connectivity_event": "2019-05-06T07:30:20.230Z",
                        "is_on__commit": "ddf95bef72a981f826bf5303df11f318dbdbff23",
                        "gateway_download": [],
                        "location": "Hanoi, Hanoi, Vietnam",
                        "status": "Idle",
                        "public_address": "14.162.159.155",
                        "is_connected_to_vpn": False,
                        "custom_latitude": "",
                        "is_active": True,
                        "provisioning_state": "",
                        "latitude": "21.0313",
                        "custom_longitude": "",
                        "is_online": False,
                        "supervisor_version": "9.0.1",
                        "ip_address": "192.168.100.20",
                        "provisioning_progress": None,
                        "is_accessible_by_support_until__date": None,
                        "created_at": "2019-01-09T11:41:19.336Z",
                        "download_progress": None,
                        "last_vpn_event": "2019-05-06T07:30:20.230Z",
                        "device_name": "spring-morning",
                        "image_install": [
                            {
                                "status": "Running",
                                "__metadata": {"type": "", "uri": "/resin/image_install(34691843)"},
                                "image": [
                                    {
                                        "is_a_build_of__service": [
                                            {
                                                "service_name": "main",
                                                "__metadata": {
                                                    "type": "",
                                                    "uri": "/resin/service(92238)",
                                                },
                                                "id": 92238,
                                            }
                                        ],
                                        "__metadata": {"type": "", "uri": "/resin/image(1117181)"},
                                        "id": 1117181,
                                    }
                                ],
                                "download_progress": None,
                                "install_date": "2019-04-29T10:24:23.476Z",
                                "id": 34691843,
                            }
                        ],
                        "local_id": None,
                        "vpn_address": None,
                    },
                    {
                        "os_variant": "prod",
                        "__metadata": {"type": "", "uri": "/resin/device(1308755)"},
                        "is_managed_by__service_instance": {
                            "__deferred": {"uri": "/resin/service_instance(2205)"},
                            "__id": 2205,
                        },
                        "should_be_running__release": None,
                        "belongs_to__user": {
                            "__deferred": {"uri": "/resin/user(5227)"},
                            "__id": 5227,
                        },
                        "is_web_accessible": False,
                        "device_type": "raspberrypi3",
                        "belongs_to__application": {
                            "__deferred": {"uri": "/resin/application(1252573)"},
                            "__id": 1252573,
                        },
                        "id": 1308755,
                        "is_locked_until__date": None,
                        "logs_channel": None,
                        "uuid": "531e5cc893b7df1e1118121059d93eee",
                        "is_managed_by__device": None,
                        "should_be_managed_by__supervisor_release": None,
                        "actor": 3259425,
                        "note": None,
                        "os_version": "Resin OS 2.15.1+rev1",
                        "longitude": "105.85",
                        "last_connectivity_event": "2018-09-27T14:48:53.034Z",
                        "is_on__commit": "19ab64483292f0a52989d0ce15ee3d21348dbfce",
                        "gateway_download": [],
                        "location": "Hanoi, Hanoi, Vietnam",
                        "status": "Idle",
                        "public_address": "14.231.247.155",
                        "is_connected_to_vpn": False,
                        "custom_latitude": "",
                        "is_active": True,
                        "provisioning_state": "",
                        "latitude": "21.0333",
                        "custom_longitude": "",
                        "is_online": False,
                        "supervisor_version": "7.16.6",
                        "ip_address": "192.168.0.102",
                        "provisioning_progress": None,
                        "is_accessible_by_support_until__date": None,
                        "created_at": "2018-09-12T04:30:13.549Z",
                        "download_progress": None,
                        "last_vpn_event": "2018-09-27T14:48:53.034Z",
                        "device_name": "nameless-resonance",
                        "image_install": [
                            {
                                "status": "Running",
                                "__metadata": {"type": "", "uri": "/resin/image_install(33844685)"},
                                "image": [
                                    {
                                        "is_a_build_of__service": [
                                            {
                                                "service_name": "main",
                                                "__metadata": {
                                                    "type": "",
                                                    "uri": "/resin/service(92238)",
                                                },
                                                "id": 92238,
                                            }
                                        ],
                                        "__metadata": {"type": "", "uri": "/resin/image(513014)"},
                                        "id": 513014,
                                    }
                                ],
                                "download_progress": None,
                                "install_date": "2018-09-27T13:53:04.748Z",
                                "id": 33844685,
                            }
                        ],
                        "local_id": None,
                        "vpn_address": None,
                    },
                ],
                "user": {"__deferred": {"uri": "/resin/user(5227)"}, "__id": 5227},
                "device_type": "raspberrypi3",
                "commit": "ddf95bef72a981f826bf5303df11f318dbdbff23",
                "id": 1252573,
            }

        """

        release = ""
        if expand_release:
            release = ",is_provided_by__release($select=id,commit)"

        # fmt: off
        raw_query = (
            f"$filter=app_name%20eq%20'{name}'"
            "&$expand=owns__device("
                "$expand=image_install("
                    "$select=id,download_progress,status,install_date"
                    "&$filter=status%20ne%20'deleted'"
                    "&$expand=image("
                        "$select=id"
                        "&$expand=is_a_build_of__service("
                            "$select=id,service_name"
                        ")"
                    ")"
                    f"{release}"
                "),"
                "gateway_download("
                    "$select=id,download_progress,status"
                    "&$filter=status%20ne%20'deleted'"
                    "&$expand=image("
                        "$select=id"
                        "&$expand=is_a_build_of__service("
                            "$select=id,service_name"
                        ")"
                    ")"
                ")"
            ")"
        )
        # fmt: on

        try:
            raw_data = self.base_request.request(
                "application",
                "GET",
                raw_query=raw_query,
                endpoint=self.settings.get("pine_endpoint"),
            )["d"]

            if raw_data and "owns__device" in raw_data:
                map(self.__generate_current_service_details, raw_data["owns__device"])
            if len(raw_data) > 1:
                raise exceptions.AmbiguousApplication(name)
            return raw_data[0]
        except IndexError:
            raise exceptions.ApplicationNotFound(name)

    def get_by_owner(self, name, owner):
        """
        Get a single application using the appname and the handle of the owning organization.

        Args:
            name (str): application name.
            owner (str): The handle of the owning organization.

        Returns:
            dict: application info.

        Raises:
            ApplicationNotFound: if application couldn't be found.
            AmbiguousApplication: when more than one application is returned.

        Examples:
            >>> balena.models.application.get_by_owner('foo', 'my_org')
            {
                "depends_on__application": None,
                "should_track_latest_release": True,
                "app_name": "foo",
                "application_type": {
                    "__deferred": {"uri": "/resin/application_type(5)"},
                    "__id": 5,
                },
                "__metadata": {"type": "", "uri": "/resin/application(12345)"},
                "is_accessible_by_support_until__date": None,
                "actor": 12345,
                "id": 12345,
                "user": {"__deferred": {"uri": "/resin/user(12345)"}, "__id": 12345},
                "device_type": "raspberrypi3",
                "commit": None,
                "slug": "my_user/foo",
            }

        """

        slug = "{owner}/{app_name}".format(owner=owner.lower(), app_name=name.lower())

        params = {"filter": "slug", "eq": slug}
        try:
            apps = self.base_request.request(
                "application",
                "GET",
                params=params,
                endpoint=self.settings.get("pine_endpoint"),
            )["d"]
            if len(apps) > 1:
                raise exceptions.AmbiguousApplication(slug)
            return apps[0]
        except IndexError:
            raise exceptions.ApplicationNotFound(slug)

    def has(self, name):
        """
        Check if an application exists.

        Args:
            name (str): application name.

        Returns:
            bool: True if application exists, False otherwise.

        Examples:
            >>> balena.models.application.has('foo')
            True

        """

        params = {"filter": "app_name", "eq": name}
        app = self.base_request.request(
            "application",
            "GET",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]
        return bool(app)

    def has_any(self):
        """
        Check if the user has any applications.

        Returns:
            bool: True if user has any applications, False otherwise.

        Examples:
            >>> balena.models.application.has_any()
            True

        """

        return len(self.get_all()) > 0

    def get_by_id(self, app_id):
        """
        Get a single application by application id.

        Args:
            app_id (str): application id.

        Returns:
            dict: application info.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >>> balena.models.application.get_by_id(12345)
            {
                "depends_on__application": None,
                "should_track_latest_release": True,
                "app_name": "foo",
                "application_type": {
                    "__deferred": {"uri": "/resin/application_type(5)"},
                    "__id": 5,
                },
                "__metadata": {"type": "", "uri": "/resin/application(12345)"},
                "is_accessible_by_support_until__date": None,
                "actor": 12345,
                "id": 12345,
                "user": {"__deferred": {"uri": "/resin/user(12345)"}, "__id": 12345},
                "device_type": "raspberrypi3",
                "commit": None,
                "slug": "my_user/foo",
            }

        """

        params = {"filter": "id", "eq": app_id}
        try:
            return self.base_request.request(
                "application",
                "GET",
                params=params,
                endpoint=self.settings.get("pine_endpoint"),
            )["d"][0]
        except IndexError:
            raise exceptions.ApplicationNotFound(app_id)

    def create(self, name, device_type, organization, app_type=None):
        """
        Create an application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.
            device_type (str): device type (display form).
            organization (str): handle or id of the organization that the application will belong to.
            app_type (Optional[str]): application type.

        Returns:
            dict: application info.

        Raises:
            InvalidDeviceType: if device type is not supported.
            InvalidApplicationType: if app type is not supported.
            InvalidParameter: if organization is missing.
            OrganizationNotFound: if organization couldn't be found.

        Examples:
            >>> balena.models.application.create('foo', 'Raspberry Pi 3', 12345, 'microservices')
            {
                "depends_on__application": None,
                "should_track_latest_release": True,
                "app_name": "foo",
                "application_type": {
                    "__deferred": {"uri": "/resin/application_type(5)"},
                    "__id": 5,
                },
                "__metadata": {"type": "", "uri": "/resin/application(12345)"},
                "is_accessible_by_support_until__date": None,
                "actor": 12345,
                "id": 12345,
                "user": {"__deferred": {"uri": "/resin/user(12345)"}, "__id": 12345},
                "device_type": "raspberrypi3",
                "commit": None,
                "slug": "my_user/foo",
            }

        """

        if not organization:
            raise exceptions.InvalidParameter("organization", organization)
        else:
            if is_id(organization):
                key = "id"
            else:
                key = "handle"
            raw_query = "$top=1&$select=id&$filter={key}%20eq%20'{value}'".format(key=key, value=organization)

            org = self.base_request.request(
                "organization",
                "GET",
                raw_query=raw_query,
                endpoint=self.settings.get("pine_endpoint"),
                login=True,
            )["d"]

            if not org:
                raise exceptions.OrganizationNotFound(organization)

        device_types = self.device_type.get_all_supported()
        device_manifest = [device for device in device_types if device["name"] == device_type]

        if device_manifest:
            slug = device_manifest[0]["slug"]
            # fmt: off
            raw_query = (
                f"$filter=(slug%20eq%20'{slug}')%20or%20(name%20eq%20'{slug}')"
                "&$select=id,name"
                "&$expand=is_default_for__application("
                    "$select=is_archived"
                    "&$filter=is_host%20eq%20true"
                ")"
            )
            # fmt: on

            device_type_detail = self.base_request.request(
                "device_type",
                "GET",
                raw_query=raw_query,
                endpoint=self.settings.get("pine_endpoint"),
                login=True,
            )["d"][0]

            if not device_type_detail:
                raise exceptions.InvalidDeviceType(device_type)

        else:
            raise exceptions.InvalidDeviceType(device_type)

        host_apps = device_type_detail["is_default_for__application"]
        # TODO: We are now checking whether all returned hostApps are marked as archived so that we
        # do not break open-balena. Once open-balena gets hostApps, we can change this to just a $filter on is_archived.
        if len(host_apps) > 0 and all([dt["is_archived"] for dt in host_apps]):
            raise exceptions.BalenaDiscontinuedDeviceType(device_type)

        data = {
            "app_name": name,
            "is_for__device_type": device_type_detail["id"],
            "organization": org[0]["id"],
        }

        if app_type:
            params = {"filter": "slug", "eq": app_type}

            app_type_detail = self.base_request.request(
                "application_type",
                "GET",
                params=params,
                endpoint=self.settings.get("pine_endpoint"),
                login=True,
            )["d"]

            if not app_type_detail:
                raise exceptions.InvalidApplicationType(app_type)

            data["application_type"] = app_type_detail[0]["id"]

        return json.loads(
            self.base_request.request(
                "application",
                "POST",
                data=data,
                endpoint=self.settings.get("pine_endpoint"),
                login=True,
            ).decode("utf-8")
        )

    def remove(self, name):
        """
        Remove application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.

        Examples:
            >>> balena.models.application.remove('Edison')
            'OK'

        """

        params = {"filter": "app_name", "eq": name}
        return self.base_request.request(
            "application",
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
            login=True,
        )

    def rename(self, app_id, new_name):
        """
        Rename application. This function only works if you log in using credentials or Auth Token.

        Args:
            app_id (int): application id.
            new_name (str): new application name.

        Examples:
            >>> balena.models.application.rename(1681618, 'py-test-app')
            'OK'

        """

        params = {"filter": "id", "eq": app_id}
        data = {"app_name": new_name}

        return self.base_request.request(
            "application",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def restart(self, name):
        """
        Restart application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >>> balena.models.application.restart('RPI1')
            'OK'

        """

        app = self.get(name)
        return self.base_request.request(
            "application/{0}/restart".format(app["id"]),
            "POST",
            endpoint=self.settings.get("api_endpoint"),
            login=True,
        )

    def get_config(self, app_id, version, **options):
        """
        Download application config.json.

        Args:
            app_id (str): application id.
            version (str): the OS version of the image.
            **options (dict): OS configuration keyword arguments to use. The available options are listed below:
                network (Optional[str]): the network type that the device will use, one of 'ethernet' or 'wifi' and defaults to 'ethernet' if not specified.
                appUpdatePollInterval (Optional[str]): how often the OS checks for updates, in minutes.
                wifiKey (Optional[str]): the key for the wifi network the device will connect to.
                wifiSsid (Optional[str]): the ssid for the wifi network the device will connect to.
                ip (Optional[str]): static ip address.
                gateway (Optional[str]): static ip gateway.
                netmask (Optional[str]): static ip netmask.

        Returns:
            dict: application config.json content.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        """  # noqa: E501

        # Application not found will be raised if can't get app by id.
        self.get_by_id(app_id)

        if not version:
            raise exceptions.MissingOption("An OS version is required when calling application.get_config()")

        if "network" not in options:
            options["network"] = "ethernet"

        options["appId"] = app_id
        options["version"] = version

        return self.base_request.request(
            "/download-config",
            "POST",
            data=options,
            endpoint=self.settings.get("api_endpoint"),
        )

    def enable_rolling_updates(self, app_id):
        """
        Enable Rolling update on application.

        Args:
            app_id (str): application id.

        Returns:
            OK/error.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >> > balena.models.application.enable_rolling_updates('106640')
            'OK'
        """

        params = {"filter": "id", "eq": app_id}
        data = {"should_track_latest_release": True}

        return self.base_request.request(
            "application",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def disable_rolling_updates(self, app_id):
        """
        Disable Rolling update on application.

        Args:
            name (str): application id.

        Returns:
            OK/error.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >> > balena.models.application.disable_rolling_updates('106640')
            'OK'
        """

        params = {"filter": "id", "eq": app_id}
        data = {"should_track_latest_release": False}

        return self.base_request.request(
            "application",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def enable_device_urls(self, app_id):
        """
        Enable device urls for all devices that belong to an application

        Args:
            app_id (str): application id.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.application.enable_device_urls('5685')
            'OK'

        """

        params = {"filter": "belongs_to__application", "eq": app_id}
        data = {"is_web_accessible": True}

        return self.base_request.request(
            "device",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def disable_device_urls(self, app_id):
        """
        Disable device urls for all devices that belong to an application.

        Args:
            app_id (str): application id.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.application.disable_device_urls('5685')
            'OK'

        """

        params = {"filter": "belongs_to__application", "eq": app_id}
        data = {"is_web_accessible": False}

        return self.base_request.request(
            "device",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def grant_support_access(self, app_id, expiry_timestamp):
        """
        Grant support access to an application until a specified time.

        Args:
            app_id (str): application id.
            expiry_timestamp (int): a timestamp in ms for when the support access will expire.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.application.grant_support_access('5685', 1511974999000)
            'OK'

        """

        if not expiry_timestamp or expiry_timestamp <= int(
            (datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000
        ):
            raise exceptions.InvalidParameter("expiry_timestamp", expiry_timestamp)

        params = {"filter": "id", "eq": app_id}

        data = {"is_accessible_by_support_until__date": expiry_timestamp}

        return self.base_request.request(
            "application",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def revoke_support_access(self, app_id):
        """
        Revoke support access to an application.

        Args:
            app_id (str): application id.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.application.revoke_support_access('5685')
            'OK'

        """

        params = {"filter": "id", "eq": app_id}

        data = {"is_accessible_by_support_until__date": None}

        return self.base_request.request(
            "application",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def generate_provisioning_key(self, app_id, key_name=None, description=None, expiry_date=None):
        """
        Generate a device provisioning key for a specific application.

        Args:
            app_id (str): application id.
            key_name (Optional[str]): provisioning key name.
            description (Optional[str]): description for provisioning key.
            expiry_date (Optional[str]): expiry date for provisioning key, for example: `2030-01-01T00:00:00Z`.

        Returns:
            str: device provisioning key.

        Examples:
            >> > balena.models.application.generate_provisioning_key('5685')
            'GThZJps91PoJCdzfYqF7glHXzBDGrkr9'

        """

        # Make sure user has access to the app_id
        self.get_by_id(app_id)

        data = {
            "actorType": "application",
            "actorTypeId": app_id,
            "roles": ["provisioning-api-key"],
            "name": key_name,
            "description": description,
            "expiryDate": expiry_date,
        }

        return self.base_request.request(
            "/api-key/v1/",
            "POST",
            data=data,
            endpoint=self.settings.get("api_endpoint"),
        )

    def set_to_release(self, app_id, full_release_hash):
        """
        Set an application to a specific commit.

        Args:
            app_id (str): application id.
            full_release_hash (str) : full_release_hash.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.application.set_to_release('5685', '7dba4e0c461215374edad74a5b78f470b894b5b7')
            'OK'

        """

        raw_query = (
            f"$filter=startswith(commit, '{full_release_hash}')"
            "&$top=1"
            "&$select=id"
            f"&filter=belongs_to__application%20eq%20'{app_id}'%20and%20status%20eq%20'success'"
        )
        try:
            release = self.release._Release__get_by_raw_query(raw_query)[0]
        except exceptions.ReleaseNotFound:
            raise exceptions.ReleaseNotFound(full_release_hash)

        params = {"filter": "id", "eq": app_id}

        data = {
            "should_be_running__release": release["id"],
            "should_track_latest_release": False,
        }

        return self.base_request.request(
            "application",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def will_track_new_releases(self, app_id):
        """
        Get whether the application is configured to receive updates whenever a new release is available.

        Args:
            app_id (str): application id.

        Returns:
            bool: is tracking the latest release.

        Examples:
            >> > balena.models.application.will_track_new_releases('5685')
            True

        """

        return bool(self.get_by_id(app_id)["should_track_latest_release"])

    def is_tracking_latest_release(self, app_id):
        """
        Get whether the application is up to date and is tracking the latest release for updates.

        Args:
            app_id (str): application id.

        Returns:
            bool: is tracking the latest release.

        Examples:
            >> > balena.models.application.is_tracking_latest_release('5685')
            True

        """
        # fmt: off
        raw_query = (
            f"$filter=id%20eq%20'{app_id}'"
            "&$select=should_track_latest_release"
            "&$expand="
                "should_be_running__release($select=id),"
                "owns__release("
                    "$select=id"
                    "&$top=1"
                    "&$filter="
                        "status%20eq%20'success'%20and%20"
                        "is_final%20eq%20true%20and%20"
                        "is_passing_tests%20eq%20true%20and%20"
                        "is_invalidated%20eq%20false"
                    "&$orderby=created_at%20desc"
                ")"
        )
        # fmt: on
        app = self.base_request.request(
            "application",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
            login=True,
        )["d"]

        if not app:
            raise exceptions.ApplicationNotFound(app_id)

        app = app[0]

        latest_release = None
        if app["owns__release"]:
            latest_release = app["owns__release"][0]

        tracked_release = None
        if app["should_be_running__release"]:
            tracked_release = app["should_be_running__release"][0]

        return bool(app["should_track_latest_release"]) and (
            not latest_release or (tracked_release and tracked_release["id"] == latest_release["id"])
        )

    def get_target_release_hash(self, app_id):
        """
        Get the hash of the current release for a specific application.

        Args:
            app_id (str): application id.

        Returns:
            str: The release hash of the current release.

        Examples:
            >>> balena.models.application.get_target_release_hash('5685')

        """

        raw_query = "$filter=id%20eq%20'{app_id}'&$select=id&$expand=should_be_running__release($select=commit)".format(
            app_id=app_id
        )

        app = self.base_request.request(
            "application",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
            login=True,
        )["d"]

        if not app:
            raise exceptions.ApplicationNotFound(app_id)

        app = app[0]

        if app["should_be_running__release"]:
            return app["should_be_running__release"][0]["commit"]

        return ""

    def track_latest_release(self, app_id):
        """
        Configure a specific application to track the latest available release.

        Args:
            app_id (str): application id.

        Examples:
            >>> balena.models.application.track_latest_release('5685')

        """

        latest_release = None

        try:
            latest_release = self.release.get_latest_by_application(app_id)
        except exceptions.ReleaseNotFound:
            pass

        params = {"filter": "id", "eq": app_id}

        data = {"should_track_latest_release": True}

        if latest_release:
            data["should_be_running__release"] = latest_release["id"]

        return self.base_request.request(
            "application",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def get_dashboard_url(self, app_id):
        """
        Get Dashboard URL for a specific application.

        Args:
            app_id (str): application id.

        Raises:
            InvalidParameter: if the app_id is not a finite number.

        Returns:
            str: Dashboard URL for the specific application.

        Examples:
            >>> balena.models.application.get_dashboard_url('1476418')
            https://dashboard.balena-cloud.com/apps/1476418

        """
        try:
            if isinf(int(app_id)):
                raise exceptions.InvalidParameter("app_id", app_id)
        except ValueError:
            raise exceptions.InvalidParameter("app_id", app_id)

        return urljoin(
            self.settings.get("api_endpoint").replace("api", "dashboard"),
            "/apps/{app_id}".format(app_id=app_id),
        )


class ApplicationInvite:
    """
    This class implements application invite model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.auth = Auth()
        self.release = Release()
        self.RESOURCE = "invitee__is_invited_to__application"

    def get_all(self):
        """
        Get all invites.

        Returns:
            list: list contains info of invites.

        Examples:
            >>> balena.models.application.invite.get_all()
            [
                {
                    "id": 5860,
                    "message": "Test invite",
                    "invitee": {
                        "__id": 2965,
                        "__deferred": {"uri": "/resin/invitee(@id)?@id=2965"},
                    },
                    "is_created_by__user": {
                        "__id": 5227,
                        "__deferred": {"uri": "/resin/user(@id)?@id=5227"},
                    },
                    "is_invited_to__application": {
                        "__id": 1681618,
                        "__deferred": {"uri": "/resin/application(@id)?@id=1681618"},
                    },
                    "application_membership_role": {
                        "__id": 2,
                        "__deferred": {"uri": "/resin/application_membership_role(@id)?@id=2"},
                    },
                    "__metadata": {
                        "uri": "/resin/invitee__is_invited_to__application(@id)?@id=5860"
                    },
                }
            ]

        """

        return self.base_request.request(self.RESOURCE, "GET", endpoint=self.settings.get("pine_endpoint"))["d"]

    def get_all_by_application(self, app_id):
        """
        Get all invites by application.

        Args:
            app_id (int): application id.

        Returns:
            list: list contains info of invites.

        Examples:
            >>> balena.models.application.invite.get_all_by_application(1681618)
            [
                {
                    "id": 5860,
                    "message": "Test invite",
                    "invitee": {
                        "__id": 2965,
                        "__deferred": {"uri": "/resin/invitee(@id)?@id=2965"},
                    },
                    "is_created_by__user": {
                        "__id": 5227,
                        "__deferred": {"uri": "/resin/user(@id)?@id=5227"},
                    },
                    "is_invited_to__application": {
                        "__id": 1681618,
                        "__deferred": {"uri": "/resin/application(@id)?@id=1681618"},
                    },
                    "application_membership_role": {
                        "__id": 2,
                        "__deferred": {"uri": "/resin/application_membership_role(@id)?@id=2"},
                    },
                    "__metadata": {
                        "uri": "/resin/invitee__is_invited_to__application(@id)?@id=5860"
                    },
                }
            ]

        """

        params = {"filter": "is_invited_to__application", "eq": app_id}

        return self.base_request.request(
            self.RESOURCE,
            "GET",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    def create(self, app_id, invitee, role_name=None, message=None):
        """
        Creates a new invite for an application.

        Args:
            app_id (int): application id.
            invitee (str): the email of the invitee.
            role_name (Optional[str]): the role name to be granted to the invitee.
            message (Optional[str]): the message to send along with the invite.

        Returns:
            dict: application invite.

        Examples:
            >>> balena.models.application.invite.create(1681618, 'james@resin.io', 'developer', 'Test invite')
            {
                "id": 5860,
                "message": "Test invite",
                "invitee": {"__id": 2965, "__deferred": {"uri": "/resin/invitee(@id)?@id=2965"}},
                "is_created_by__user": {
                    "__id": 5227,
                    "__deferred": {"uri": "/resin/user(@id)?@id=5227"},
                },
                "is_invited_to__application": {
                    "__id": 1681618,
                    "__deferred": {"uri": "/resin/application(@id)?@id=1681618"},
                },
                "application_membership_role": {
                    "__id": 2,
                    "__deferred": {"uri": "/resin/application_membership_role(@id)?@id=2"},
                },
                "__metadata": {"uri": "/resin/invitee__is_invited_to__application(@id)?@id=5860"},
            }

        """

        data = {
            "invitee": invitee,
            "is_invited_to__application": app_id,
            "message": message,
        }

        if role_name:
            data["application_membership_role "] = _get_role_by_name(role_name)

        return json.loads(
            self.base_request.request(
                self.RESOURCE,
                "POST",
                data=data,
                endpoint=self.settings.get("pine_endpoint"),
                login=True,
            ).decode("utf-8")
        )

    def revoke(self, invite_id):
        """
        Revoke an invite.

        Args:
            invite_id (int): application invite id.

        Examples:
            >>> balena.models.application.invite.revoke(5860)
            'OK'

        """

        params = {"filter": "id", "eq": invite_id}

        return self.base_request.request(
            self.RESOURCE,
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def accept(self, invite_token):
        """
        Accepts an invite.

        Args:
            invite_token (str): invitationToken - invite token.

        """

        return self.base_request.request(
            "/user/v1/invitation/{0}".format(invite_token),
            "POST",
            endpoint=self.settings.get("api_endpoint"),
            login=True,
        )


class ApplicationMembership:
    """
    This class implements application membership model for balena python SDK.
    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.auth = Auth()
        self.RESOURCE = "user__is_member_of__application"

    def get_all(self):
        """
        Get all application memberships.

        Returns:
            list: list contains info of application memberships.

        Examples:
            >>> balena.models.application.membership.get_all()
            [
                {
                    "is_member_of__application": {
                        "__id": 1681618,
                        "__deferred": {"uri": "/resin/application(@id)?@id=1681618"},
                    },
                    "application_membership_role": {
                        "__id": 2,
                        "__deferred": {"uri": "/resin/application_membership_role(@id)?@id=2"},
                    },
                    "__metadata": {"uri": "/resin/user__is_member_of__application(@id)?@id=55074"},
                    "id": 55074,
                    "user": {"__id": 189, "__deferred": {"uri": "/resin/user(@id)?@id=189"}},
                }
            ]

        """

        return self.base_request.request(self.RESOURCE, "GET", endpoint=self.settings.get("pine_endpoint"))["d"]

    def get(self, membership_id):
        """
        Get a single application membership.

        Args:
            membership_id (int): application membership id.

        Returns:
            dict: application membership.

        Examples:
            >>> balena.models.application.membership.get(55074)
            {
                "is_member_of__application": {
                    "__id": 1681618,
                    "__deferred": {"uri": "/resin/application(@id)?@id=1681618"},
                },
                "application_membership_role": {
                    "__id": 2,
                    "__deferred": {"uri": "/resin/application_membership_role(@id)?@id=2"},
                },
                "__metadata": {"uri": "/resin/user__is_member_of__application(@id)?@id=55074"},
                "id": 55074,
                "user": {"__id": 189, "__deferred": {"uri": "/resin/user(@id)?@id=189"}},
            }

        """

        params = {"filter": "id", "eq": membership_id}

        result = self.base_request.request(
            self.RESOURCE,
            "GET",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

        if not result:
            raise exceptions.ApplicationMembershipNotFound(membership_id)

        return result[0]

    def get_all_by_application(self, app_id):
        """
        Get all memberships by application.

        Args:
            app_id (int): application id.

        Returns:
            list: list contains info of application memberships.

        Examples:
            >>> balena.models.application.membership.get_all_by_application(1681618)
            [
                {
                    "is_member_of__application": {
                        "__id": 1681618,
                        "__deferred": {"uri": "/resin/application(@id)?@id=1681618"},
                    },
                    "application_membership_role": {
                        "__id": 2,
                        "__deferred": {"uri": "/resin/application_membership_role(@id)?@id=2"},
                    },
                    "__metadata": {"uri": "/resin/user__is_member_of__application(@id)?@id=55074"},
                    "id": 55074,
                    "user": {"__id": 189, "__deferred": {"uri": "/resin/user(@id)?@id=189"}},
                }
            ]

        """

        params = {"filter": "is_member_of__application", "eq": app_id}

        return self.base_request.request(
            self.RESOURCE,
            "GET",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    def create(self, app_id, user_name, role_name=None):
        """
        Creates a new membership for an application.

        Args:
            app_id (int): application id.
            user_name (str): the username of the balena user that will become a member.
            role_name (Optional[str]): the role name to be granted to the membership.

        Returns:
            dict: application invite.

        Examples:
            >>> balena.models.application.membership.create(1681618, 'nghiant2710')
            {
                "is_member_of__application": {
                    "__id": 1681618,
                    "__deferred": {"uri": "/resin/application(@id)?@id=1681618"},
                },
                "application_membership_role": {
                    "__id": 2,
                    "__deferred": {"uri": "/resin/application_membership_role(@id)?@id=2"},
                },
                "__metadata": {"uri": "/resin/user__is_member_of__application(@id)?@id=55074"},
                "id": 55074,
                "user": {"__id": 189, "__deferred": {"uri": "/resin/user(@id)?@id=189"}},
            }

        """

        data = {"username": user_name, "is_member_of__application": app_id}

        if role_name:
            data["application_membership_role "] = _get_role_by_name(role_name)

        return json.loads(
            self.base_request.request(
                self.RESOURCE,
                "POST",
                data=data,
                endpoint=self.settings.get("pine_endpoint"),
                login=True,
            ).decode("utf-8")
        )

    def change_role(self, membership_id, role_name):
        """
        Changes the role of an application member.

        Args:
            membership_id (int): the id of the membership that will be changed.
            role_name (str): the role name to be granted to the membership.

        Examples:
            >>> balena.models.application.membership.change_role(55074, 'observer')
            'OK'

        """

        role_id = _get_role_by_name(role_name)

        params = {"filter": "id", "eq": membership_id}

        data = {"application_membership_role": role_id}

        return self.base_request.request(
            self.RESOURCE,
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def remove(self, membership_id):
        """
        Remove a membership.

        Args:
            membership_id (int): application membership id.

        """

        params = {"filter": "id", "eq": membership_id}

        return self.base_request.request(
            self.RESOURCE,
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )
