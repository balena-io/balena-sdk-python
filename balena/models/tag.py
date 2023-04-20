import json

from ..base_request import BaseRequest
from .device import Device
from .release import Release
from ..settings import Settings
from ..utils import is_id
from .. import exceptions
import re


class Tag:
    """
    This class is a wrapper for Tag models.

    """

    def __init__(self):
        self.device = DeviceTag()
        self.application = ApplicationTag()
        self.release = ReleaseTag()


class BaseTag:
    """
    an abstract implementation for resource tags. This class won't be included in the docs.

    """

    def __init__(self, resource):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.resource = resource

    def get_all(self, params=None, data=None, raw_query=None):
        if raw_query:
            return self.base_request.request(
                "{}_tag".format(self.resource),
                "GET",
                raw_query=raw_query,
                endpoint=self.settings.get("pine_endpoint"),
            )["d"]
        else:
            return self.base_request.request(
                "{}_tag".format(self.resource),
                "GET",
                params=params,
                data=data,
                endpoint=self.settings.get("pine_endpoint"),
            )["d"]

    def set(self, resource_id, tag_key, value):
        try:
            data = {self.resource: resource_id, "tag_key": tag_key, "value": value}

            return json.loads(
                self.base_request.request(
                    "{}_tag".format(self.resource), "POST", data=data, endpoint=self.settings.get("pine_endpoint")
                ).decode("utf-8")
            )
        except exceptions.RequestError as e:
            is_unique_key_violation_response = e.status_code == 409 and re.search(r"unique", e.message, re.IGNORECASE)

            if not is_unique_key_violation_response:
                raise e

            params = {"filters": {self.resource: resource_id, "tag_key": tag_key}}

            data = {"value": value}

            return self.base_request.request(
                "{}_tag".format(self.resource),
                "PATCH",
                params=params,
                data=data,
                endpoint=self.settings.get("pine_endpoint"),
            )

    def remove(self, resource_id, tag_key):
        params = {"filters": {self.resource: resource_id, "tag_key": tag_key}}

        return self.base_request.request(
            "{}_tag".format(self.resource),
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )


class DeviceTag(BaseTag):
    """
    This class implements device tag model for balena python SDK.

    """

    def __init__(self):
        super(DeviceTag, self).__init__("device")
        self.device = Device()

    def get_all_by_application(self, app_id):
        """
        Get all device tags for an application.

        Args:
            app_id (str): application id .

        Returns:
            list: list contains device tags.

        Examples:
            >>> balena.models.tag.device.get_all_by_application('1005160')
            [
                {
                    "device": {"__deferred": {"uri": "/balena/device(1055117)"}, "__id": 1055117},
                    "tag_key": "group1",
                    "id": 20158,
                    "value": "aaa",
                    "__metadata": {"type": "", "uri": "/balena/device_tag(20158)"},
                },
                {
                    "device": {"__deferred": {"uri": "/balena/device(1055116)"}, "__id": 1055116},
                    "tag_key": "group1",
                    "id": 20159,
                    "value": "bbb",
                    "__metadata": {"type": "", "uri": "/balena/device_tag(20159)"},
                },
            ]

        """

        query = "$filter=device/any(d:d/belongs_to__application%20eq%20{app_id})".format(app_id=app_id)

        return super(DeviceTag, self).get_all(raw_query=query)

    def get_all_by_device(self, uuid):
        """
        Get all device tags for a device.

        Args:
            uuid (str): device uuid.

        Returns:
            list: list contains device tags.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.tag.device.get_all_by_device('a03ab646c01f39e39a1e3deb7fce76b93075c6d599fd5be4a889b8145e2f8f')
            [
                {
                    "device": {"__deferred": {"uri": "/balena/device(1055116)"}, "__id": 1055116},
                    "tag_key": "group1",
                    "id": 20159,
                    "value": "bbb",
                    "__metadata": {"type": "", "uri": "/balena/device_tag(20159)"},
                },
                {
                    "device": {"__deferred": {"uri": "/balena/device(1055116)"}, "__id": 1055116},
                    "tag_key": "db_tag",
                    "id": 20160,
                    "value": "aaa",
                    "__metadata": {"type": "", "uri": "/balena/device_tag(20160)"},
                },
            ]

        """  # noqa: E501

        raw_query = "$filter=device/any(d:d/uuid%20eq%20'{uuid}')".format(uuid=uuid)

        return super(DeviceTag, self).get_all(raw_query=raw_query)

    def get_all(self):
        """
        Get all device tags.

        Returns:
            list: list contains device tags.

        Examples:
            >>> balena.models.tag.device.get_all()
            [
                {
                    "device": {"__deferred": {"uri": "/balena/device(1036574)"}, "__id": 1036574},
                    "tag_key": "db_tag",
                    "id": 20157,
                    "value": "rpi3",
                    "__metadata": {"type": "", "uri": "/balena/device_tag(20157)"},
                },
                {
                    "device": {"__deferred": {"uri": "/balena/device(1055117)"}, "__id": 1055117},
                    "tag_key": "group1",
                    "id": 20158,
                    "value": "aaa",
                    "__metadata": {"type": "", "uri": "/balena/device_tag(20158)"},
                },
            ]

        """

        return super(DeviceTag, self).get_all()

    def set(self, parent_id, tag_key, value):
        """
        Set a device tag (update tag value if it exists).
        ___Note___: Notice that when using the device ID rather than UUID, it will avoid one extra API roundtrip.

        Args:
            parent_id (Union[str, int]): device uuid or device id.
            tag_key (str): tag key.
            value (str): tag value.

        Returns:
            dict: dict contains device tag info if tag doesn't exist.
            OK: if tag exists.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.tag.device.set('f5213eac0d63ac47721b037a7406d306', 'testtag','test1')
            {
                "device": {"__deferred": {"uri": "/balena/device(1036574)"}, "__id": 1036574},
                "tag_key": "testtag",
                "id": 20163,
                "value": "test1",
                "__metadata": {"type": "", "uri": "/balena/device_tag(20163)"},
            }
            >>> balena.models.tag.device.set('f5213eac0d63ac47721b037a7406d306', 'testtag','test2')
            OK

        """

        # Trying to avoid an extra HTTP request
        # when the provided parameter looks like an id.
        # Note that this throws an exception for missing names/uuids,
        # but not for missing ids
        device_id = parent_id if is_id(parent_id) else self.device.get(parent_id)["id"]

        return super(DeviceTag, self).set(device_id, tag_key, value)

    def remove(self, parent_id, tag_key):
        """
        Remove a device tag.

        Args:
            parent_id (Union[str, int]): device uuid or device id.
            tag_key (str): tag key.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.tag.device.remove('f5213eac0d63ac47721b037a7406d306', 'testtag'))
            OK

        """

        device_id = parent_id if is_id(parent_id) else self.device.get(parent_id)["id"]
        return super(DeviceTag, self).remove(device_id, tag_key)


class ApplicationTag(BaseTag):
    """
    This class implements application tag model for balena python SDK.

    """

    def __init__(self):
        super(ApplicationTag, self).__init__("application")

    def get_all_by_application(self, app_id):
        """
        Get all application tags for an application.

        Args:
            app_id (str): application id .

        Returns:
            list: list contains application tags.

        Examples:
            >>> balena.models.tag.application.get_all_by_application('1005767')
            [
                {
                    "application": {
                        "__deferred": {"uri": "/balena/application(1005767)"},
                        "__id": 1005767,
                    },
                    "tag_key": "appTa1",
                    "id": 12887,
                    "value": "Python SDK",
                    "__metadata": {"type": "", "uri": "/balena/application_tag(12887)"},
                },
                {
                    "application": {
                        "__deferred": {"uri": "/balena/application(1005767)"},
                        "__id": 1005767,
                    },
                    "tag_key": "appTag2",
                    "id": 12888,
                    "value": "Python SDK",
                    "__metadata": {"type": "", "uri": "/balena/application_tag(12888)"},
                },
            ]

        """

        params = {"filter": "application", "eq": app_id}

        return super(ApplicationTag, self).get_all(params=params)

    def get_all(self):
        """
        Get all application tags.

        Returns:
            list: list contains application tags.

        Examples:
            >>> balena.models.tag.application.get_all()
            [
                {
                    "application": {
                        "__deferred": {"uri": "/balena/application(1005160)"},
                        "__id": 1005160,
                    },
                    "tag_key": "appTag",
                    "id": 12886,
                    "value": "Python SDK",
                    "__metadata": {"type": "", "uri": "/balena/application_tag(12886)"},
                },
                {
                    "application": {
                        "__deferred": {"uri": "/balena/application(1005767)"},
                        "__id": 1005767,
                    },
                    "tag_key": "appTa1",
                    "id": 12887,
                    "value": "Python SDK",
                    "__metadata": {"type": "", "uri": "/balena/application_tag(12887)"},
                },
            ]
        """

        return super(ApplicationTag, self).get_all()

    def set(self, app_id, tag_key, value):
        """
        Set an application tag (update tag value if it exists).

        Args:
            app_id (str): application id.
            tag_key (str): tag key.
            value (str): tag value.

        Returns:
            dict: dict contains application tag info if tag doesn't exist.
            OK: if tag exists.

        Examples:
            >>> balena.models.tag.application.set('1005767', 'tag1', 'Python SDK')
            {
                "application": {
                    "__deferred": {"uri": "/balena/application(1005767)"},
                    "__id": 1005767,
                },
                "tag_key": "tag1",
                "id": 12889,
                "value": "Python SDK",
                "__metadata": {"type": "", "uri": "/balena/application_tag(12889)"},
            }
            >>> balena.models.tag.application.set('1005767', 'tag1','Balena Python SDK')
            OK

        """

        return super(ApplicationTag, self).set(app_id, tag_key, value)

    def remove(self, app_id, tag_key):
        """
        Remove an application tag.

        Args:
            app_id (str): application id.
            tag_key (str): tag key.

        Examples:
            >>> balena.models.tag.application.remove('1005767', 'tag1')
            OK

        """

        return super(ApplicationTag, self).remove(app_id, tag_key)


class ReleaseTag(BaseTag):
    """
    This class implements release tag model for balena python SDK.

    """

    def __init__(self):
        super(ReleaseTag, self).__init__("release")
        self.release = Release()

    def get_all_by_application(self, app_id):
        """
        Get all release tags for an application.

        Args:
            app_id (str): application id.

        Returns:
            list: list contains release tags.

        Examples:
            >>> balena.models.tag.release.get_all_by_application('1043050')
            [
                {
                    "release": {"__deferred": {"uri": "/balena/release(465307)"}, "__id": 465307},
                    "tag_key": "releaseTag1",
                    "id": 135,
                    "value": "Python SDK",
                    "__metadata": {"type": "", "uri": "/balena/release_tag(135)"},
                }
            ]


        """

        query = "$filter=release/any(d:d/belongs_to__application%20eq%20{app_id})".format(app_id=app_id)

        return super(ReleaseTag, self).get_all(raw_query=query)

    def get_all_by_release(self, commit_or_id):
        """
        Get all release tags for a release.

        Args:
            commit_or_id: release commit (str) or id (int).

        Returns:
            list: list contains release tags.

        Examples:
            >>> balena.models.tag.release.get_all_by_release(135)
            [
                {
                    "release": {"__deferred": {"uri": "/balena/release(465307)"}, "__id": 465307},
                    "tag_key": "releaseTag1",
                    "id": 135,
                    "value": "Python SDK",
                    "__metadata": {"type": "", "uri": "/balena/release_tag(135)"},
                }
            ]

        """

        release_id = self.release.get(commit_or_id)["id"]

        params = {"filter": "release", "eq": release_id}

        return super(ReleaseTag, self).get_all(params=params)

    def get_all(self):
        """
        Get all release tags.

        Returns:
            list: list contains release tags.

        Examples:
            >>> balena.models.tag.release.get_all()
            [
                {
                    "release": {"__deferred": {"uri": "/balena/release(465307)"}, "__id": 465307},
                    "tag_key": "releaseTag1",
                    "id": 135,
                    "value": "Python SDK",
                    "__metadata": {"type": "", "uri": "/balena/release_tag(135)"},
                }
            ]

        """

        return super(ReleaseTag, self).get_all()

    def set(self, commit_or_id, tag_key, value):
        """
        Set a release tag (update tag value if it exists).

        Args:
            commit_or_id: release commit (str) or id (int).
            tag_key (str): tag key.
            value (str): tag value.

        Returns:
            dict: dict contains release tag info if tag doesn't exist.
            OK: if tag exists.

        Examples:
            >>> balena.models.tag.release.set(465307, 'releaseTag1', 'Python SDK')
            {
                "release": {"__deferred": {"uri": "/balena/release(465307)"}, "__id": 465307},
                "tag_key": "releaseTag1",
                "id": 135,
                "value": "Python SDK",
                "__metadata": {"type": "", "uri": "/balena/release_tag(135)"},
            }
            >>> balena.models.tag.release.set(465307, 'releaseTag1', 'Python SDK 1')
            OK

        """

        release_id = self.release.get(commit_or_id)["id"]

        return super(ReleaseTag, self).set(release_id, tag_key, value)

    def remove(self, commit_or_id, tag_key):
        """
        Remove a release tag.

        Args:
            commit_or_id: release commit (str) or id (int).
            tag_key (str): tag key.

        Examples:
            >>> balena.models.tag.release.remove(135, 'releaseTag1')
            OK

        """

        release_id = self.release.get(commit_or_id)["id"]
        return super(ReleaseTag, self).remove(release_id, tag_key)
