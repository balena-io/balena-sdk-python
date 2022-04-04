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

from .auth import Auth
from .logs import Logs
from .settings import Settings
from .models import Models
from .twofactor_auth import TwoFactorAuth


__version__ = '11.3.2'


class Balena:
    """
    This class implements all functions supported by the python SDK.
    Attributes:
            settings (Settings): configuration settings for balena python SDK.
            logs (Logs): logs from devices working on Balena.
            auth (Auth): authentication handling.
            models (Models): all models in balena python SDK.

    """

    def __init__(self):
        self.settings = Settings()
        self.logs = Logs()
        self.auth = Auth()
        self.models = Models()
        self.twofactor_auth = TwoFactorAuth()
