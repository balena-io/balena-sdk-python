from typing import List, Optional, Union, cast, TypedDict

from .. import exceptions
from ..dependent_resource import DependentResource
from ..pine import PineClient
from ..types import AnyObject
from ..types.models import EnvironmentVariableBase, ServiceType
from ..utils import merge
from ..settings import Settings
from .application import Application


class ServiceNaturalKey(TypedDict):
    application: Union[str, int]
    service_name: str


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

        services = self.__application.get(slug_or_uuid_or_id, {"$select": "service", "$expand": {"service": options}})[
            "service"
        ]

        return cast(List[ServiceType], services)


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
            self.__get_resource_id,
            pine,
        )

    def __get_resource_id(self, resource_id: Union[int, ServiceNaturalKey]):
        if resource_id is not None and isinstance(resource_id, dict):
            keys = resource_id.keys()
            if len(keys) != 2 or "application" not in keys or "service_name" not in keys:
                raise Exception(f"Unexpected type for id provided in service var model get resource id: {resource_id}")

            service = self.__service.get_all_by_application(
                resource_id["application"], {"$select": "id", "$filter": {"service_name": resource_id["service_name"]}}
            )[0]

            if service is None:
                raise exceptions.ServiceNotFound(resource_id["service_name"])

            return service["id"]
        if not isinstance(resource_id, int):
            raise Exception(f"Unexpected type for id provided in service varModel getResourceId: {resource_id}")
        return self.__service._get(resource_id, {"$select": "id"})["id"]

    def get_all_by_service(
        self, service_id_or_natural_key: Union[int, ServiceNaturalKey], options: AnyObject = {}
    ) -> List[EnvironmentVariableBase]:
        """
        Get all variables for a service.

        Args:
            service_id_or_natural_key (Union[int, ServiceNaturalKey]): service id (number) or appliation-service_name
            options (AnyObject): extra pine options to use

        Returns:
            List[EnvironmentVariableBase]: service environment variables.

        Examples:
            >>> balena.models.service.var.get_all_by_service(1234)
            >>> balena.models.service.var.get_all_by_service({'application': 'myorg/myapp', 'service_name': 'service'})
        """
        return super(ServiceEnvVariable, self)._get_all_by_parent(service_id_or_natural_key, options)

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

    def get(self, service_id_or_natural_key: Union[int, ServiceNaturalKey], key: str) -> Optional[str]:
        """
        Get the value of a specific service variable

        Args:
            service_id_or_natural_key (Union[int, ServiceNaturalKey]): service id (number) or appliation-service_name
            key (str): variable name

        Examples:
            >>> balena.models.service.var.get(1234,'test_env4')
            >>> balena.models.service.var.get({'application': 'myorg/myapp', 'service_name': 'service'}, 'VAR')
        """
        return super(ServiceEnvVariable, self)._get(service_id_or_natural_key, key)

    def set(self, service_id_or_natural_key: Union[int, ServiceNaturalKey], key: str, value: str) -> None:
        """
        Set the value of a specific application environment variable.

        Args:
            service_id_or_natural_key (Union[int, ServiceNaturalKey]): service id (number) or appliation-service_name
            key (str): variable name
            value (str): environment variable value.

        Examples:
            >>> balena.models.service.var.set({'application': 'myorg/myapp', 'service_name': 'service'}, 'VAR', 'value')
            >>> balena.models.service.var.set(1234,'test_env4', 'value')
        """
        super(ServiceEnvVariable, self)._set(service_id_or_natural_key, key, value)

    def remove(self, service_id_or_natural_key: Union[int, ServiceNaturalKey], key: str) -> None:
        """
        Clear the value of a specific service variable

        Args:
            service_id_or_natural_key (Union[int, ServiceNaturalKey]): service id (number) or appliation-service_name
            key (str): variable name

        Examples:
            >>> balena.models.service.var.remove({'application': 'myorg/myapp', 'service_name': 'service'}, 'VAR')
            >>> balena.models.service.var.remove(1234,'test_env4')
        """
        super(ServiceEnvVariable, self)._remove(service_id_or_natural_key, key)
