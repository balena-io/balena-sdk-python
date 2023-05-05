from typing import List, Optional, Union
from urllib.parse import urljoin

import requests
from deprecated import deprecated

from .. import exceptions
from ..auth import Auth
from ..balena_auth import get_token
from ..pine import pine
from ..settings import settings
from ..types import AnyObject
from ..types.models import APIKeyInfoType, APIKeyType
from ..utils import merge
from .application import Application
from .device import Device


class ApiKey:
    """
    This class implements user API key model for balena python SDK.

    """

    def __init__(self):
        self.application = Application()
        self.auth = Auth()
        self.device = Device()

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        expiry_date: Optional[str] = None,
    ) -> str:
        """
        This method registers a new api key for the current user with the name given.

        Args:
            name (str): the API key name
            description (Optional[str]): the API key description
            expiry_date (Optional[str]): the API key expiring date

        Returns:
            str: API key

        Examples:
            >>> balena.models.api_key.create_api_key("myApiKey")
            >>> balena.models.api_key.create_api_key("myApiKey", "my api key description")
        """
        api_key_body = {"name": name}

        if description is not None and isinstance(description, str):
            api_key_body["description"] = description

        if expiry_date is not None and isinstance(expiry_date, str):
            api_key_body["expiry_date"] = expiry_date

        token = get_token()

        if token is None:
            raise exceptions.NotLoggedIn()
        try:
            req = requests.post(
                url=urljoin(settings.get("pine_endpoint"), "/api-key/user/full"),
                json=api_key_body,
                headers={"Authorization": f"Bearer {token}"},
            )
            return req.content.decode()
        except Exception:
            raise exceptions.NotLoggedIn()

    @deprecated(reason="This function is deprecated, use 'balena.models.api_key.create' instead")
    def create_api_key(self, name: str, description: Optional[str] = None) -> str:
        """
        DEPRECATED: Please use balena.models.api_key.create instead.
        """
        return self.create(name, description)

    def get_all(self, options: AnyObject = {}) -> List[APIKeyType]:
        """
        This function gets all API keys.

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[APIKeyType]: user API key

        Examples:
            >>> balena.models.api_key.get_all()

        """
        return pine.get(
            {"resource": "api_key", "options": merge({"$orderby": "name asc"}, options)}
        )

    def update(self, id: int, api_key_info: APIKeyInfoType):
        """
        This function updates details of an API key.

        Args:
            id (str): API key id.
            api_key_info (APIKeyInfoType): new API key info.

        Examples:
            >>> balena.models.api_key.update(1296047, {"name":"new name"})

        """

        if api_key_info is None:
            raise exceptions.InvalidParameter("apiKeyInfo", api_key_info)

        if api_key_info.get("name") is not None and api_key_info.get("name") == "":
            raise exceptions.InvalidParameter(
                "apiKeyInfo.name", api_key_info.get("name")
            )

        body = {
            "description": api_key_info.get("description"),
            "expiry_date": api_key_info.get("expiry_date")
        }

        name = api_key_info.get("name")
        if name is not None:
            body["name"] = name

        pine.patch({"resource": "api_key", "id": id, "body": body})

    def revoke(self, id: int):
        """
        This function revokes an API key.

        Args:
            id (int): API key id.

        Examples:
            >>> balena.models.api_key.revoke(1296047)

        """

        pine.delete({"resource": "api_key", "id": id})

    def get_provisioning_api_keys_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[APIKeyType]:
        """
        Get all provisioning API keys for an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            options (AnyObject): extra pine options to use

        Examples:
            >>> balena.models.api_key.get_provisioning_api_keys_by_application(1296047)
            >>> balena.models.api_key.get_provisioning_api_keys_by_application("myorg/myapp")
        """

        app = self.application.get(slug_or_uuid_or_id, {"$select": "actor"})
        return self.get_all(merge({"$filter": {"is_of__actor": app.get("actor")}}, options))

    def get_device_api_keys_by_device(
        self, uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[APIKeyType]:
        """
        Get all API keys for a device.

        Args:
            device_uuid (Union[str, int]): device, uuid (string) or id (int)
            options (AnyObject): extra pine options to use

        Examples:
            >>> balena.models.api_key.get_device_api_keys_by_device("44cc9d1861b9f992808c506276e5d31d")
            >>> balena.models.api_key.get_device_api_keys_by_device(1111386)
        """

        dev = self.device.get(uuid_or_id, {"$select": "actor"})
        return self.get_all(merge({"$filter": {"is_of__actor": dev["actor"]}}, options))

    def get_all_named_user_api_keys(self, options: AnyObject = {}) -> List[APIKeyType]:
        """
        Get all named user API keys of the current user.

        Args:
            options (AnyObject): extra pine options to use

        Examples:
            >>> balena.models.api_key.get_all_named_user_api_keys()
        """

        return self.get_all(
            merge(
                {
                    "$filter": {
                        "is_of__actor": self.auth.get_user_actor_id(),
                        "name": {"$ne": None},
                    }
                },
                options,
            )
        )
