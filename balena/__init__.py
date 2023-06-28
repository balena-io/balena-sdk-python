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

If you feel something is missing, not clear or could be improved, [please don't
hesitate to open an issue in GitHub](https://github.com/balena-io/balena-sdk-python/issues), we'll be happy to help.
"""

from typing import Optional
from .auth import Auth
from .logs import Logs
from .models import Models
from .pine import PineClient
from .settings import SettingsConfig, Settings

__version__ = "12.7.0"


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
