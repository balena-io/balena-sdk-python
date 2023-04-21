from ..base_request import BaseRequest
from ..settings import Settings
from ..auth import Auth
from .. import exceptions
from .application import Application
from .device import Device


class ApiKey:
    """
    This class implements user API key model for balena python SDK.

    """

    def __init__(self):
        self.application = Application()
        self.auth = Auth()
        self.base_request = BaseRequest()
        self.device = Device()
        self.settings = Settings()

    def __get_all_with_filter(self, filters):
        return self.base_request.request(
            "api_key",
            "GET",
            params=filters,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    def create_api_key(self, name, description=None):
        """
        This function registers a new api key for the current user with the name given.

        Args:
            name (str): user API key name.
            description (Optional[str]): API key description.

        Returns:
            str: user API key.

        Examples:
            >>> balena.models.api_key.create_api_key('myApiKey')
            3YHD9DVPLe6LbjEgQb7FEFXYdtPEMkV9

        """

        data = {"name": name, "description": description}

        return self.base_request.request(
            "/api-key/user/full",
            "POST",
            data=data,
            endpoint=self.settings.get("api_endpoint"),
        )

    def get_all(self):
        """
        This function gets all API keys.

        Returns:
            list: user API key.

        Examples:
            >>> balena.models.api_key.get_all()
            [
                {
                    "description": None,
                    "created_at": "2018-04-06T03:53:34.189Z",
                    "__metadata": {"type": "", "uri": "/balena/api_key(1296047)"},
                    "is_of__actor": {
                        "__deferred": {"uri": "/balena/actor(2454095)"},
                        "__id": 2454095,
                    },
                    "id": 1296047,
                    "name": "myApiKey",
                }
            ]


        """

        return self.base_request.request("api_key", "GET", endpoint=self.settings.get("pine_endpoint"))["d"]

    def update(self, id, api_key_info):
        """
        This function updates details of an API key.

        Args:
            id (str): API key id.
            api_key_info: new API key info.
                name (str): new API key name.
                description (Optional[str]): new API key description.

        Examples:
            >>> balena.models.api_key.update(1296047, {'name':'new name')
            OK

        """

        data = api_key_info
        params = {"filter": "id", "eq": id}

        return self.base_request.request(
            "api_key",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def revoke(self, id):
        """
        This function revokes an API key.

        Args:
            id (str): API key id.

        Examples:
            >>> balena.models.api_key.revoke(1296047)
            OK

        """

        params = {"filter": "id", "eq": id}

        return self.base_request.request(
            "api_key",
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def get_provisioning_api_keys_by_application(self, app_id):
        """
        Get all provisioning API keys for an application.

        Args:
            app_id (str): application id.

        Examples:
            >>> balena.models.api_key.get_provisioning_api_keys_by_application(1296047)
            [
                {
                    "id": 5492033,
                    "created_at": "2021-12-29T03:38:04.470Z",
                    "is_of__actor": {
                        "__id": 6444453,
                        "__deferred": {"uri": "/resin/actor(@id)?@id=6444453"},
                    },
                    "name": None,
                    "description": None,
                    "__metadata": {"uri": "/resin/api_key(@id)?@id=5492033"},
                },
                {
                    "id": 5492044,
                    "created_at": "2021-12-29T03:41:04.441Z",
                    "is_of__actor": {
                        "__id": 6444453,
                        "__deferred": {"uri": "/resin/actor(@id)?@id=6444453"},
                    },
                    "name": "key p1",
                    "description": "key desc",
                    "__metadata": {"uri": "/resin/api_key(@id)?@id=5492044"},
                },
                {
                    "id": 3111481,
                    "created_at": "2020-06-25T04:24:53.621Z",
                    "is_of__actor": {
                        "__id": 6444453,
                        "__deferred": {"uri": "/resin/actor(@id)?@id=6444453"},
                    },
                    "name": None,
                    "description": None,
                    "__metadata": {"uri": "/resin/api_key(@id)?@id=3111481"},
                },
            ]
        """

        app = self.application.get_by_id(app_id)

        params = {"filter": "is_of__actor", "eq": app["actor"]}

        return self.__get_all_with_filter(params)

    def get_device_api_keys_by_device(self, device_uuid):
        """
        Get all API keys for a device.

        Args:
            device_uuid (str): device uuid.

        Examples:
            >>> balena.models.api_key.get_device_api_keys_by_device('44cc9d1861b9f992808c506276e5d31d')
            [
                {
                    "id": 3111484,
                    "created_at": "2020-06-25T04:33:33.069Z",
                    "is_of__actor": {
                        "__id": 6444456,
                        "__deferred": {"uri": "/resin/actor(@id)?@id=6444456"},
                    },
                    "name": None,
                    "description": None,
                    "__metadata": {"uri": "/resin/api_key(@id)?@id=3111484"},
                }
            ]

        """

        device = self.device.get(device_uuid)

        params = {"filter": "is_of__actor", "eq": device["actor"]}

        return self.__get_all_with_filter(params)

    def get_all_named_user_api_keys(self):
        """
        Get all named user API keys of the current user.

        Examples:
            >>> balena.models.api_key.get_all_named_user_api_keys()
            [
                {
                    "id": 2452013,
                    "created_at": "2019-11-12T09:48:42.437Z",
                    "is_of__actor": {
                        "__id": 113809,
                        "__deferred": {"uri": "/resin/actor(@id)?@id=113809"},
                    },
                    "name": "test",
                    "description": None,
                    "__metadata": {"uri": "/resin/api_key(@id)?@id=2452013"},
                }
            ]

        """

        if self.auth.is_logged_in():
            user = self.auth._Auth__get_full_user_data()
            raw_query = "$filter=is_of__actor%20eq%20'{actor}'%20and%20name%20ne%20null".format(actor=user["actor"])

            return self.base_request.request(
                "api_key",
                "GET",
                raw_query=raw_query,
                endpoint=self.settings.get("pine_endpoint"),
            )["d"]
        else:
            raise exceptions.NotLoggedIn()
