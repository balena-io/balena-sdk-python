import os
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urljoin

import jwt
import requests

from . import exceptions
from .settings import Settings
import balena


def __request_new_token(settings: Settings) -> str:
    headers = {"Authorization": f"Bearer {settings.get('token')}"}
    url = urljoin(settings.get("api_endpoint"), "whoami")
    response = requests.get(url, headers=headers)

    if not response.ok:
        raise exceptions.RequestError(response.content.decode(), response.status_code)

    return response.content.decode()


def __should_update_token(token: str, interval: str) -> bool:
    try:
        # Auth token
        token_data = jwt.decode(token, algorithms=["HS256"], options={"verify_signature": False})
        # dt will be the same as Date.now() in Javascript but converted to
        # milliseconds for consistency with js/sc sdk
        dt = (datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds()
        dt = dt * 1000
        age = dt - (int(token_data["iat"]) * 1000)
        return int(age) >= int(interval)
    except jwt.InvalidTokenError:
        return False


def get_token(settings: Settings) -> Optional[str]:
    if settings.has("token"):
        token = settings.get("token")
        interval = settings.get("token_refresh_interval")
        if __should_update_token(token, interval):
            settings.set("token", __request_new_token(settings))
        api_key = settings.get("token")

    else:
        api_key = os.environ.get("BALENA_API_KEY") or os.environ.get("RESIN_API_KEY")

    return api_key


def request(
    method: str,
    path: str,
    settings: Settings,
    body: Optional[Any] = None,
    endpoint: Optional[str] = None,
    token: Optional[str] = None,
    qs: Optional[Any] = {},
    return_raw: bool = False,
    stream: bool = False,
    send_token: bool = True,
) -> Any:
    if endpoint is None:
        endpoint = settings.get("api_endpoint")

    if token is None and send_token:
        token = get_token(settings)

    url = urljoin(endpoint, path)

    if token is None and send_token:
        raise exceptions.NotLoggedIn()
    try:
        headers = {"X-Balena-Client": f"balena-python-sdk/{balena.__version__}"}
        if send_token:
            headers["Authorization"] = f"Bearer {token}"

        req = requests.request(method=method, url=url, params=qs, json=body, headers=headers, stream=stream)

        if return_raw:
            return req

        try:
            return req.json()
        except Exception:
            return req.content.decode()

    except Exception as e:
        if not send_token:
            raise e
        raise exceptions.NotLoggedIn()
