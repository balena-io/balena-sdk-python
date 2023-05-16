from typing import Union, List, Optional

from ..dependent_resource import DependentResource
from ..types import AnyObject
from ..types.models import EnvironmentVariableBase
from ..utils import merge
from .application import Application

from .device import Device


class ConfigVariable:
    """
    This class is a wrapper for config variable models.

    """

    def __init__(self):
        self.device_config_variable = DeviceConfigVariable()
        self.application_config_variable = ApplicationConfigVariable()


class DeviceConfigVariable(DependentResource[EnvironmentVariableBase]):
    """
    This class implements device config variable model for balena python SDK.

    """

    def __init__(self):
        self.device = Device()
        self.application = Application()
        super(DeviceConfigVariable, self).__init__(
            "device_config_variable",
            "name",
            "device",
            lambda id: self.device.get(id, {"$select": "id"})["id"],
        )

    def get_all_by_device(
        self, uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[EnvironmentVariableBase]:
        """
        Get all device config variables belong to a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: device config variables.

        Examples:
            >>> balena.models.config_variable.device_config_variable.get_all_by_device('f5213ea')
        """
        return super(DeviceConfigVariable, self)._get_all_by_parent(
            uuid_or_id, options
        )

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
            >>> balena.models.config_variable.device_config_variable.device.get_all_by_application(5780)
        """
        app_id = self.application.get(slug_or_uuid_or_id, {"$select": "id"})[
            "id"
        ]
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

    def get(
        self, uuid_or_id: Union[str, int], env_var_name: str
    ) -> Optional[str]:
        """
        Get a device config variable.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            env_var_name (str): environment variable name.

        Examples:
            >>> balena.models.config_variable.device_config_variable.device.get('8deb12','test_env4')
        """
        return super(DeviceConfigVariable, self)._get(uuid_or_id, env_var_name)

    def set(
        self, uuid_or_id: Union[str, int], env_var_name: str, value: str
    ) -> None:
        """
        Set the value of a device config variable.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Examples:
            >>> balena.models.config_variable.device_config_variable.device.set('8deb12','test_env4', 'testing1')
        """
        super(DeviceConfigVariable, self)._set(uuid_or_id, env_var_name, value)

    def remove(self, uuid_or_id: Union[str, int], key: str) -> None:
        """
        Remove a device environment variable.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Examples:
            >>> balena.models.config_variable.device_config_variable.device.remove(2184)
        """
        super(DeviceConfigVariable, self)._remove(uuid_or_id, key)


class ApplicationConfigVariable(DependentResource[EnvironmentVariableBase]):
    """
    This class implements application config variable model for balena python SDK.

    """

    def __init__(self):
        self.application = Application()
        super(ApplicationConfigVariable, self).__init__(
            "application_config_variable",
            "name",
            "application",
            lambda id: self.application.get(id, {"$select": "id"})["id"],
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
            >>> balena.models.config_variable.device_config_variable.application.get_all_by_application(9020)
        """
        return super(ApplicationConfigVariable, self)._get_all_by_parent(slug_or_uuid_or_id, options)

    def get(self, slug_or_uuid_or_id: Union[str, int], env_var_name: str) -> Optional[str]:
        """
        Get application config variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            env_var_name (str): environment variable name.

        Examples:
            >>> balena.models.config_variable.device_config_variable.application.get('8deb12','test_env4')
        """
        return super(ApplicationConfigVariable, self)._get(slug_or_uuid_or_id, env_var_name)

    def set(
        self, slug_or_uuid_or_id: Union[str, int], env_var_name: str, value: str
    ) -> None:
        """
        Set the value of a specific application config variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Examples:
            >>> balena.models.config_variable.device_config_variable.application.set('8deb12','test_env', 'testing1')
        """
        super(ApplicationConfigVariable, self)._set(slug_or_uuid_or_id, env_var_name, value)

    def remove(self, slug_or_uuid_or_id: Union[str, int], key: str) -> None:
        """
        Remove an application config variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)

        Examples:
            >>> balena.models.config_variable.device_config_variable.application.remove(2184)
        """
        super(ApplicationConfigVariable, self)._remove(slug_or_uuid_or_id, key)
