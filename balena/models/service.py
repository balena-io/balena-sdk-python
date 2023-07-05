from typing import List, Optional, Union

from .. import exceptions
from ..dependent_resource import DependentResource
from ..pine import PineClient
from ..types import AnyObject
from ..types.models import EnvironmentVariableBase, ServiceType
from ..utils import merge
from ..settings import Settings
from .application import Application


class Service:
    """
    This class implements service model for balena python SDK.

    """

    def __init__(self, pine: PineClient, settings: Settings):
        self.__pine = pine
        self.__application = Application(pine, settings, False)
        self.var = ServiceEnvVariable(pine, self, settings)

    def _get(self, id: int, options: AnyObject = {}):
        service = self.__pine.get({"resource": "service", "id": id, "options": options})

        if service is None:
            raise exceptions.ServiceNotFound(id)

        return service

    def get_all_by_application(self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}) -> List[ServiceType]:
        """
        Get all services from an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[ServiceType]: service info.
        """

        app_id = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]

        return self.__pine.get({"resource": "service", "options": merge({"$filter": {"application": app_id}}, options)})


class ServiceEnvVariable(DependentResource[EnvironmentVariableBase]):
    """
    This class implements Service environment variable model for balena python SDK.

    """

    def __init__(self, pine: PineClient, service: Service, settings: Settings):
        self.__service = service
        self.__application = Application(pine, settings, False)
        super(ServiceEnvVariable, self).__init__(
            "service_environment_variable",
            "name",
            "service",
            lambda id: self.__service._get(id, {"$select": "id"})["id"],
            pine,
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
            >>> balena.models.service.var.get_all_by_service(1234)
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
            >>> balena.models.service.var.get_all_by_application(9020)
            >>> balena.models.service.var.get_all_by_application("myorg/myslug")
        """
        app_id = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]

        return super(ServiceEnvVariable, self)._get_all(
            merge(
                {
                    "$filter": {
                        "service": {
                            "$any": {
                                "$alias": "s",
                                "$expr": {"s": {"application": app_id}},
                            }
                        }
                    },
                    "$orderby": "name asc",
                },
                options,
            )
        )

    def get(self, id: int, key: str) -> Optional[str]:
        """
        Get the value of a specific service variable

        Args:
            id (int): service id
            key (str): variable name

        Examples:
            >>> balena.models.service.var.get(1234,'test_env4')
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
            >>> balena.models.service.var.set(1234,'test_env4', 'value')
        """
        id = self.__service._get(id, {"$select": "id"})["id"]
        super(ServiceEnvVariable, self)._set(id, key, value)

    def remove(self, id: int, key: str) -> None:
        """
        Clear the value of a specific service variable

        Args:
            id (int): service id
            key (str): variable name

        Examples:
            >>> balena.models.service.var.remove(1234,'test_env4')
        """
        super(ServiceEnvVariable, self)._remove(id, key)
