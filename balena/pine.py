import json
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from pine_client import PinejsClientCore
from pine_client.client import Params

from .balena_auth import get_token
from .exceptions import RequestError
from .settings import settings


class PineClient(PinejsClientCore):
    def __init__(self, params: Params = {}):
        api_url = settings.get("api_endpoint")
        api_version = settings.get("api_version")

        super().__init__({**params, "api_prefix": urljoin(api_url, api_version) + "/"})

    def _request(self, method: str, url: str, body: Optional[Any] = None) -> Any:
        token = get_token()

        headers = {"Content-Type": "application/json"}
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
            print(req.status_code)
            print(req.content)
            raise RequestError(body=req.content, status_code=req.status_code)


pine = PineClient()
