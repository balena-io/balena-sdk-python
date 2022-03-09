import os
from pkg_resources import parse_version

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions
from .device import Device


def _print_deprecation_warning():
    print("This is not supported on multicontainer devices, and will be removed in future")


class Supervisor:
    """
    This class implements supervisor model for balena python SDK.

    Attributes:
        SUPERVISOR_API_VERSION (str): supervisor API version.
        SUPERVISOR_ADDRESS (str): supervisor endpoint address on device.
        SUPERVISOR_API_KEY (str): supervisor API key on device.
        _on_device (bool): API endpoint flag.
            If True then all commands will be sent to the API on device.
            If False then all command will be sent to the balena API proxy endpoint (api.balena-cloud.com/supervisor/<url>).
            If SUPERVISOR_ADDRESS and SUPERVISOR_API_KEY are available, _on_device will be set to True by default. Otherwise, it's False.

    """

    SUPERVISOR_API_VERSION = 'v1'
    MIN_SUPERVISOR_MC_API = '7.0.0'

    SUPERVISOR_ADDRESS = os.environ.get('BALENA_SUPERVISOR_ADDRESS') or os.environ.get('RESIN_SUPERVISOR_ADDRESS')
    SUPERVISOR_API_KEY = os.environ.get('BALENA_SUPERVISOR_API_KEY') or os.environ.get('RESIN_SUPERVISOR_API_KEY')

    # _on_device = True, if SUPERVISOR_ADDRESS and SUPERVISOR_API_KEY env vars are avaiable => can communicate with both supervisor API endpoints on device or balena API endpoints.
    # _on_device = False, if UPERVISOR_ADDRESS and SUPERVISOR_API_KEY env vars are not avaiable => can only communicate with balena API endpoints.
    _on_device = all([SUPERVISOR_ADDRESS, SUPERVISOR_API_KEY])

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.device = Device()
        self._last_device = None

    def _check_args(self, device_uuid, app_id):
        if device_uuid is None:
            raise exceptions.MissingOption('device_uuid')

        if app_id is None:
            raise exceptions.MissingOption('app_id')

    def _do_command(self, endpoint, req_data={}, device_uuid=None, app_id=None,
                    method=None, required_version=None, on_device_method=None):
        if not self._on_device:
            self._check_args(device_uuid, app_id)

            if (self._last_device and self._last_device['uuid'] != device_uuid) or not self._last_device:
                self._last_device = self.device.get(device_uuid)

            if required_version:
                if not self._last_device['supervisor_version'] or (parse_version(required_version) > parse_version(self._last_device['supervisor_version'])):
                    raise exceptions.UnsupportedFunction(required_version, self._last_device['supervisor_version'])

            device_id = self._last_device['id']

            data = {
                'deviceId': device_id,
                'appId': app_id
            }

            if req_data:
                data['data'] = req_data

            if on_device_method:
                data['method'] = on_device_method

            return self.base_request.request(
                'supervisor/{0}'.format(endpoint),
                'POST',
                data=data,
                endpoint=self.settings.get('api_endpoint'),
                login=True
            )
        else:
            if required_version:
                current_version = os.environ.get('BALENA_SUPERVISOR_VERSION') or os.environ.get('RESIN_SUPERVISOR_VERSION')
                if not current_version or (parse_version(required_version) > parse_version(current_version)):
                    raise exceptions.UnsupportedFunction(required_version, current_version)

            return self.base_request.request(
                endpoint,
                method,
                data=req_data,
                endpoint=self.SUPERVISOR_ADDRESS,
                api_key=self.SUPERVISOR_API_KEY
            )

    def force_api_endpoint(self, endpoint):
        """
        Force all API commands to a specific endpoint.

        Args:
            endpoint (bool): True if selecting the API on device. False if selecting the balena API proxy endpoint.

        Raises:
            InvalidOption: if endpoint value is not bool.

        """

        self._on_device = bool(endpoint)

    def ping(self, device_uuid=None, app_id=None):
        """
        Check that the supervisor is alive and well.
        No need to set device uuid and app_id if command is sent to the API on device.

        Args:
            device_uuid (Optional[str]): device uuid.
            app_id (Optional[str]): application id.

        Returns:
            str: `OK` signals that the supervisor is alive and well.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not set.

        Examples:
            >>> balena.models.supervisor.ping(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020')
            'OK'

        """

        if not self._on_device:
            self._check_args(device_uuid, app_id)

            if (self._last_device and self._last_device['uuid'] != device_uuid) or not self._last_device:
                self._last_device = self.device.get(device_uuid)

            device_id = self._last_device['id']

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
                endpoint=self.SUPERVISOR_ADDRESS,
                api_key=self.SUPERVISOR_API_KEY
            )

    def blink(self, device_uuid=None, app_id=None):
        """
        Start a blink pattern on a LED for 15 seconds. This is the same with `balena.models.device.identify()`.
        No need to set device_uuid and app_id if command is sent to the API on device.

        Args:
            device_uuid (Optional[str]): device uuid.
            app_id (Optional[str]): application id.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not specified.

        Examples:
            >>> balena.models.supervisor.blink(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020')
            'OK'

        """

        return self._do_command(
            '{0}/blink'.format(self.SUPERVISOR_API_VERSION),
            device_uuid=device_uuid,
            app_id=app_id,
            method='POST'
        )

    def update(self, device_uuid=None, app_id=None, force=False):
        """
        Triggers an update check on the supervisor. Optionally, forces an update when updates are locked.
        No need to set device_uuid and app_id if command is sent to the API on device.

        Args:
            device_uuid (Optional[str]): device uuid.
            app_id (Optional[str]): application id.
            force (Optional[bool]): If force is True, the update lock will be overridden.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not specified.

        Examples:
            >>> balena.models.supervisor.update(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020')
            (Empty Response)

            # Force an update
            >>> balena.models.supervisor.update(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020', force=True)
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
            device_uuid=device_uuid,
            app_id=app_id,
            method='POST'
        )

    def reboot(self, device_uuid=None, app_id=None, force=False):
        """
        Reboot the device.
        No need to set device_uuid and app_id if command is sent to the API on device.

        Args:
            device_uuid (Optional[str]): device uuid.
            app_id (Optional[str]): application id.
            force (Optional[bool]): If force is True, the update lock will be overridden.

        Returns:
            dict: when successful, this dictionary is returned `{ 'Data': 'OK', 'Error': '' }`.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not specified.

        Examples:
            >>> balena.models.supervisor.reboot(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020')
            {u'Data': u'OK', u'Error': u''}

        """

        if force:
            data = {
                'force': force
            }
        else:
            data = {}

        return self._do_command(
            '{0}/reboot'.format(self.SUPERVISOR_API_VERSION),
            req_data=data,
            device_uuid=device_uuid,
            app_id=app_id,
            method='POST'
        )

    def shutdown(self, device_uuid=None, app_id=None, force=False):
        """
        Shut down the device.
        No need to set device_uuid and app_id if command is sent to the API on device.

        Args:
            device_uuid (Optional[str]): device uuid.
            app_id (Optional[str]): application id.
            force (Optional[bool]): If force is True, the update lock will be overridden.

        Returns:
            dict: when successful, this dictionary is returned `{ 'Data': 'OK', 'Error': '' }`.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not specified.

        Examples:
            >>> balena.models.supervisor.shutdown(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='8362')
            {u'Data': u'OK', u'Error': u''}

        """

        if force:
            data = {
                'force': force
            }
        else:
            data = {}

        return self._do_command(
            '{0}/shutdown'.format(self.SUPERVISOR_API_VERSION),
            req_data=data,
            device_uuid=device_uuid,
            app_id=app_id,
            method='POST'
        )

    def purge(self, app_id, device_uuid=None):
        """
        Clears the user application's /data folder.
        No need to set device_uuid and app_id if command is sent to the API on device.

        Args:
            app_id (str): application id.
            device_uuid (Optional[str]): device uuid.

        Returns:
            dict: when successful, this dictionary is returned `{ 'Data': 'OK', 'Error': '' }`.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not specified.

        Examples:
            >>> balena.models.supervisor.purge(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020')
            {u'Data': u'OK', u'Error': u''}

        """

        data = {
            'appId': app_id
        }

        return self._do_command(
            '{0}/purge'.format(self.SUPERVISOR_API_VERSION),
            req_data=data,
            device_uuid=device_uuid,
            app_id=app_id,
            method='POST'
        )

    def restart(self, app_id, device_uuid=None):
        """
        Restart user application container.
        No need to set device_uuid and app_id if command is sent to the API on device.

        Args:
            app_id (str): application id.
            device_uuid (Optional[str]): device uuid.

        Returns:
            str: `OK` signals that the supervisor is alive and well.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not specified.

        Examples:
            >>> balena.models.supervisor.restart(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020')
            'OK'

        """

        data = {
            'appId': app_id
        }

        return self._do_command(
            '{0}/restart'.format(self.SUPERVISOR_API_VERSION),
            req_data=data,
            device_uuid=device_uuid,
            app_id=app_id,
            method='POST'
        )

    def regenerate_supervisor_api_key(self, app_id=None, device_uuid=None):
        """
        Invalidate the current SUPERVISOR_API_KEY and generates a new one.
        The application will be restarted on the next update cycle to update the API key environment variable.
        No need to set device_uuid and app_id if command is sent to the API on device.

        Args:
            app_id (Optional[str]): application id.
            device_uuid (Optional[str]): device uuid.

        Returns:
            str: new supervisor API key.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not specified.

        Examples:
            >>> balena.models.supervisor.regenerate_supervisor_api_key(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020')
            '480af7bb8a9cf56de8a1e295f0d50e6b3bb46676aaddbf4103aa43cb57039364'

        """

        return self._do_command(
            '{0}/regenerate-api-key'.format(self.SUPERVISOR_API_VERSION),
            device_uuid=device_uuid,
            app_id=app_id,
            method='POST'
        )

    def get_device_state(self, app_id=None, device_uuid=None):
        """
        Return the current device state, as reported to the balena API and with some extra fields added to allow control over pending/locked updates.
        This function requires supervisor v1.6 or higher.
        No need to set device_uuid and app_id if command is sent to the API on device.

        Args:
            app_id (Optional[str]): application id.
            device_uuid (Optional[str]): device uuid.

        Returns:
            dict: dictionary contains device state.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not specified.

        Examples:
            >>> balena.models.supervisor.get_device_state(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020')
            {u'status': u'Idle', u'update_failed': False, u'update_pending': False, u'download_progress': None, u'os_version': u'Balena OS 1.1.1', u'api_port': 48484, u'commit': u'ff812b9a5f82d9661fb23c24aa86dce9425f1112', u'update_downloaded': False, u'supervisor_version': u'1.7.0', u'ip_address': u'192.168.0.102'}

        """

        required_version = '1.6'

        on_device_method = 'GET'

        if not self._on_device:
            return self._do_command(
                '{0}/device'.format(self.SUPERVISOR_API_VERSION),
                on_device_method=on_device_method,
                device_uuid=device_uuid,
                app_id=app_id,
                required_version=required_version,
                method='POST'
            )
        else:
            return self._do_command(
                '{0}/device'.format(self.SUPERVISOR_API_VERSION),
                required_version,
                method=on_device_method
            )

    def stop_application(self, app_id, device_uuid=None):
        """
        ***Deprecated***
        Temporarily stops a user application container. Application container will not be removed after invoking this function and a reboot or supervisor restart will cause the container to start again.
        This function requires supervisor v1.8 or higher.
        No need to set device_uuid if command is sent to the API on device.

        Args:
            app_id (str): application id.
            device_uuid (Optional[str]): device uuid.

        Returns:
            dict: dictionary contains stopped application container id.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not specified.

        Examples:
            >>> balena.models.supervisor.stop_application(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020')

        """

        _print_deprecation_warning()
        required_version = '1.8'

        return self._do_command(
            '{0}/apps/{1}/stop'.format(self.SUPERVISOR_API_VERSION, app_id),
            device_uuid=device_uuid,
            app_id=app_id,
            required_version=required_version,
            method='POST'
        )

    def start_application(self, app_id, device_uuid=None):
        """
        ***Deprecated***
        Starts a user application container, usually after it has been stopped with `stop_application()`.
        This function requires supervisor v1.8 or higher.
        No need to set device_uuid if command is sent to the API on device.

        Args:
            app_id (str): application id.
            device_uuid (Optional[str]): device uuid.

        Returns:
            dict: dictionary contains started application container id.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not specified.

        Examples:
            >>> balena.models.supervisor.start_application(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020')

        """

        _print_deprecation_warning()
        required_version = '1.8'

        return self._do_command(
            '{0}/apps/{1}/start'.format(self.SUPERVISOR_API_VERSION, app_id),
            device_uuid=device_uuid,
            app_id=app_id,
            required_version=required_version,
            method='POST'
        )

    def get_application_info(self, app_id, device_uuid=None):
        """
        ***Deprecated***
        Return information about the application running on the device.
        This function requires supervisor v1.8 or higher.
        No need to set device_uuid if command is sent to the API on device.

        Args:
            app_id (str): application id.
            device_uuid (Optional[str]): device uuid.

        Returns:
            dict: dictionary contains application information.

        Raises:
            InvalidOption: if the endpoint is balena API proxy endpoint and device_uuid or app_id is not specified.

        Examples:
            >>> balena.models.supervisor.get_application_info(device_uuid='8f66ec7335267e7cc7999ca9eec029a01ea7d823214c742ace5cfffaa21be3', app_id='9020')

        """

        _print_deprecation_warning()
        required_version = '1.8'

        on_device_method = 'GET'

        if not self._on_device:
            return self._do_command(
                '{0}/apps/{1}'.format(self.SUPERVISOR_API_VERSION, app_id),
                on_device_method=on_device_method,
                device_uuid=device_uuid,
                app_id=app_id,
                required_version=required_version,
                method='POST'
            )
        else:
            return self._do_command(
                '{0}/apps/{1}'.format(self.SUPERVISOR_API_VERSION, app_id),
                required_version,
                method='GET'
            )

    def __service_request(self, endpoint, device_uuid, image_id):
        """
        Service request.

        Args:
            endpoint (str): service endpoint.
            device_uuid (str): device uuid.
            image_id (int): id of the image to start

        """

        device = self.device.get(device_uuid)
        app_id = device['belongs_to__application']['__id']

        if (parse_version(self.MIN_SUPERVISOR_MC_API) > parse_version(device['supervisor_version'])):
            raise exceptions.UnsupportedFunction(self.MIN_SUPERVISOR_MC_API, device['supervisor_version'])

        data = {
            'deviceId': device['id'],
            'appId': app_id,
            'data': {
                'appId': app_id,
                'imageId': image_id
            }
        }

        return self.base_request.request(
            '/supervisor/v2/applications/{app_id}/{endpoint}'.format(app_id=app_id, endpoint=endpoint), 'POST', data=data,
            endpoint=self.settings.get('api_endpoint')
        )

    def start_service(self, device_uuid, image_id):
        """
        Start a service on device.

        Args:
            device_uuid (str): device uuid.
            image_id (int): id of the image to start

        Examples:
            >>> balena.models.supervisor.start_service('f3887b184396844f52402c5cf09bd3b9', 392229)
            OK

        """

        return self.__service_request('start-service', device_uuid, image_id)

    def stop_service(self, device_uuid, image_id):
        """
        Stop a service on device.

        Args:
            device_uuid (str): device uuid.
            image_id (int): id of the image to start

        Examples:
            >>> balena.models.supervisor.stop_service('f3887b184396844f52402c5cf09bd3b9', 392229)
            OK

        """

        return self.__service_request('stop-service', device_uuid, image_id)

    def restart_service(self, device_uuid, image_id):
        """
        Restart a service on device.

        Args:
            device_uuid (str): device uuid.
            image_id (int): id of the image to start

        Examples:
            >>> balena.models.supervisor.restart_service('f3887b184396844f52402c5cf09bd3b9', 392229)
            OK

        """

        return self.__service_request('restart-service', device_uuid, image_id)
