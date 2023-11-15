from typing import Any, Optional, cast
from urllib.parse import urljoin
from ratelimit import limits, sleep_and_retry
from time import sleep
import mimetypes
import io
import requests
import os
from pine_client import PinejsClientCore
from pine_client.client import Params

from .balena_auth import get_token
from .exceptions import RequestError, InvalidOption
from .settings import Settings


class PineClient(PinejsClientCore):
    def __init__(self, settings: Settings, sdk_version: str, params: Optional[Params] = None):
        if params is None:
            params = {}

        self.__settings = settings
        self.__sdk_version = sdk_version

        api_url = cast(str, settings.get("api_endpoint"))
        api_version = cast(str, settings.get("api_version"))

        try:
            calls = int(self.__settings.get("request_limit"))
            period = int(self.__settings.get("request_limit_interval"))

            self.__request = sleep_and_retry(limits(calls=calls, period=period)(self.__base_request))
        except InvalidOption:
            self.__request = self.__base_request

        super().__init__({**params, "api_prefix": urljoin(api_url, api_version) + "/"})

    def _request(self, method: str, url: str, body: Optional[Any] = None) -> Any:
        return self.__request(method, url, body)

    def __base_request(self, method: str, url: str, body: Optional[Any] = None) -> Any:
        token = get_token(self.__settings)

        headers = {"X-Balena-Client": f"balena-python-sdk/{self.__sdk_version}"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        is_multipart_form_data = False
        files = {}
        values = {}
        if body is not None:
            for k, v in body.items():
                if isinstance(v, io.BufferedReader):
                    mimetype, _ = mimetypes.guess_type(v.name)
                    files[k] = (os.path.basename(v.name), v, mimetype)
                    is_multipart_form_data = True
                else:
                    values[k] = v

        if is_multipart_form_data:
            req = requests.request(method, url=url, files=files, data=values, headers=headers)
        else:
            req = requests.request(method, url=url, json=body, headers=headers)

        if req.ok:
            try:
                return req.json()
            except Exception:
                return req.content.decode()
        else:
            retry_after = req.headers.get("retry-after")
            if (
                self.__settings.get("retry_rate_limited_request") is True
                and req.status_code == 429
                and retry_after is not None
                and retry_after.isdigit()
            ):
                sleep(int(retry_after))
                return self.__base_request(method, url, body)

            raise RequestError(body=req.content.decode(), status_code=req.status_code)
