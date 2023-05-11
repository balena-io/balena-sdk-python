from typing import Any, Optional

from ..pine import pine
from ..types import AnyObject
from ..utils import merge


class BaseTag:
    """
    an abstract implementation for resource tags. This class won't be included in the docs.

    """

    def __init__(self, resource: str):
        self.resource = f"{resource}_tag"
        self.resource_key_field = "tag_key"
        self.parent_resource_name = resource

    def get_all(self, options: AnyObject = {}) -> Any:
        default_orderby = {"$orderby": {}}
        default_orderby["$orderby"][self.resource_key_field] = "asc"

        return pine.get(
            {
                "resource": self.resource,
                "options": merge(default_orderby, options),
            }
        )

    def get_all_by_parent(
        self, parent_param: Any, options: AnyObject = {}
    ) -> Any:
        get_options = {
            "$filter": {},
            "$orderby": f"{self.resource_key_field} asc",
        }
        get_options["$filter"][self.parent_resource_name] = parent_param

        return pine.get(
            {
                "resource": self.resource,
                "options": merge(get_options, options),
            }
        )

    def get(self, parent_param: Any, key: str) -> Optional[str]:
        dollar_filter = {}
        dollar_filter[self.parent_resource_name] = parent_param
        dollar_filter[self.resource_key_field] = key

        result = pine.get(
            {
                "resource": self.resource,
                "options": {"$select": "value", "$filter": dollar_filter},
            }
        )

        if len(result) == 1:
            return result[0].get("value")

    def set(self, parent_param: Any, tag_key: str, value: str):
        upsert_id = {}
        upsert_id[self.parent_resource_name] = parent_param
        upsert_id[self.resource_key_field] = tag_key

        pine.upsert(
            {
                "resource": self.resource,
                "id": upsert_id,
                "body": {"value": value},
            }
        )

    def remove(self, parent_param: Any, tag_key: str):
        dollar_filter = {}
        dollar_filter[self.parent_resource_name] = parent_param
        dollar_filter[self.resource_key_field] = tag_key

        pine.delete(
            {"resource": self.resource, "options": {"$filter": dollar_filter}}
        )
