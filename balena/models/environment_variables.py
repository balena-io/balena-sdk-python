import re
import json

from ..base_request import BaseRequest
from .device import Device
from ..settings import Settings
from .. import exceptions
from .service import Service
from .service_install import ServiceInstall


def _is_valid_env_var_name(env_var_name):
    return re.match("^[a-zA-Z_]+[a-zA-Z0-9_]*$", env_var_name)


class EnvironmentVariable:
    """
    This class is a wrapper for environment variable models.

    """

    def __init__(self):
        self.application = ApplicationEnvVariable()
        self.service_environment_variable = ServiceEnvVariable()
        self.device = DeviceEnvVariable()
        self.device_service_environment_variable = DeviceServiceEnvVariable()


class DeviceEnvVariable:
    """
    This class implements device environment variable model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.device = Device()
        self.settings = Settings()

    def _fix_device_env_var_name_key(self, env_var):
        """
        Internal method to workaround the fact that applications environment variables contain a `name` property
        while device environment variables contain an `env_var_name` property instead.
        """

        if "env_var_name" in env_var:
            env_var["name"] = env_var["env_var_name"]
            env_var.pop("env_var_name", None)
        return env_var

    def get_all(self, uuid):
        """
        Get all device environment variables.

        Args:
            uuid (str): device uuid.

        Returns:
            list: device environment variables.

        Examples:
            >>> balena.models.environment_variables.device.get_all('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            [
                {
                    "device": {"__deferred": {"uri": "/ewa/device(122950)"}, "__id": 122950},
                    "__metadata": {"type": "", "uri": "/ewa/device_environment_variable(2173)"},
                    "id": 2173,
                    "value": "1322944771964103",
                    "env_var_name": "BALENA_DEVICE_RESTART",
                }
            ]

        """  # noqa: E501

        raw_query = "$filter=device/any(d:d/uuid%20eq%20'{uuid}')".format(uuid=uuid)
        return self.base_request.request(
            "device_environment_variable",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    def create(self, uuid, env_var_name, value):
        """
        Create a device environment variable.

        Args:
            uuid (str): device uuid.
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Returns:
            dict: new device environment variable info.

        Examples:
            >>> balena.models.environment_variables.device.create('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143','test_env4', 'testing1')
            {
                "name": "test_env4",
                "__metadata": {"type": "", "uri": "/balena/device_environment_variable(42166)"},
                "value": "testing1",
                "device": {"__deferred": {"uri": "/balena/device(115792)"}, "__id": 115792},
                "id": 42166,
            }

        """  # noqa: E501

        if not _is_valid_env_var_name(env_var_name):
            raise exceptions.InvalidParameter("env_var_name", env_var_name)
        device = self.device.get(uuid)
        data = {"device": device["id"], "name": env_var_name, "value": value}
        new_env_var = json.loads(
            self.base_request.request(
                "device_environment_variable",
                "POST",
                data=data,
                endpoint=self.settings.get("pine_endpoint"),
            ).decode("utf-8")
        )
        return self._fix_device_env_var_name_key(new_env_var)

    def update(self, var_id, value):
        """
        Update a device environment variable.

        Args:
            var_id (str): environment variable id.
            value (str): new environment variable value.

        Examples:
            >>> balena.models.environment_variables.device.update(2184, 'new value')
            'OK'

        """

        params = {"filter": "id", "eq": var_id}
        data = {"value": value}
        return self.base_request.request(
            "device_environment_variable",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def remove(self, var_id):
        """
        Remove a device environment variable.

        Args:
            var_id (str): environment variable id.

        Examples:
            >>> balena.models.environment_variables.device.remove(2184)
            'OK'

        """

        params = {"filter": "id", "eq": var_id}
        return self.base_request.request(
            "device_environment_variable",
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def get_all_by_application(self, app_id):
        """
        Get all device environment variables for an application.

        Args:
            app_id (str): application id.

        Returns:
            list: list of device environment variables.

        Examples:
            >>> balena.models.environment_variables.device.get_all_by_application('5780')
            [
                {
                    "name": "device1",
                    "__metadata": {"type": "", "uri": "/balena/device_environment_variable(40794)"},
                    "value": "test",
                    "device": {"__deferred": {"uri": "/balena/device(115792)"}, "__id": 115792},
                    "id": 40794,
                },
                {
                    "name": "BALENA_DEVICE_RESTART",
                    "__metadata": {"type": "", "uri": "/balena/device_environment_variable(1524)"},
                    "value": "961506585823372",
                    "device": {"__deferred": {"uri": "/balena/device(121794)"}, "__id": 121794},
                    "id": 1524,
                },
            ]

        """  # noqa: E501

        params = {"filter": "device/belongs_to__application", "eq": app_id}
        env_list = self.base_request.request(
            "device_environment_variable",
            "GET",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )
        return list(map(self._fix_device_env_var_name_key, env_list["d"]))


class DeviceServiceEnvVariable:
    """
    This class implements device service variable model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.device = Device()
        self.settings = Settings()
        self.service = Service()
        self.service_install = ServiceInstall()

    def get_all(self, uuid):
        """
        Get all device service environment variables belong to a device.

        Args:
            uuid (str): device uuid.

        Returns:
            list: device service environment variables.

        Examples:
            >>> balena.models.environment_variables.device_service_environment_variable.get_all('f5213eac0d63ac47721b037a7406d306')
            [
                {
                    "name": "dev_proxy",
                    "created_at": "2018-03-16T19:23:21.727Z",
                    "__metadata": {
                        "type": "",
                        "uri": "/balena/device_service_environment_variable(28888)",
                    },
                    "value": "value",
                    "service_install": [
                        {
                            "__metadata": {"type": "", "uri": "/balena/service_install(30788)"},
                            "id": 30788,
                            "service": [
                                {
                                    "service_name": "proxy",
                                    "__metadata": {"type": "", "uri": "/balena/service(NaN)"},
                                }
                            ],
                        }
                    ],
                    "id": 28888,
                },
                {
                    "name": "dev_data",
                    "created_at": "2018-03-16T19:23:11.614Z",
                    "__metadata": {
                        "type": "",
                        "uri": "/balena/device_service_environment_variable(28887)",
                    },
                    "value": "dev_data_value",
                    "service_install": [
                        {
                            "__metadata": {"type": "", "uri": "/balena/service_install(30789)"},
                            "id": 30789,
                            "service": [
                                {
                                    "service_name": "data",
                                    "__metadata": {"type": "", "uri": "/balena/service(NaN)"},
                                }
                            ],
                        }
                    ],
                    "id": 28887,
                },
                {
                    "name": "dev_data1",
                    "created_at": "2018-03-17T05:53:19.257Z",
                    "__metadata": {
                        "type": "",
                        "uri": "/balena/device_service_environment_variable(28964)",
                    },
                    "value": "aaaa",
                    "service_install": [
                        {
                            "__metadata": {"type": "", "uri": "/balena/service_install(30789)"},
                            "id": 30789,
                            "service": [
                                {
                                    "service_name": "data",
                                    "__metadata": {"type": "", "uri": "/balena/service(NaN)"},
                                }
                            ],
                        }
                    ],
                    "id": 28964,
                },
            ]

        """  # noqa: E501

        # fmt: off
        query = (
            "$expand=service_install("
                "$select=id"
                "&$expand=service($select=service_name)"
            ")"
            f"&$filter=service_install/any(si:si/device/any(d:d/uuid%20eq%20'{uuid}'))"
        )
        # fmt: on

        return self.base_request.request(
            "device_service_environment_variable",
            "GET",
            raw_query=query,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    def create(self, uuid, service_name, env_var_name, value):
        """
        Create a device service environment variable.

        Args:
            uuid (str): device uuid.
            service_name (str): service name.
            env_var_name (str): device service environment variable name.
            value (str): device service environment variable value.

        Returns:
            dict: new device service environment variable info.

        Examples:
            >>> balena.models.environment_variables.device_service_environment_variable.create('f5213eac0d63ac47721b037a7406d306', 'data', 'dev_data_sdk', 'test1')
            {
                "id": 28970,
                "created_at": "2018-03-17T10:13:14.184Z",
                "service_install": {
                    "__deferred": {"uri": "/balena/service_install(30789)"},
                    "__id": 30789,
                },
                "value": "test1",
                "name": "dev_data_sdk",
                "__metadata": {
                    "uri": "/balena/device_service_environment_variable(28970)",
                    "type": "",
                },
            }


        """  # noqa: E501

        if not _is_valid_env_var_name(env_var_name):
            raise exceptions.InvalidParameter("env_var_name", env_var_name)

        device = self.device.get(uuid)
        services = self.service.get_all_by_application(device["belongs_to__application"]["__id"])
        service_id = [i["id"] for i in services if i["service_name"] == service_name]
        if service_id:
            service_installs = self.service_install.get_all_by_device(device["id"])
            service_install_id = [i["id"] for i in service_installs if i["installs__service"]["__id"] == service_id[0]]

            data = {
                "service_install": service_install_id[0],
                "name": env_var_name,
                "value": value,
            }

            return json.loads(
                self.base_request.request(
                    "device_service_environment_variable",
                    "POST",
                    data=data,
                    endpoint=self.settings.get("pine_endpoint"),
                ).decode("utf-8")
            )
        else:
            raise exceptions.ServiceNotFound(service_name)

    def update(self, var_id, value):
        """
        Update a device service environment variable.

        Args:
            var_id (str): device environment variable id.
            value (str): new device environment variable value.

        Examples:
            >>> balena.models.environment_variables.device_service_environment_variable.update('28970', 'test1 new')
            'OK'

        """

        params = {"filter": "id", "eq": var_id}
        data = {"value": value}
        return self.base_request.request(
            "device_service_environment_variable",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def remove(self, var_id):
        """
        Remove a device service environment variable.

        Args:
            var_id (str): device service environment variable id.

        Examples:
            >>> balena.models.environment_variables.device_service_environment_variable.remove('28970')
            'OK'

        """

        params = {"filter": "id", "eq": var_id}
        return self.base_request.request(
            "device_service_environment_variable",
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def get_all_by_application(self, app_id):
        """
        Get all device service environment variables belong to an application.

        Args:
            app_id (int): application id.

        Returns:
            list: list of device service environment variables.

        Examples:
            >>> balena.models.environment_variables.device_service_environment_variable.get_all_by_application(1043050)
            [
                {
                    "id": 566017,
                    "created_at": "2021-04-23T08:28:08.539Z",
                    "service_install": {
                        "__id": 1874939,
                        "__deferred": {"uri": "/resin/service_install(@id)?@id=1874939"},
                    },
                    "value": "1",
                    "name": "testEnv1",
                    "__metadata": {
                        "uri": "/resin/device_service_environment_variable(@id)?@id=566017"
                    },
                },
                {
                    "id": 566015,
                    "created_at": "2021-04-23T08:17:45.767Z",
                    "service_install": {
                        "__id": 1874939,
                        "__deferred": {"uri": "/resin/service_install(@id)?@id=1874939"},
                    },
                    "value": "12",
                    "name": "testEnv2",
                    "__metadata": {
                        "uri": "/resin/device_service_environment_variable(@id)?@id=566015"
                    },
                },
            ]

        """

        raw_query = f"$filter=service_install/any(si:si/device/any(d:d/belongs_to__application%20eq%20{app_id}))"

        return self.base_request.request(
            "device_service_environment_variable",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]


class ApplicationEnvVariable:
    """
    This class implements application environment variable model for balena python SDK.

    Attributes:
        SYSTEM_VARIABLE_RESERVED_NAMES (list): list of reserved system variable names.
        OTHER_RESERVED_NAMES_START (list): list of prefix for system variable.

    """

    SYSTEM_VARIABLE_RESERVED_NAMES = ["BALENA", "RESIN", "USER"]
    OTHER_RESERVED_NAMES_START = ["BALENA_", "RESIN_"]

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def get_all(self, app_id):
        """
        Get all environment variables by application.

        Args:
            app_id (str): application id.

        Returns:
            list: application environment variables.

        Examples:
            >>> balena.models.environment_variables.application.get_all(9020)
            [
                {
                    "application": {"__deferred": {"uri": "/ewa/application(9020)"}, "__id": 9020},
                    "__metadata": {"type": "", "uri": "/ewa/environment_variable(5650)"},
                    "id": 5650,
                    "value": "7330634368117899",
                    "name": "BALENA_RESTART",
                }
            ]

        """

        params = {"filter": "application", "eq": app_id}
        return self.base_request.request(
            "application_environment_variable",
            "GET",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    def create(self, app_id, env_var_name, value):
        """
        Create an environment variable for application.

        Args:
            app_id (str): application id.
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Returns:
            dict: new application environment info.

        Examples:
            >>> balena.models.environment_variables.application.create('978062', 'test2', '123')
            {
                "id": 91138,
                "application": {
                    "__deferred": {"uri": "/balena/application(978062)"},
                    "__id": 978062,
                },
                "name": "test2",
                "value": "123",
                "__metadata": {"uri": "/balena/environment_variable(91138)", "type": ""},
            }

        """

        if not _is_valid_env_var_name(env_var_name):
            raise exceptions.InvalidParameter("env_var_name", env_var_name)
        data = {"name": env_var_name, "value": value, "application": app_id}
        return json.loads(
            self.base_request.request(
                "application_environment_variable",
                "POST",
                data=data,
                endpoint=self.settings.get("pine_endpoint"),
            ).decode("utf-8")
        )

    def update(self, var_id, value):
        """
        Update an environment variable value for application.

        Args:
            var_id (str): environment variable id.
            value (str): new environment variable value.

        Examples:
            >>> balena.models.environment_variables.application.update(5652, 'new value')
            'OK'

        """

        params = {"filter": "id", "eq": var_id}

        data = {"value": value}
        return self.base_request.request(
            "application_environment_variable",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def remove(self, var_id):
        """
        Remove application environment variable.

        Args:
            var_id (str): environment variable id.

        Examples:
            >>> balena.models.environment_variables.application.remove(5652)
            'OK'

        """

        params = {"filter": "id", "eq": var_id}
        return self.base_request.request(
            "application_environment_variable",
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def is_system_variable(self, variable):
        """
        Check if a variable is system specific.

        Args:
            variable (str): environment variable name.

        Returns:
            bool: True if system variable, False otherwise.

        Examples:
            >>> balena.models.environment_variables.application.is_system_variable('BALENA_API_KEY')
            True
            >>> balena.models.environment_variables.application.is_system_variable('APPLICATION_API_KEY')
            False

        """

        if variable in self.SYSTEM_VARIABLE_RESERVED_NAMES:
            return True

        return any(True for prefix in self.OTHER_RESERVED_NAMES_START if variable.startswith(prefix))


class ServiceEnvVariable:
    """
    This class implements service environment variable model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.service = Service()

    def get_all_by_application(self, app_id):
        """
        Get all service environment variables by application.

        Args:
            app_id (str): application id.

        Returns:
            list: service application environment variables.

        Examples:
            >>> balena.models.environment_variables.service_environment_variable.get_all_by_application('1005160')
            [
                {
                    "name": "app_data",
                    "service": {"__deferred": {"uri": "/balena/service(21667)"}, "__id": 21667},
                    "created_at": "2018-03-16T19:21:21.087Z",
                    "__metadata": {
                        "type": "",
                        "uri": "/balena/service_environment_variable(12365)",
                    },
                    "value": "app_data_value",
                    "id": 12365,
                },
                {
                    "name": "app_data1",
                    "service": {"__deferred": {"uri": "/balena/service(21667)"}, "__id": 21667},
                    "created_at": "2018-03-16T19:21:49.662Z",
                    "__metadata": {
                        "type": "",
                        "uri": "/balena/service_environment_variable(12366)",
                    },
                    "value": "app_data_value",
                    "id": 12366,
                },
                {
                    "name": "app_front",
                    "service": {"__deferred": {"uri": "/balena/service(21669)"}, "__id": 21669},
                    "created_at": "2018-03-16T19:22:06.955Z",
                    "__metadata": {
                        "type": "",
                        "uri": "/balena/service_environment_variable(12367)",
                    },
                    "value": "front_value",
                    "id": 12367,
                },
            ]

        """

        # TODO: pine client for python
        raw_query = "$filter=service/any(s:s/application%20eq%20{app_id})".format(app_id=app_id)

        return self.base_request.request(
            "service_environment_variable",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    def create(self, app_id, service_name, env_var_name, value):
        """
        Create a service environment variable for application.

        Args:
            app_id (str): application id.
            service_name(str): service name.
            env_var_name (str): environment variable name.
            value (str): environment variable value.

        Returns:
            str: new service environment variable info.

        Examples:
            >>> balena.models.environment_variables.service_environment_variable.create('1005160', 'proxy', 'app_proxy', 'test value')
            {
                "id": 12444,
                "created_at": "2018-03-18T09:34:09.144Z",
                "service": {"__deferred": {"uri": "/balena/service(21668)"}, "__id": 21668},
                "name": "app_proxy",
                "value": "test value",
                "__metadata": {"uri": "/balena/service_environment_variable(12444)", "type": ""},
            }

        """  # noqa: E501

        if not _is_valid_env_var_name(env_var_name):
            raise exceptions.InvalidParameter("env_var_name", env_var_name)

        services = self.service.get_all_by_application(app_id)
        service_id = [i["id"] for i in services if i["service_name"] == service_name]

        if service_id:
            data = {"name": env_var_name, "value": value, "service": service_id[0]}

            return json.loads(
                self.base_request.request(
                    "service_environment_variable",
                    "POST",
                    data=data,
                    endpoint=self.settings.get("pine_endpoint"),
                ).decode("utf-8")
            )
        else:
            raise exceptions.ServiceNotFound(service_name)

    def update(self, var_id, value):
        """
        Update a service environment variable value for application.

        Args:
            var_id (str): service environment variable id.
            value (str): new service environment variable value.

        Examples:
            >>> balena.models.environment_variables.service_environment_variable.update('12444', 'new test value')
            'OK'

        """

        params = {"filter": "id", "eq": var_id}

        data = {"value": value}
        return self.base_request.request(
            "service_environment_variable",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def remove(self, var_id):
        """
        Remove service environment variable.

        Args:
            var_id (str): service environment variable id.

        Examples:
            >>> balena.models.environment_variables.service_environment_variable.remove('12444')
            'OK'

        """

        params = {"filter": "id", "eq": var_id}
        return self.base_request.request(
            "service_environment_variable",
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )
