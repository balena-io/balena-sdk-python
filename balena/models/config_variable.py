import json

from ..base_request import BaseRequest
from .device import Device
from ..settings import Settings
from .. import exceptions


def _is_valid_config_var_name(config_var_name):
    return config_var_name.startswith("RESIN_") or config_var_name.startswith("BALENA_")


class ConfigVariable:
    """
    This class is a wrapper for config variable models.

    """

    def __init__(self):
        self.device_config_variable = DeviceConfigVariable()
        self.application_config_variable = ApplicationConfigVariable()


class DeviceConfigVariable:
    """
    This class implements device config variable model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.device = Device()
        self.settings = Settings()

    def get_all(self, uuid):
        """
        Get all device config variables belong to a device.

        Args:
            uuid (str): device uuid.

        Returns:
            list: device config variables.

        Examples:
            >>> balena.models.config_variable.device_config_variable.get_all('f5213eac0d63ac47721b037a7406d306')
            [
                {
                    "id": 1234567,
                    "device": {"__id": 7654321},
                    "value": "test",
                    "name": "MODE",
                },
                {
                    "id": 7890123,
                    "device": {"__id": 3210987},
                    "value": "true",
                    "name": "IS_TESTING",
                },
            ]

        """

        raw_query = "$filter=device/any(d:d/uuid%20eq%20'{uuid}')".format(uuid=uuid)

        return self.base_request.request(
            "device_config_variable",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    def get_all_by_application(self, app_id):
        """
        Get all device config variables by application.

        Args:
            app_id (int): application id.

        Returns:
            list: device config variables.

        Examples:
            >>> balena.models.config_variable.device_config_variable.get_all_by_application(1043050)
            [
                {
                    "id": 1234567,
                    "device": {"__id": 7654321},
                    "value": "test_app",
                    "name": "MODE_APPLICATION",
                },
                {
                    "id": 7890123,
                    "device": {"__id": 3210987},
                    "value": "true",
                    "name": "IS_TESTING",
                },
            ]

        """

        raw_query = f"$filter=device/any(d:d/belongs_to__application%20eq%20{app_id})"

        return self.base_request.request(
            "device_config_variable",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    def create(self, uuid, config_var_name, value):
        """
        Create a device config variable.

        Args:
            uuid (str): device uuid.
            config_var_name (str): device config variable name.
            value (str): device config variable value.

        Returns:
            dict: new device config variable info.

        Examples:
            >>> balena.models.config_variable.device_config_variable.create('f14a73b3a762396f7bfeacf5d530c316aa8cfeff307bea93422f71a106c344','BALENA_TEST_DEVICE_CONFIG_VAR','test value')
            {
                "device": {"__deferred": {"uri": "/balena/device(1083716)"}, "__id": 1083716},
                "__metadata": {"type": "", "uri": "/balena/device_config_variable(163985)"},
                "id": 163985,
                "value": "test value",
                "name": "BALENA_TEST_DEVICE_CONFIG_VAR",
            }

        """  # noqa: E501

        if not _is_valid_config_var_name(config_var_name):
            raise exceptions.InvalidParameter("config_var_name", config_var_name)

        device = self.device.get(uuid)

        data = {"device": device["id"], "name": config_var_name, "value": value}

        return json.loads(
            self.base_request.request(
                "device_config_variable",
                "POST",
                data=data,
                endpoint=self.settings.get("pine_endpoint"),
            ).decode("utf-8")
        )

    def update(self, var_id, value):
        """
        Update a device config variable.

        Args:
            var_id (str): device config variable id.
            value (str): new device config variable value.

        Examples:
            >>> balena.models.config_variable.device_config_variable.update('132715', 'new test value')
            'OK'

        """

        params = {"filter": "id", "eq": var_id}
        data = {"value": value}
        return self.base_request.request(
            "device_config_variable",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def remove(self, var_id):
        """
        Remove a device config environment variable.

        Args:
            var_id (str): device config environment variable id.

        Examples:
            >>> balena.models.config_variable.device_config_variable.remove('132715')
            'OK'

        """

        params = {"filter": "id", "eq": var_id}
        return self.base_request.request(
            "device_config_variable",
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )


class ApplicationConfigVariable:
    """
    This class implements application config variable model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def get_all(self, app_id):
        """
        Get all application config variables belong to an application.

        Args:
            app_id (str): application id.

        Returns:
            list: application config variables.

        Examples:
            >>> balena.models.config_variable.application_config_variable.get_all('1005160')
            [
                {
                    "application": {
                        "__deferred": {"uri": "/balena/application(1005160)"},
                        "__id": 1005160,
                    },
                    "__metadata": {
                        "type": "",
                        "uri": "/balena/application_config_variable(116965)",
                    },
                    "id": 116965,
                    "value": "false",
                    "name": "BALENA_SUPERVISOR_NATIVE_LOGGER",
                }
            ]

        """

        params = {"filter": "application", "eq": app_id}

        return self.base_request.request(
            "application_config_variable",
            "GET",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

    def create(self, app_id, config_var_name, value):
        """
        Create an application config variable.

        Args:
            app_id (str): application id.
            config_var_name (str): application config variable name.
            value (str): application config variable value.

        Returns:
            dict: new application config variable info.

        Examples:
            >>> balena.models.config_variable.application_config_variable.create('1005160', 'BALENA_TEST_APP_CONFIG_VAR', 'test value')
            {
                "id": 117738,
                "application": {
                    "__deferred": {"uri": "/balena/application(1005160)"},
                    "__id": 1005160,
                },
                "name": "BALENA_TEST_APP_CONFIG_VAR",
                "value": "test value",
                "__metadata": {"uri": "/balena/application_config_variable(117738)", "type": ""},
            }

        """  # noqa: E501

        if not _is_valid_config_var_name(config_var_name):
            raise exceptions.InvalidParameter("config_var_name", config_var_name)

        data = {"application": app_id, "name": config_var_name, "value": value}

        return json.loads(
            self.base_request.request(
                "application_config_variable",
                "POST",
                data=data,
                endpoint=self.settings.get("pine_endpoint"),
            ).decode("utf-8")
        )

    def update(self, var_id, value):
        """
        Update an application config variable.

        Args:
            var_id (str): application config variable id.
            value (str): new application config variable value.

        Examples:
            >>> balena.models.config_variable.application_config_variable.update('117738', 'new test value')
            'OK'

        """

        params = {"filter": "id", "eq": var_id}
        data = {"value": value}
        return self.base_request.request(
            "application_config_variable",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def remove(self, var_id):
        """
        Remove a application config environment variable.

        Args:
            var_id (str): application config environment variable id.

        Examples:
            >>> balena.models.config_variable.application_config_variable.remove('117738')
            'OK'

        """

        params = {"filter": "id", "eq": var_id}
        return self.base_request.request(
            "application_config_variable",
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )
