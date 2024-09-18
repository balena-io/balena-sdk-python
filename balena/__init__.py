"""
Welcome to the balena python SDK documentation.
This document aims to describe all the functions supported by the SDK, as well as
showing examples of their expected usage.

Install the Balena SDK:

From Pip:
```
pip install balena-sdk
```

From Source (In case, you want to test a development branch):
```
https://github.com/balena-io/balena-sdk-python
```

Getting started:

```python
>>> from balena import Balena
>>> balena = Balena()
>>> credentials = {'username':<your email>, 'password':<your password>}
>>> balena.auth.login(**credentials)
...
```

The Balena object can be configured with a dict of type Settings

```python
balena = Balena({
    "balena_host": "balena-cloud.com",
    "api_version": "v7",
    "device_actions_endpoint_version": "v1",
    "data_directory": "/home/example/.balena",
    "image_cache_time": str(1 * 1000 * 60 * 60 * 24 * 7), # 1 week
    "token_refresh_interval": str(1 * 1000 * 60 * 60),    # 1 hour
    "timeout": str(30 * 1000),                            # request timeout, 30s
    "request_limit": str(300), # the number of requests per request_limit_interval that the SDK should respect, defaults to unlimited.
    "request_limit_interval": str(60), # the timespan that the request_limit should apply to in seconds, defaults to 60s (1 minute).
    "retry_rate_limited_request": False, # awaits and retry once a request is rate limited (429)
})
```

Notice that if you want to change for the staging environment, you could simply do:
balena = Balena({"balena_host": "balena-staging.com"})

However, this will overwrite your balena-cloud settings (stored api keys etc). So we recommend using
a different data_directory for each balena-sdk instance, e.g:

```python
balena_prod = Balena()
balena_staging = Balena({
    "balena_host": "balena-staging.com",
    "data_directory": "/home/balena-staging-sdk/.balena",
})
```

In adition, you can also run balena-python-sdk completely in memory, without writing anything to the file system like:

```python
balena_prod = Balena({"data_directory": False})
balena_staging = Balena({
    "balena_host": "balena-staging.com",
    "data_directory": False
})
```

By default the SDK will throw once a request is Rate limited by the API (with a 429 status code).
A 429 request will contain a header called "retry-after" which informs how long the client should wait before trying a new request.
If you would like the SDK to use this header and wait and automatically retry the request, just do:

```python
balena = Balena({"retry_rate_limited_request": True})
```

If you feel something is missing, not clear or could be improved, [please don't
hesitate to open an issue in GitHub](https://github.com/balena-io/balena-sdk-python/issues), we'll be happy to help.
"""  # noqa: E501

from typing import Optional
from .auth import Auth
from .logs import Logs
from .models import Models
from .pine import PineClient
from .settings import SettingsConfig, Settings

__version__ = "15.0.0"


class Balena:
    """
    This class implements all functions supported by the python SDK.
    Attributes:
            settings (Settings): configuration settings for balena python SDK.
            logs (Logs): logs from devices working on Balena.
            auth (Auth): authentication handling.
            models (Models): all models in balena python SDK.

    """

    def __init__(self, settings: Optional[SettingsConfig] = None):
        self.settings = Settings(settings)
        self.pine = PineClient(self.settings, __version__)
        self.logs = Logs(self.pine, self.settings)
        self.auth = Auth(self.pine, self.settings)
        self.models = Models(self.pine, self.settings)
