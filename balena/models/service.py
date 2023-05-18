from typing import Union, List

from . import application as app_module
from ..types import AnyObject
from ..pine import pine
from ..utils import merge
from .. import exceptions
from ..types.models import ServiceType


class Service:
    """
    This class implements service model for balena python SDK.

    """

    def _get(self, id: int, options: AnyObject = {}):
        service = pine.get({"resource": "service", "id": id, "options": options})

        if service is None:
            raise exceptions.ServiceNotFound(id)

        return service

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[ServiceType]:
        """
        Get all services from an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Returns:
            List[ServiceType]: service info.
        """

        app_id = app_module.application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]

        return pine.get({
            "resource": "service",
            "options": merge({
                "$filter": {"application": app_id}
            }, options)
        })
