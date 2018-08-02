import json

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions

NETWORK_WIFI = 'wifi'
NETWORK_ETHERNET = 'ethernet'

NETWORK_TYPES = [
    NETWORK_WIFI,
    NETWORK_ETHERNET
]


# TODO: https://github.com/resin-io/resin-sdk/pull/288
class DeviceOs(object):
    """
    This class implements device os model for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def get_config(self, app_id, options):
        """
        Get an application config.json.

        Args:
            app_id (str): application id.
            options (dict): OS configuration options to use. The available options are listed below:
                version (str): the OS version of the image.
                network (Optional[str]): the network type that the device will use, one of 'ethernet' or 'wifi' and defaults to 'ethernet' if not specified.
                appUpdatePollInterval (Optional[str]): how often the OS checks for updates, in minutes.
                wifiKey (Optional[str]): the key for the wifi network the device will connect to.
                wifiSsid (Optional[str]): the ssid for the wifi network the device will connect to.
                ip (Optional[str]): static ip address.
                gateway (Optional[str]): static ip gateway.
                netmask (Optional[str]): static ip netmask.

        Returns:
            dict: application config.json

        """

        if 'version' not in options:
            raise exceptions.MissingOption('An OS version is required when calling device_os.get_config()')

        if 'network' not in options:
            options['network'] = 'ethernet'

        options['appId'] = app_id

        return self.base_request.request(
            'download-config', 'POST', data=options,
            endpoint=self.settings.get('api_endpoint')
        )

    def download(self, raw=None, **data):
        """
        Download an OS image. This function only works if you log in using credentials or Auth Token.

        Args:
            raw (bool): determining function return value.
            **data: os parameters keyword arguments.
                Details about os parameters can be found in parse_params function

        Returns:
            object:
                If raw is True, urllib3.HTTPResponse object is returned.
                If raw is False, original response object is returned.

        Notes:
            default OS image file name can be found in response headers.

        Examples:
            >>> data = {'appId':'9020', 'network':'ethernet'}
            >>> response = resin.models.device_os.download(**data)
            >>> type(response)
            <class 'requests.models.Response'>
            >>> response['headers']
            >>> response.headers
            {'access-control-allow-methods': 'GET, PUT, POST, PATCH, DELETE, OPTIONS, HEAD', 'content-disposition': 'attachment; filename="resin-RPI1-0.1.0-1.1.0-7588720e0262.img"', 'content-encoding': 'gzip', 'transfer-encoding': 'chunked', 'x-powered-by': 'Express', 'connection': 'keep-alive', 'access-control-allow-credentials': 'true', 'date': 'Mon, 23 Nov 2015 15:13:39 GMT', 'access-control-allow-origin': '*', 'access-control-allow-headers': 'Content-Type, Authorization, Application-Record-Count, MaxDataServiceVersion, X-Requested-With', 'content-type': 'application/octet-stream', 'x-frame-options': 'DENY'}

        """

        self.params = self.parse_params(**data)
        response = self.base_request.request(
            'download', 'POST', data=data,
            endpoint=self.settings.get('api_endpoint'), stream=True, login=True
        )
        if raw:
            # return urllib3.HTTPResponse object
            return response.raw
        else:
            return response

    def parse_params(self, **params):
        """
        Validate parameters for downloading device OS image.

        Args:
            **parameters: os parameters keyword arguments.

        Returns:
            dict: validated parameters.

        Raises:
            MissingOption: if mandatory option are missing.
            InvalidOption: if appId or network are invalid (appId is not a number or parseable string. network is not in NETWORK_TYPES)

        """

        if 'appId' not in params:
            raise exceptions.MissingOption('appId')

        try:
            params['appId'] = int(params['appId'])
        except ValueError:
            raise exceptions.InvalidOption('appId')

        if 'network' not in params:
            raise exceptions.MissingOption('network')

        if params['network'] not in NETWORK_TYPES:
            raise exceptions.InvalidOption('network')

        if params['network'] == NETWORK_WIFI:
            if 'wifiSsid' not in params:
                raise exceptions.MissingOption('wifiSsid')

            # if 'wifiKey' not in params:
            #    raise exceptions.MissingOption('wifiKey')
        return params
