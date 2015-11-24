Resin SDK
---------

The official [Resin.io](https://resin.io/) SDK for Python.

Role
----

The intention of this module is to provide developers a nice API to integrate their Python applications with Resin.io.

Installation
------------

Install the Resin SDK:

From Source:
```
https://github.com/resin-io/resin-sdk-python
```

From git:
```
pip install git+https://github.com/resin-io/resin-sdk-python.git
```

Platforms
---------

We also support [NodeJS SDK](https://github.com/resin-io/resin-sdk).

Basic Usage
-----------

```python
>>> from resin import Resin
>>> resin = Resin()
>>> credentials = {'username':<your email>, 'password':<your password>}
>>> resin.auth.login(**credentials)
...
```

Documentation
-------------

We generate markdown documentation in [DOCUMENTATION.md](https://github.com/resin-io/resin-sdk-python/blob/master/DOCUMENTATION.md).

To generate the documentation:
```bash
python docs_generators.py > DOCUMENTATION.md
```

Support
-------

If you're having any problem, please [raise an issue](https://github.com/resin-io/resin-sdk-python/issues/new) on GitHub and the Resin.io team will be happy to help.

Contribute
----------

- Issue Tracker: [github.com/resin-io/resin-sdk-python/issues](https://github.com/resin-io/resin-sdk-python/issues)
- Source Code: [github.com/resin-io/resin-sdk-python](https://github.com/resin-io/resin-sdk-python)

License
-------

The project is licensed under the MIT license.
