from typing import List, Union

from .. import exceptions
from ..pine import PineClient
from ..settings import Settings
from ..types import AnyObject
from ..types.models import DeviceTypeType
from ..utils import merge


class DeviceType:
    """
    This class implements user API key model for balena python SDK.

    """

    def __init__(self, pine: PineClient, settings: Settings):
        self.__pine = pine
        self.__settings = settings

    def get(self, id_or_slug: Union[str, int], options: AnyObject = {}) -> DeviceTypeType:
        """
        Get a single device type.

        Args:
            id_or_slug (Union[str, int]): device type slug or alias (string) or id (int).
            options (AnyObject): extra pine options to use.

        Returns:
            DeviceTypeType: Returns the device type
        """

        if id_or_slug is None:
            raise exceptions.InvalidDeviceType(id_or_slug)

        if isinstance(id_or_slug, str):
            device_types = self.get_all(
                merge(
                    {
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
                    },
                    options,
                )
            )
            device_type = None
            if len(device_types) > 0:
                device_type = device_types[0]
        else:
            device_type = self.__pine.get(
                {
                    "resource": "device_type",
                    "id": id_or_slug,
                    "options": options,
                }
            )

        if device_type is None:
            raise exceptions.InvalidDeviceType(id_or_slug)

        return device_type

    def get_all(self, options: AnyObject = {}) -> List[DeviceTypeType]:
        """
        Get all device types.

        Args:
            options (AnyObject): extra pine options to use.

        Returns:
            List[DeviceTypeType]: list contains info of device types.
        """
        opts = merge({"$orderby": "name asc"}, options)
        return self.__pine.get(
            {
                "resource": "device_type",
                "options": opts,
            }
        )

    def get_all_supported(self, options: AnyObject = {}):
        """
        Get all supported device types.

        Args:
            options (AnyObject): extra pine options to use.

        Returns:
            List[DeviceTypeType]: list contains info of all supported device types.
        """

        return self.get_all(
            merge(
                {
                    "$filter": {
                        "is_default_for__application": {
                            "$any": {
                                "$alias": "idfa",
                                "$expr": {
                                    "idfa": {
                                        "is_host": True,
                                        "is_archived": False,
                                        "owns__release": {
                                            "$any": {
                                                "$alias": "r",
                                                "$expr": {
                                                    "r": {
                                                        "status": "success",
                                                        "is_final": True,
                                                        "is_invalidated": False,
                                                    }
                                                },
                                            }
                                        },
                                    }
                                },
                            }
                        }
                    }
                },
                options,
            )
        )

    def get_by_slug_or_name(self, slug_or_name: str, options: AnyObject = {}) -> DeviceTypeType:
        """
        Get a single device type by slug or name.

        Args:
            slug_or_name (str): device type slug or name.
            options (AnyObject): extra pine options to use.

        Returns:
            DeviceTypeType: Returns the device type
        """

        device_types = self.get_all(
            merge(
                {
                    "$top": 1,
                    "$filter": {"$or": [{"name": slug_or_name}, {"slug": slug_or_name}]},
                },
                options,
            )
        )

        device_type = device_types[0] if len(device_types) > 0 else None

        if device_type is None:
            raise exceptions.InvalidDeviceType(slug_or_name)

        return device_type

    def get_name(self, slug: str) -> str:
        """
        Get display name for a device.

        Args:
            slug (str): device type slug.

        """

        return self.get_by_slug_or_name(slug, {"$select": "name"})["name"]

    def get_slug_by_name(self, name: str) -> str:
        """
        Get device slug.

        Args:
            name (str): device type name.

        """

        return self.get_by_slug_or_name(name, {"$select": "slug"})["slug"]
