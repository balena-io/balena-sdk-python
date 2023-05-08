import json
import re

from .. import exceptions
from ..base_request import BaseRequest
from ..settings import Settings


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
