from typing import Any, Union

from .. import exceptions
from ..base_request import BaseRequest
from ..pine import pine
from ..settings import Settings
from ..types import AnyObject
from ..utils import merge


class DeviceType(object):
    """
    This class implements user API key model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def get_all(self, options: AnyObject = {}) -> Any:
        """
        Get all device types.

        Args:
            options (AnyObject): extra pine options to use.

        Returns:
            list: list contains info of device types.

        """
        return pine.get({
            "resource": "device_type",
            "options": merge({"$orderby": "name asc"}, options),
        })

    def get_all_supported(self):
        """
        Get all supported device types.

        Returns:
            list: list contains info of all supported device types.

        """

        # fmt: off
        raw_query = (
            "$expand=is_of__cpu_architecture($select=slug,id)"
            "&$filter="
                "is_default_for__application/any(idfa:idfa/is_host%20eq%20true%20and%20is_archived%20eq%20false)"
        )
        # fmt: on

        return self.base_request.request(
            "device_type",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    def get(self, id_or_slug: Union[str, int], options: AnyObject = {}) -> Any:
        """
        Get a single device type.

        Args:
            id_or_slug (Union[str, int]): device type slug or alias (string) or id (int).
            options (AnyObject): extra pine options to use.
        """

        if id_or_slug is None:
            raise exceptions.InvalidDeviceType(id_or_slug)

        if isinstance(id_or_slug, str):
            device_types = self.get_all(merge({
                "$top": 1,
                "$filter": {
                    "device_type_alias": {
                        "$any": {
                            "$alias": "dta",
                            "$expr": {
                                "dta": {
                                    "is_referenced_by__alias": id_or_slug,
                                },
                            },
                        },
                    },
                },
            }, options))
            device_type = None
            if len(device_types) > 0:
                device_type = device_types[0]
        else:
            device_type = pine.get({
                "resource": "device_type",
                "id": id_or_slug,
                "options": options
            })

        if device_type is None:
            raise exceptions.InvalidDeviceType(id_or_slug)

        return device_type

    def get_by_slug_or_name(self, slug_or_name):
        """
        Get a single device type by slug or name.

        Args:
            slug_or_name (str): device type slug or name.

        """

        raw_query = (
            "$top=1"
            "&$expand=is_of__cpu_architecture($select=slug,id)"
            f"&$filter=name%20eq%20'{slug_or_name}'%20or%20slug%20eq%20'{slug_or_name}'"
        )

        device_type = self.base_request.request(
            "device_type",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

        if not device_type:
            raise exceptions.InvalidDeviceType(slug_or_name)

        return device_type[0]

    def get_name(self, slug):
        """
        Get display name for a device.

        Args:
            slug (str): device type slug.

        """

        return self.get_by_slug_or_name(slug)["name"]

    def get_slug_by_name(self, name):
        """
        Get device slug.

        Args:
            name (str): device type name.

        """

        return self.get_by_slug_or_name(name)["slug"]
