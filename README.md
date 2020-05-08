Balena SDK
---------

The official [balena](https://balena.io/) SDK for python.

Role
----

The intention of this module is to provide developers a nice API to integrate their python applications with balena.

Installation
------------

Install the balena SDK:

From Source:
```
https://github.com/balena-io/balena-sdk-python
```

From git:
```
pip install git+https://github.com/balena-io/balena-sdk-python.git
```

Example of installing on a Debian container:
```
FROM balenalib/amd64-debian:stretch

# Install python 3 and balena SDK dependencies.
RUN install_packages build-essential python3 python3-pip python3-setuptools \
    python3-dev libffi-dev libssl-dev

# Install balena python SDK in python 3.
RUN pip3 install balena-sdk
```

Example of installing on a Alpine Linux container:
```
FROM balenalib/amd64-alpine:3.9

# Install python 3 and balena SDK dependencies.
RUN install_packages build-base python3 py3-setuptools python3-dev libffi-dev openssl-dev

# Install balena python SDK in python 3.
RUN pip3 install balena-sdk
```

Platforms
---------

We also support [NodeJS SDK](https://github.com/balena-io/balena-sdk).

Basic Usage
-----------

```python
>>> from balena import Balena
>>> balena = Balena()
>>> credentials = {'username':<your email>, 'password':<your password>}
>>> balena.auth.login(**credentials)
...
```

Documentation
-------------

We generate markdown documentation in [DOCUMENTATION.md](https://github.com/balena-io/balena-sdk-python/blob/master/DOCUMENTATION.md).

To generate the documentation:
```bash
python docs_generator.py > DOCUMENTATION.md
```

Deprecation policy
------------------

The balena SDK for Python uses [semver versioning](https://semver.org/), with the concepts of major, minor and patch version releases.

The latest release of the previous major version of the balena SDK will remain compatible with the balenaCloud backend services for one year from the date when the next major version is released.
For example, balena SDK v8.1.1, as the latest v8 release, would remain compatible with the balenaCloud backend for one year from the date when v9.0.0 is released.

At the end of this period, the older major version is considered deprecated and some of the functionality that depends on balenaCloud services may stop working at any time.
Users are encouraged to regularly update the balena SDK to the latest version.

Tests
-----

To run the tests, first create a `.env` file with your test user configuration, e.g.:

```
[Credentials]
email=my_test_user@balena.io
user_id=my_test_user
password=123456my_password
```

You can optionally change the target API endpoint too, e.g. `api_endpoint=https://api.balena-cloud.com`.

Then run `python -m unittest discover tests -v`.

Support
-------

If you're having any problem, please [raise an issue](https://github.com/balena-io/balena-sdk-python/issues/new) on GitHub and the balena team will be happy to help.

Contribute
----------

- Issue Tracker: [github.com/balena-io/balena-sdk-python/issues](https://github.com/balena-io/balena-sdk-python/issues)
- Source Code: [github.com/balena-io/balena-sdk-python](https://github.com/balena-io/balena-sdk-python)

License
-------

The project is licensed under the MIT license.
