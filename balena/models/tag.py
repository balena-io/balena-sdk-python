from typing import List, Optional, Union

from ..types import AnyObject
from ..types.models import BaseTagType
from ..utils import is_id, merge
from ..dependent_resource import DependentResource
from .device import Application, Device
from .release import Release, ReleaseRawVersionApplicationPair


class Tag:
    """
    This class is a wrapper for Tag models.

    """

    def __init__(self):
        self.device = DeviceTag()
        self.application = ApplicationTag()
        self.release = ReleaseTag()


class DeviceTag(DependentResource[BaseTagType]):
    """
    This class implements device tag model for balena python SDK.

    """

    def __init__(self):
        self.device = Device()
        self.application = Application()
        super(DeviceTag, self).__init__(
            "device_tag",
            "tag_key",
            "device",
            lambda id: self.device.get(id, {"$select": "id"})["id"]
        )

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[BaseTagType]:
        """
        Get all device tags for an application.

        Args:
            slug_or_uuid_or_id (int): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.tag.device.get_all_by_application(1005160)
        """

        app_id = self.application.get(slug_or_uuid_or_id, {"$select": "id"})[
            "id"
        ]
        return super(DeviceTag, self)._get_all(
            merge(
                {
                    "$filter": {
                        "device": {
                            "$any": {
                                "$alias": "d",
                                "$expr": {
                                    "d": {"belongs_to__application": app_id}
                                },
                            }
                        }
                    }
                },
                options,
            )
        )

    def get_all_by_device(
        self, uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[BaseTagType]:
        """
        Get all device tags for a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.tag.device.get_all_by_device('a03ab646c')
        """

        id = self.device.get(uuid_or_id, {"$select": "id"})["id"]
        return super(DeviceTag, self)._get_all_by_parent(id, options)

    def get_all(self, options: AnyObject = {}) -> List[BaseTagType]:
        """
        Get all device tags.

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.tag.device.get_all()
        """

        return super(DeviceTag, self)._get_all(options)

    def get(self, uuid_or_id: Union[str, int], tag_key: str) -> Optional[str]:
        """
        Set a device tag (update tag value if it exists).
        ___Note___: Notice that when using the device ID rather than UUID,
        it will avoid one extra API roundtrip.

        Args:
            uuid_or_id (Union[str, int]): device uuid or device id.
            tag_key (str): tag key.
            value (str): tag value.

        Returns:
            Optional[str]: tag value

        Examples:
            >>> balena.models.tag.device.set('f5213eac0d63ac4', 'testtag','test1')
            >>> balena.models.tag.device.set('f5213eac0d63ac4', 'testtag','test2')
        """

        # Trying to avoid an extra HTTP request
        # when the provided parameter looks like an id.
        # Note that this throws an exception for missing names/uuids,
        # but not for missing ids
        device_id = (
            uuid_or_id
            if is_id(uuid_or_id)
            else self.device.get(uuid_or_id, {"$select": "id"})["id"]
        )
        return super(DeviceTag, self)._get(device_id, tag_key)

    def set(
        self, uuid_or_id: Union[str, int], tag_key: str, value: str
    ) -> None:
        """
        Set a device tag (update tag value if it exists).
        ___Note___: Notice that when using the device ID rather than UUID,
        it will avoid one extra API roundtrip.

        Args:
            uuid_or_id (Union[str, int]): device uuid or device id.
            tag_key (str): tag key.
            value (str): tag value.

        Examples:
            >>> balena.models.tag.device.set('f5213eac0d63ac4', 'testtag','test1')
            >>> balena.models.tag.device.set('f5213eac0d63ac4', 'testtag','test2')
        """

        # Trying to avoid an extra HTTP request
        # when the provided parameter looks like an id.
        # Note that this throws an exception for missing names/uuids,
        # but not for missing ids
        device_id = (
            uuid_or_id
            if is_id(uuid_or_id)
            else self.device.get(uuid_or_id, {"$select": "id"})["id"]
        )
        super(DeviceTag, self)._set(device_id, tag_key, value)

    def remove(self, uuid_or_id: Union[str, int], tag_key: str) -> None:
        """
        Remove a device tag.

        Args:
            uuid_or_id (Union[str, int]): device uuid or device id.
            tag_key (str): tag key.

        Examples:
            >>> balena.models.tag.device.remove('f5213eac0d63ac477', 'testtag')
        """

        device_id = (
            uuid_or_id
            if is_id(uuid_or_id)
            else self.device.get(uuid_or_id, {"$select": "id"})["id"]
        )
        super(DeviceTag, self)._remove(device_id, tag_key)


class ApplicationTag(DependentResource[BaseTagType]):
    """
    This class implements application tag model for balena python SDK.

    """

    def __init__(self):
        self.application = Application()
        super(ApplicationTag, self).__init__(
            "application_tag",
            "tag_key",
            "application",
            lambda id: self.application.get(id, {"$select": "id"})["id"]
        )

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[BaseTagType]:
        """
        Get all application tags for an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.tag.device.get_all_by_application(1005160)
        """
        return super(ApplicationTag, self)._get_all_by_parent(
            slug_or_uuid_or_id, options
        )

    def get_all(self, options: AnyObject = {}) -> List[BaseTagType]:
        """
        Get all application tags.

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.tag.application.get_all()
        """
        return super(ApplicationTag, self)._get_all(options)

    def get(
        self, slug_or_uuid_or_id: Union[str, int], tag_key: str
    ) -> Optional[str]:
        """
        Set an application tag (update tag value if it exists).

        Args:
            slug_or_uuid_or_id (int): application slug (string), uuid (string) or id (number)
            tag_key (str): tag key.

        Returns:
            Optional[str]: tag value.

        Examples:
            >>> balena.models.tag.application.get(1005767, 'tag1')
        """
        return super(ApplicationTag, self)._get(slug_or_uuid_or_id, tag_key)

    def set(
        self, slug_or_uuid_or_id: Union[str, int], tag_key: str, value: str
    ) -> None:
        """
        Set an application tag (update tag value if it exists).

        Args:
            slug_or_uuid_or_id (int): application slug (string), uuid (string) or id (number)
            tag_key (str): tag key.
            value (str): tag value.

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.tag.application.set(1005767, 'tag1', 'Python SDK')
        """
        super(ApplicationTag, self)._set(slug_or_uuid_or_id, tag_key, value)

    def remove(self, slug_or_uuid_or_id: Union[str, int], tag_key: str) -> None:
        """
        Remove an application tag.

        Args:
            slug_or_uuid_or_id (int): application slug (string), uuid (string) or id (number)
            tag_key (str): tag key.

        Examples:
            >>> balena.models.tag.application.remove(1005767, 'tag1')
        """
        super(ApplicationTag, self)._remove(slug_or_uuid_or_id, tag_key)


class ReleaseTag(DependentResource[BaseTagType]):
    """
    This class implements release tag model for balena python SDK.

    """

    def __init__(self):
        self.application = Application()
        self.release = Release()
        super(ReleaseTag, self).__init__(
            "release_tag",
            "tag_key",
            "release",
            lambda id: self.release.get(id, {"$select": "id"})["id"]
        )

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[BaseTagType]:
        """
        Get all device tags for an application.

        Args:
            slug_or_uuid_or_id (int): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.tag.device.get_all_by_application(1005160)
        """

        app_id = self.application.get(slug_or_uuid_or_id, {"$select": "id"})[
            "id"
        ]
        return super(ReleaseTag, self)._get_all(
            merge(
                {
                    "$filter": {
                        "release": {
                            "$any": {
                                "$alias": "r",
                                "$expr": {
                                    "r": {"belongs_to__application": app_id}
                                },
                            }
                        }
                    }
                },
                options,
            )
        )

    def get_all_by_release(
        self,
        commit_or_id_or_raw_version: Union[
            str, int, ReleaseRawVersionApplicationPair
        ],
        options: AnyObject = {},
    ) -> List[BaseTagType]:
        """
        Get all release tags for a release.

        Args:
            commit_or_id_or_raw_version(Union[str, int, ReleaseRawVersionApplicationPair]): release commit (string) or
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.tag.release.get_all_by_release(135)
        """

        release_opts = {
            "$select": "id",
            "$expand": {
                "release_tag": merge({"$orderby": "tag_key asc"}, options)
            },
        }
        release = self.release.get(commit_or_id_or_raw_version, release_opts)
        return release["release_tag"]

    def get_all(self, options: AnyObject = {}) -> List[BaseTagType]:
        """
        Get all release tags.

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[BaseTagType]: tags list.

        Examples:
            >>> balena.models.tag.release.get_all()
        """
        return super(ReleaseTag, self)._get_all(options)

    def set(
        self,
        commit_or_id_or_raw_version: Union[
            str, int, ReleaseRawVersionApplicationPair
        ],
        tag_key: str,
        value: str,
    ) -> None:
        """
        Set a release tag (update tag value if it exists).

        Args:
            commit_or_id_or_raw_version(Union[str, int, ReleaseRawVersionApplicationPair]): release commit (string) or
            tag_key (str): tag key.
            value (str): tag value.

        Returns:
            BaseTagType: dict contains release

        Examples:
            >>> balena.models.tag.release.set(465307, 'releaseTag1', 'Python SDK')
        """
        super(ReleaseTag, self)._set(commit_or_id_or_raw_version, tag_key, value)

    def get(
        self,
        commit_or_id_or_raw_version: Union[
            str, int, ReleaseRawVersionApplicationPair
        ],
        tag_key: str,
    ) -> Optional[str]:
        """
        Get a single release tag.

        Args:
            commit_or_id_or_raw_version(Union[str, int, ReleaseRawVersionApplicationPair]): release commit (string) or
            tag_key (str): tag key.

        Returns:
            BaseTagType: dict contains release

        Examples:
            >>> balena.models.tag.release.get(465307, 'releaseTag1')
        """
        return super(ReleaseTag, self)._get(commit_or_id_or_raw_version, tag_key)

    def remove(
        self,
        commit_or_id_or_raw_version: Union[
            str, int, ReleaseRawVersionApplicationPair
        ],
        tag_key: str,
    ) -> None:
        """
        Remove a release tag.

        Args:
            commit_or_id_or_raw_version(Union[str, int, ReleaseRawVersionApplicationPair]): release commit (string) or
            tag_key (str): tag key.

        Examples:
            >>> balena.models.tag.release.remove(135, 'releaseTag1')
        """

        super(ReleaseTag, self)._remove(commit_or_id_or_raw_version, tag_key)
