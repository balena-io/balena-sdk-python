from typing import Union, List, Optional


from .. import exceptions
from .application import Application
from ..types.models import EnvironmentVariableBase
from ..types import AnyObject
from ..dependent_resource import DependentResource
from ..utils import merge, is_id, is_full_uuid
from ..pine import pine
from .device import Device
from .service import Service


class EnvironmentVariable:
    """
    This class is a wrapper for environment variable models.

    """

    def __init__(self):
        self.application = ApplicationEnvVariable()
        self.device = DeviceEnvVariable()
        self.device_service = DeviceServiceEnvVariable()
        self.service = ServiceEnvVariable()


class DeviceEnvVariable(DependentResource[EnvironmentVariableBase]):
    """
    This class implements device environment variable model for balena python SDK.

    """

    def __init__(self):
        self.device = Device()
        self.application = Application()
        super(DeviceEnvVariable, self).__init__(
            "device_environment_variable",
            "name",
            "device",
            lambda id: self.device.get(id, {"$select": "id"})["id"],
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
            >>> balena.models.environment_variables.device.get_all_by_device('8deb12a')
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
            >>> balena.models.environment_variables.device.get_all_by_application(5780)
        """
        app_id = self.application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]
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
            >>> balena.models.environment_variables.device.get('8deb12','test_env4')
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
            >>> balena.models.environment_variables.device.set('8deb12','test_env4', 'testing1')
        """
        super(DeviceEnvVariable, self)._set(uuid_or_id, env_var_name, value)

    def remove(self, uuid_or_id: Union[str, int], key: str) -> None:
        """
        Remove a device environment variable.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)

        Examples:
            >>> balena.models.environment_variables.device.remove(2184)
        """
        super(DeviceEnvVariable, self)._remove(uuid_or_id, key)


class DeviceServiceEnvVariable:
    """
    This class implements device service variable model for balena python SDK.
    """

    def __init__(self):
        self.device = Device()
        self.application = Application()

    def get_all_by_device(self, uuid_or_id: Union[str, int], options: AnyObject = {}) -> List[EnvironmentVariableBase]:
        """
        Get all device environment variables.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: device service environment variables.

        Examples:
            >>> balena.models.environment_variables.device_service.get_all_by_device(8deb12a)
        """
        device_id = self.device.get(uuid_or_id, {"$select": "id"})["id"]
        return pine.get(
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
            >>> balena.models.environment_variables.device_service.get_all_by_application(1043050)
        """
        app_id = self.application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]

        return pine.get(
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

    def get(self, uuid_or_id: Union[str, int], service_id: int, key: str) -> Optional[str]:
        """
        Get the overriden value of a service variable on a device

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            service_id (int): service id
            key (str): variable name

        Returns:
           Optional[str]: device service environment variables.

        Examples:
            >>> balena.models.environment_variables.device_service.get('8deb12a', 1234', 'VAR')
        """
        device_id = self.device.get(uuid_or_id, {"$select": "id"})["id"]
        variables = pine.get(
            {
                "resource": "device_service_environment_variable",
                "options": {
                    "$select": "value",
                    "$filter": {
                        "service_install": {
                            "$any": {
                                "$alias": "si",
                                "$expr": {
                                    "si": {
                                        "device": device_id,
                                        "installs__service": service_id,
                                    }
                                },
                            }
                        },
                        "name": key,
                    },
                },
            }
        )

        if isinstance(variables, list) and len(variables) == 1:
            return variables[0].get("value")

    def set(self, uuid_or_id: Union[str, int], service_id: int, key: str, value: str) -> None:
        """
        Set the overriden value of a service variable on a device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            service_id (int): service id
            key (str): variable name
            value (str): variable value

        Examples:
            >>> balena.models.environment_variables.device_service.set('7cf02a6', 123, 'VAR', 'override')
        """

        if is_id(uuid_or_id):
            device_filter = uuid_or_id
        elif is_full_uuid(uuid_or_id):
            device_filter = {"$any": {"$alias": "d", "$expr": {"d": {"uuid": uuid_or_id}}}}
        else:
            device_filter = self.device.get(uuid_or_id, {"$select": "id"})["id"]

        service_installs = pine.get(
            {
                "resource": "service_install",
                "options": {
                    "$select": "id",
                    "$filter": {
                        "device": device_filter,
                        "installs__service": service_id,
                    },
                },
            }
        )

        if (
            service_installs is None
            or (isinstance(service_installs, list) and len(service_installs) == 0)
            or service_installs[0] is None
        ):
            raise exceptions.ServiceNotFound(service_id)

        if len(service_installs) > 1:
            raise exceptions.AmbiguousDevice(uuid_or_id)

        pine.upsert(
            {
                "resource": "device_service_environment_variable",
                "id": {"service_install": service_installs[0]["id"], "name": key},
                "body": {"value": value},
            }
        )

    def remove(self, uuid_or_id: Union[str, int], service_id: int, key: str) -> None:
        """
        Remove a device service environment variable.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            service_id (int): service id
            key (str): variable name

        Examples:
            >>> balena.models.environment_variables.device_service.remove(28970)
        """

        device_id = self.device.get(uuid_or_id, {"$select": "id"})["id"]
        pine.delete(
            {
                "resource": "device_service_environment_variable",
                "options": {
                    "$filter": {
                        "service_install": {
                            "$any": {"$alias": "si", "$expr": {"si": {"device": device_id, "service": service_id}}}
                        },
                        "name": key,
                    }
                },
            }
        )


class ApplicationEnvVariable(DependentResource[EnvironmentVariableBase]):
    """
    This class implements application environment variable model for balena python SDK.

    """

    def __init__(self):
        self.application = Application()
        super(ApplicationEnvVariable, self).__init__(
            "application_environment_variable",
            "name",
            "application",
            lambda id: self.application.get(id, {"$select": "id"})["id"],
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
            >>> balena.models.environment_variables.application.get_all_by_application(9020)
            >>> balena.models.environment_variables.application.get_all_by_application("myorg/myslug")
        """
        return super(ApplicationEnvVariable, self)._get_all_by_parent(slug_or_uuid_or_id, options)

    def get(self, slug_or_uuid_or_id: Union[str, int], env_var_name: str) -> Optional[str]:
        """
        Get application environment variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            env_var_name (str): environment variable name.

        Examples:
            >>> balena.models.environment_variables.application.get('8deb12','test_env4')
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
            >>> balena.models.environment_variables.application.set('8deb12','test_env4', 'testing1')
        """
        super(ApplicationEnvVariable, self)._set(slug_or_uuid_or_id, env_var_name, value)

    def remove(self, slug_or_uuid_or_id: Union[str, int], key: str) -> None:
        """
        Remove an application environment variable.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)

        Examples:
            >>> balena.models.environment_variables.application.remove(2184)
        """
        super(ApplicationEnvVariable, self)._remove(slug_or_uuid_or_id, key)


class ServiceEnvVariable(DependentResource[EnvironmentVariableBase]):
    """
    This class implements Service environment variable model for balena python SDK.

    """

    def __init__(self):
        self.service = Service()
        self.application = Application()
        super(ServiceEnvVariable, self).__init__(
            "service_environment_variable",
            "name",
            "service",
            lambda id: self.service._get(id, {"$select": "id"})["id"],
        )

    def get_all_by_service(self, id: int, options: AnyObject = {}) -> List[EnvironmentVariableBase]:
        """
        Get all variables for a service.

        Args:
            id (int): service id
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: service environment variables.

        Examples:
            >>> balena.models.environment_variables.service.get_all_by_service(1234)
        """
        return super(ServiceEnvVariable, self)._get_all_by_parent(id, options)

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[EnvironmentVariableBase]:
        """
        Get all service variables by application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: application environment variables.

        Examples:
            >>> balena.models.environment_variables.service.get_all_by_application(9020)
            >>> balena.models.environment_variables.service.get_all_by_application("myorg/myslug")
        """
        app_id = self.application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]

        return super(ServiceEnvVariable, self)._get_all(
            merge({
                "$filter": {
                    "service": {
                        "$any": {
                            "$alias": "s",
                            "$expr": {
                                "s": {
                                    "application": app_id
                                }
                            },
                        }
                    }
                },
                "$orderby": "name asc",
            }, options)
        )

    def get(self, id: int, key: str) -> Optional[str]:
        """
        Get the value of a specific service variable

        Args:
            id (int): service id
            key (str): variable name

        Examples:
            >>> balena.models.environment_variables.service.get(1234,'test_env4')
        """
        return super(ServiceEnvVariable, self)._get(id, key)

    def set(self, id: int, key: str, value: str) -> None:
        """
        Set the value of a specific application environment variable.

        Args:
            id (int): service id
            key (str): variable name
            value (str): environment variable value.

        Examples:
            >>> balena.models.environment_variables.service.set(1234,'test_env4', 'value')
        """
        super(ServiceEnvVariable, self)._set(id, key, value)

    def remove(self, id: int, key: str) -> None:
        """
        Clear the value of a specific service variable

        Args:
            id (int): service id
            key (str): variable name

        Examples:
            >>> balena.models.environment_variables.service.remove(1234,'test_env4')
        """
        super(ServiceEnvVariable, self)._remove(id, key)
