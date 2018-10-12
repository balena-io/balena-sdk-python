"""
Welcome to the Resin Python SDK documentation.
This document aims to describe all the functions supported by the SDK, as well as
showing examples of their expected usage.

Install the Resin SDK:

From Pip:
```
pip install resin-sdk
```

From Source (In case, you want to test a development branch):
```
https://github.com/resin-io/resin-sdk-python
```

Getting started:

```python
>>> from resin import Resin
>>> resin = Resin()
>>> credentials = {'username':<your email>, 'password':<your password>}
>>> resin.auth.login(**credentials)
...
```

If you feel something is missing, not clear or could be improved, [please don't
hesitate to open an issue in GitHub](https://github.com/resin-io/resin-sdk-python/issues), we'll be happy to help.
"""

from .auth import Auth
from .logs import Logs
from .settings import Settings
from .models import Models
from .twofactor_auth import TwoFactorAuth

from .util.deprecation_warning import print_rename_warning

__version__ = '5.1.2'


class Resin(object):
    """
    This class implements all functions supported by the Python SDK.
    Attributes:
            settings (Settings): configuration settings for Resin Python SDK.
            logs (Logs): logs from devices working on Resin.
            auth (Auth): authentication handling.
            models (Models): all models in Resin Python SDK.

    """

    def __init__(self):
        print_rename_warning()

        self.settings = Settings()
        self.logs = Logs()
        self.auth = Auth()
        self.models = Models()
        self.twofactor_auth = TwoFactorAuth()
