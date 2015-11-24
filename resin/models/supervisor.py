import os

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions


class Supervisor(object):
    """
    This class implements supervisor model for Resin Python SDK.

    Attributes:
        SUPERVISOR_API_VERSION (str): supervisor API version.
        RESIN_SUPERVISOR_ADDRESS (str): supervisor endpoint address on device.
        RESIN_SUPERVISOR_API_KEY (str): supervisor API key on device.
        _on_device (bool): API endpoint flag.
            If True then all commands will be sent to the API on device.
            If False then all command will be sent to the Resin API proxy endpoint (api.resin.io/supervisor/<url>).
            If RESIN_SUPERVISOR_ADDRESS and RESIN_SUPERVISOR_API_KEY are available, _on_device will be set to True by default. Otherwise, it's False.

    """

    SUPERVISOR_API_VERSION = 'v1'
    RESIN_SUPERVISOR_ADDRESS = os.environ.get('RESIN_SUPERVISOR_ADDRESS')
    RESIN_SUPERVISOR_API_KEY = os.environ.get('RESIN_SUPERVISOR_API_KEY')

    # _on_device = True, if RESIN_SUPERVISOR_ADDRESS and RESIN_SUPERVISOR_API_KEY env vars are avaiable => can communicate with both supervisor API endpoints on device or Resin API endpoints.
    # _on_device = False, if RESIN_SUPERVISOR_ADDRESS and RESIN_SUPERVISOR_API_KEY env vars are not avaiable => can only communicate with Resin API endpoints.
    _on_device = all([RESIN_SUPERVISOR_ADDRESS, RESIN_SUPERVISOR_API_KEY])

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def _check_args(self, device_id, app_id):
        if device_id is None:
            exceptions.MissingOption('device_id')

        if app_id is None:
            exceptions.MissingOption('app_id')

    def _do_command(self, endpoint, req_data={}, device_id=None, app_id=None, method=None):
        if not self._on_device:
            self._check_args(device_id, app_id)

            if req_data:
                data = {
                    'deviceId': device_id,
                    'appId': app_id,
                    'data': req_data
                }
            else:
                data = {
                    'deviceId': device_id,
                    'appId': app_id
                }

            return self.base_request.request(
                'supervisor/{0}'.format(endpoint),
                'POST',
                data=data,
                endpoint=self.settings.get('api_endpoint'),
                login=True
            )
        else:
            return self.base_request.request(
                endpoint,
                method,
                data=req_data,
                endpoint=self.RESIN_SUPERVISOR_ADDRESS,
                api_key=self.RESIN_SUPERVISOR_API_KEY
            )

    def force_api_endpoint(self, endpoint):
        """
        Force all API commands to a specific endpoint.

        Args:
            endpoint (bool): True if selecting the API on device. False if selecting the Resin API proxy endpoint.

        Raises:
            InvalidOption: if endpoint value is not bool.

        """

        self._on_device = bool(endpoint)

    def ping(self, device_id=None, app_id=None):
        """
        Check that the supervisor is alive and well.
        No need to set device_id and app_id if command is sent to the API on device.

        Args:
            device_id (Optional[str]): device id.
            app_id (Optional[str]): application id.

        Returns:
            str: `OK` signals that the supervisor is alive and well.

        Raises:
            InvalidOption: if the endpoint is Resin API proxy endpoint and device_id or app_id is not set.

        Examples:
            >>> resin.models.supervisor.ping(device_id='122950', app_id='9020')
            'OK'

        """

        if not self._on_device:
            self._check_args(device_id, app_id)

            data = {
                'deviceId': device_id,
                'appId': app_id,
                'method': 'GET'
            }

            return self.base_request.request(
                'supervisor/ping',
                'POST',
                data=data,
                endpoint=self.settings.get('api_endpoint'),
                login=True
            )
        else:
            return self.base_request.request(
                'ping',
                'GET',
                endpoint=self.RESIN_SUPERVISOR_ADDRESS,
                api_key=self.RESIN_SUPERVISOR_API_KEY
            )

    def blink(self, device_id=None, app_id=None):
        """
        Start a blink pattern on a LED for 15 seconds. This is the same with `resin.models.device.identify()`.
        No need to set device_id and app_id if command is sent to the API on device.

        Args:
            device_id (Optional[str]): device id.
            app_id (Optional[str]): application id.

        Raises:
            InvalidOption: if the endpoint is Resin API proxy endpoint and device_id or app_id is not specified.

        Examples:
            >>> resin.models.supervisor.blink(device_id='122950', app_id='9020')
            'OK'

        """

        return self._do_command(
            '{0}/blink'.format(self.SUPERVISOR_API_VERSION),
            device_id=device_id,
            app_id=app_id,
            method='POST'
        )

    def update(self, device_id=None, app_id=None, force=False):
        """
        Triggers an update check on the supervisor. Optionally, forces an update when updates are locked.
        No need to set device_id and app_id if command is sent to the API on device.

        Args:
            device_id (Optional[str]): device id.
            app_id (Optional[str]): application id.
            force (Optional[bool]): If force is True, the update lock will be overridden.

        Raises:
            InvalidOption: if the endpoint is Resin API proxy endpoint and device_id or app_id is not specified.

        Examples:
            >>> resin.models.supervisor.update(device_id='122950', app_id='9020')
            (Empty Response)

            # Force an update
            >>> resin.models.supervisor.update(device_id='122950', app_id='9020', force=True)
            (Empty Response)

        """

        if force:
            data = {
                'force': force
            }
        else:
            data = {}

        return self._do_command(
            '{0}/update'.format(self.SUPERVISOR_API_VERSION),
            req_data=data,
            device_id=device_id,
            app_id=app_id,
            method='POST'
        )

    def reboot(self, device_id=None, app_id=None):
        """
        Reboot the device.
        No need to set device_id and app_id if command is sent to the API on device.

        Args:
            device_id (Optional[str]): device id.
            app_id (Optional[str]): application id.

        Returns:
            dict: when successful, this dictionary is returned `{ 'Data': 'OK', 'Error': '' }`.

        Raises:
            InvalidOption: if the endpoint is Resin API proxy endpoint and device_id or app_id is not specified.

        Examples:
            >>> resin.models.supervisor.reboot(device_id='122950', app_id='9020')
            {u'Data': u'OK', u'Error': u''}

        """

        return self._do_command(
            '{0}/reboot'.format(self.SUPERVISOR_API_VERSION),
            device_id=device_id,
            app_id=app_id,
            method='POST'
        )

    def shutdown(self, device_id=None, app_id=None):
        """
        Shut down the device.
        No need to set device_id and app_id if command is sent to the API on device.

        Args:
            device_id (Optional[str]): device id.
            app_id (Optional[str]): application id.

        Returns:
            dict: when successful, this dictionary is returned `{ 'Data': 'OK', 'Error': '' }`.

        Raises:
            InvalidOption: if the endpoint is Resin API proxy endpoint and device_id or app_id is not specified.

        Examples:
            >>> resin.models.supervisor.shutdown(device_id='121867', app_id='8362')
            {u'Data': u'OK', u'Error': u''}

        """

        return self._do_command(
            '{0}/shutdown'.format(self.SUPERVISOR_API_VERSION),
            device_id=device_id,
            app_id=app_id,
            method='POST'
        )

    def purge(self, app_id, device_id=None):
        """
        Clears the user application's /data folder.
        No need to set device_id and app_id if command is sent to the API on device.

        Args:
            app_id (str): application id.
            device_id (Optional[str]): device id.

        Returns:
            dict: when successful, this dictionary is returned `{ 'Data': 'OK', 'Error': '' }`.

        Raises:
            InvalidOption: if the endpoint is Resin API proxy endpoint and device_id or app_id is not specified.

        Examples:
            >>> resin.models.supervisor.purge(device_id='122950', app_id='9020')
            {u'Data': u'OK', u'Error': u''}

        """

        data = {
            'appId': app_id
        }

        return self._do_command(
            '{0}/purge'.format(self.SUPERVISOR_API_VERSION),
            req_data=data,
            device_id=device_id,
            app_id=app_id,
            method='POST'
        )

    def restart(self, app_id, device_id=None):
        """
        Restart user application container.
        No need to set device_id and app_id if command is sent to the API on device.

        Args:
            app_id (str): application id.
            device_id (Optional[str]): device id.

        Returns:
            str: `OK` signals that the supervisor is alive and well.

        Raises:
            InvalidOption: if the endpoint is Resin API proxy endpoint and device_id or app_id is not specified.

        Examples:
            >>> resin.models.supervisor.restart(device_id='122950', app_id='9020')
            'OK'

        """

        data = {
            'appId': app_id
        }

        return self._do_command(
            '{0}/restart'.format(self.SUPERVISOR_API_VERSION),
            req_data=data,
            device_id=device_id,
            app_id=app_id,
            method='POST'
        )
