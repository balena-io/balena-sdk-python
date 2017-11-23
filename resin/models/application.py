from ..base_request import BaseRequest
from ..settings import Settings
from .config import Config
from .. import exceptions

from datetime import datetime

# TODO: support both app_id and app_name
class Application(object):
    """
    This class implements application model for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()

    def get_all(self):
        """
        Get all applications.

        Returns:
            list: list contains info of applications.

        Examples:
            >>> resin.models.application.get_all()
            [{u'app_name': u'RPI1', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9020)'}, u'git_repository': u'g_trong_nghia_nguyen@git.resin.io:g_trong_nghia_nguyen/rpi1.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi', u'commit': None, u'id': 9020}, {u'app_name': u'RPI2', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9019)'}, u'git_repository': u'g_trong_nghia_nguyen@git.resin.io:g_trong_nghia_nguyen/rpi2.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi2', u'commit': None, u'id': 9019}]

        """

        return self.base_request.request(
            'application', 'GET', endpoint=self.settings.get('pine_endpoint')
        )['d']

    def get(self, name):
        """
        Get a single application.

        Args:
            name (str): application name.

        Returns:
            dict: application info.

        Raises:
            ApplicationNotFound: if application couldn't be found.
            AmbiguousApplication: when more than one application is returned.

        Examples:
            >>> resin.models.application.get('RPI1')
            {u'app_name': u'RPI1', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9020)'}, u'git_repository': u'g_trong_nghia_nguyen@git.resin.io:g_trong_nghia_nguyen/rpi1.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi', u'commit': None, u'id': 9020}

        """

        params = {
            'filter': 'app_name',
            'eq': name
        }
        try:
            apps = self.base_request.request(
                'application', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d']
            if len(apps) > 1:
                raise exceptions.AmbiguousApplication(name)
            return apps[0]
        except IndexError:
            raise exceptions.ApplicationNotFound(name)

    def has(self, name):
        """
        Check if an application exists.

        Args:
            name (str): application name.

        Returns:
            bool: True if application exists, False otherwise.

        Examples:
            >>> resin.models.application.has('RPI1')
            True

        """

        params = {
            'filter': 'app_name',
            'eq': name
        }
        app = self.base_request.request(
            'application', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']
        return bool(app)

    def has_any(self):
        """
        Check if the user has any applications.

        Returns:
            bool: True if user has any applications, False otherwise.

        Examples:
            >>> resin.models.application.has_any()
            True

        """

        apps = self.base_request.request(
            'application', 'GET', endpoint=self.settings.get('pine_endpoint')
        )['d']
        return bool(apps)

    def get_by_id(self, app_id):
        """
        Get a single application by application id.

        Args:
            app_id (str): application id.

        Returns:
            dict: application info.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >>> resin.models.application.get_by_id(9020)
            {u'app_name': u'RPI1', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9020)'}, u'git_repository': u'g_trong_nghia_nguyen@git.resin.io:g_trong_nghia_nguyen/rpi1.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi', u'commit': None, u'id': 9020}

        """

        params = {
            'filter': 'id',
            'eq': app_id
        }
        try:
            return self.base_request.request(
                'application', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d'][0]
        except IndexError:
            raise exceptions.ApplicationNotFound(app_id)

    def create(self, name, device_type):
        """
        Create an application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.
            device_type (str): device type (display form).

        Returns:
            dict: application info.

        Raises:
            InvalidDeviceType: if device type is not supported.

        Examples:
            >>> resin.models.application.create('Edison','Intel Edison')
            '{"id":9021,"user":{"__deferred":{"uri":"/ewa/user(5397)"},"__id":5397},"app_name":"Edison","git_repository":"g_trong_nghia_nguyen@git.resin.io:g_trong_nghia_nguyen/edison.git","commit":null,"device_type":"intel-edison","__metadata":{"uri":"/ewa/application(9021)","type":""}}'

        """

        device_types = self.config.get_device_types()
        device_slug = [device['slug'] for device in device_types
                       if device['name'] == device_type]
        if device_slug:
            data = {
                'app_name': name,
                'device_type': device_slug[0]
            }
            return self.base_request.request(
                'application', 'POST', data=data,
                endpoint=self.settings.get('pine_endpoint'), login=True
            )
        else:
            raise exceptions.InvalidDeviceType(device_type)

    def remove(self, name):
        """
        Remove application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.

        Examples:
            >>> resin.models.application.remove('Edison')
            'OK'

        """

        params = {
            'filter': 'app_name',
            'eq': name
        }
        return self.base_request.request(
            'application', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )

    def restart(self, name):
        """
        Restart application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >>> resin.models.application.restart('RPI1')
            'OK'

        """

        app = self.get(name)
        return self.base_request.request(
            'application/{0}/restart'.format(app['id']), 'POST',
            endpoint=self.settings.get('api_endpoint'), login=True
        )

    def get_config(self, app_id):
        """
        Download application config.json.

        Args:
            app_id (str): application id.

        Returns:
            dict: application config.json content.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >>> resin.models.application.get_config('106640')
            {u'applicationName': u'RPI3', u'username': u'nghiant2710', u'apiKey': u'kIaqS6ZLOoxkFzpzqSYhWtr2lj6m8KZi', u'vpnPort': 443, u'listenPort': 48484, u'pubnubSubscribeKey': u'sub-c-bbc12eba-ce4a-11e3-9782-02ee2ddab7fe', u'vpnEndpoint': u'vpn.resin.io', u'userId': 189, u'files': {u'network/network.config': u'[service_home_ethernet]\nType = ethernet\nNameservers = 8.8.8.8,8.8.4.4', u'network/settings': u'[global]\nOfflineMode=false\nTimeUpdates=manual\n\n[WiFi]\nEnable=true\nTethering=false\n\n[Wired]\nEnable=true\nTethering=false\n\n[Bluetooth]\nEnable=true\nTethering=false'}, u'pubnubPublishKey': u'pub-c-6cbce8db-bfd1-4fdf-a8c8-53671ae2b226', u'apiEndpoint': u'https://api.resin.io', u'connectivity': u'connman', u'deviceType': u'raspberrypi3', u'mixpanelToken': u'99eec53325d4f45dd0633abd719e3ff1', u'deltaEndpoint': u'https://delta.resin.io', u'appUpdatePollInterval': 60000, u'applicationId': 106640, u'registryEndpoint': u'registry.resin.io'}
        """

        # Application not found will be raised if can't get app by id.
        self.get_by_id(app_id)
        data = {
            'appId': app_id
        }
        return self.base_request.request(
            '/download-config', 'POST', data=data,
            endpoint=self.settings.get('api_endpoint')
        )

    def enable_rolling_updates(self, app_id):
        """
        Enable Rolling update on application.

        Args:
            app_id (str): application id.

        Returns:
            OK/error.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >> > resin.models.application.enable_rolling_updates('106640')
            'OK'
        """

        params = {
            'filter': 'id',
            'eq': app_id
        }
        data = {
            'should_track_latest_release': True
        }

        return self.base_request.request(
            'application', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def disable_rolling_updates(self, app_id):
        """
        Disable Rolling update on application.

        Args:
            name (str): application id.

        Returns:
            OK/error.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        Examples:
            >> > resin.models.application.disable_rolling_updates('106640')
            'OK'
        """

        params = {
            'filter': 'id',
            'eq': app_id
        }
        data = {
            'should_track_latest_release': False
        }

        return self.base_request.request(
            'application', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def enable_device_urls(self, app_id):
        """
        Enable device urls for all devices that belong to an application

        Args:
            app_id (str): application id.

        Returns:
            OK/error.

        Examples:
            >> > resin.models.application.enable_device_urls('5685')
            'OK'

        """

        params = {
            'filter': 'belongs_to__application',
            'eq': app_id
        }
        data = {
            'is_web_accessible': True
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def disable_device_urls(self, app_id):
        """
        Disable device urls for all devices that belong to an application.

        Args:
            app_id (str): application id.

        Returns:
            OK/error.

        Examples:
            >> > resin.models.application.disable_device_urls('5685')
            'OK'

        """

        params = {
            'filter': 'belongs_to__application',
            'eq': app_id
        }
        data = {
            'is_web_accessible': False
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def grant_support_access(self, app_id, valid_period):
        """
        Grant support access to an application until a specified time.

        Args:
            app_id (str): application id.
            valid_period (int): valid period in hour.

        Returns:
            OK/error.

        Examples:
            >> > resin.models.application.grant_support_access('5685', 2)
            'OK'

        """

        if not valid_period or int(valid_period) <= 0:
            raise exceptions.InvalidParameter(`valid_period`, valid_period)

        expiry_timestamp = ((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() + int(valid_period) * 3600) * 1000

        params = {
            'filter': 'id',
            'eq': app_id
        }

        data = {
            'is_accessible_by_support_until__date': expiry_timestamp
        }

        return self.base_request.request(
            'application', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def revoke_support_access(self, app_id):
        """
        Revoke support access to an application.

        Args:
            app_id (str): application id.

        Returns:
            OK/error.

        Examples:
            >> > resin.models.application.revoke_support_access('5685')
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': app_id
        }

        data = {
            'is_accessible_by_support_until__date': None
        }

        return self.base_request.request(
            'application', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def generate_provisioning_key(self, app_id):
        """
        Generate a device provisioning key for a specific application.

        Args:
            app_id (str): application id.

        Returns:
            str: device provisioning key.

        Examples:
            >> > resin.models.application.generate_provisioning_key('5685')
            'GThZJps91PoJCdzfYqF7glHXzBDGrkr9'

        """

        # Make sure user has access to the app_id
        self.get_by_id(app_id)

        return self.base_request.request(
            '/api-key/application/{}/provisioning'.format(app_id),
            'POST',
            endpoint=self.settings.get('api_endpoint')
        )
