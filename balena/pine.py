import json
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from pine_client import PinejsClientCore
from pine_client.client import Params

from .balena_auth import get_token
from .exceptions import RequestError
from .settings import Settings


class PineClient(PinejsClientCore):
    def __init__(self, settings: Settings, sdk_version: str, params: Optional[Params] = None):
        if params is None:
            params = {}

        self.__settings = settings
        self.__sdk_version = sdk_version

        api_url = settings.get("api_endpoint")
        api_version = settings.get("api_version")

        super().__init__({**params, "api_prefix": urljoin(api_url, api_version) + "/"})

    def _request(self, method: str, url: str, body: Optional[Any] = None) -> Any:
        token = get_token(self.__settings)

        headers = {"Content-Type": "application/json", "X-Balena-Client": f"balena-python-sdk/{self.__sdk_version}"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        data = None
        if body is not None:
            data = json.dumps(body)

        req = requests.request(method, url=url, data=data, headers=headers)

        if req.ok:
            try:
                return req.json()
            except Exception:
                return req.content.decode()
        else:
            raise RequestError(body=req.content.decode(), status_code=req.status_code)
