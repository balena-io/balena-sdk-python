from ..auth import Auth
from ..base_request import BaseRequest
from ..settings import Settings
from .config import Config
from .. import exceptions

from datetime import datetime
import json


# TODO: support both app_id and app_name
class Application(object):
    """
    This class implements application model for balena python SDK.

    Due to API changes, the returned Application object schema has changed. Here are the formats of the old and new returned objects.

    The old returned object's properties: `__metadata, actor, app_name, application, commit, device_type, git_repository, id, should_track_latest_release, support_expiry_date, user, version`.

    The new returned object's properties (since python SDK v2.0.0): `__metadata, actor, app_name, commit, depends_on__application, device_type, git_repository, id, is_accessible_by_support_until__date, should_track_latest_release, user, version`.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()
        self.auth = Auth()

    def get_all(self):
        """
        Get all applications (including collaborator applications).

        Returns:
            list: list contains info of applications.

        Examples:
            >>> balena.models.application.get_all()
            [{u'app_name': u'RPI1', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9020)'}, u'git_repository': u'g_trong_nghia_nguyen@git.balena.io:g_trong_nghia_nguyen/rpi1.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi', u'commit': None, u'id': 9020}, {u'app_name': u'RPI2', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9019)'}, u'git_repository': u'g_trong_nghia_nguyen@git.balena.io:g_trong_nghia_nguyen/rpi2.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi2', u'commit': None, u'id': 9019}]

        """

        return self.base_request.request(
            'my_application', 'GET', endpoint=self.settings.get('pine_endpoint')
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
            >>> balena.models.application.get('RPI1')
            {u'app_name': u'RPI1', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9020)'}, u'git_repository': u'g_trong_nghia_nguyen@git.balena.io:g_trong_nghia_nguyen/rpi1.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi', u'commit': None, u'id': 9020}

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

    def get_by_owner(self, name, owner):
        """
        Get a single application.

        Args:
            name (str): application name.
            owner (str):  owner's username.

        Returns:
            dict: application info.

        Raises:
            ApplicationNotFound: if application couldn't be found.
            AmbiguousApplication: when more than one application is returned.

        Examples:
            >>> balena.models.application.get('RPI1')
            {u'app_name': u'RPI1', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9020)'}, u'git_repository': u'g_trong_nghia_nguyen@git.balena.io:g_trong_nghia_nguyen/rpi1.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi', u'commit': None, u'id': 9020}

        """

        slug = '{owner}/{app_name}'.format(owner=owner.lower(), app_name=name.lower())

        params = {
            'filter': 'slug',
            'eq': slug
        }
        try:
            apps = self.base_request.request(
                'application', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d']
            if len(apps) > 1:
                raise exceptions.AmbiguousApplication(slug)
            return apps[0]
        except IndexError:
            raise exceptions.ApplicationNotFound(slug)

    def has(self, name):
        """
        Check if an application exists.

        Args:
            name (str): application name.

        Returns:
            bool: True if application exists, False otherwise.

        Examples:
            >>> balena.models.application.has('RPI1')
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
            >>> balena.models.application.has_any()
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
            >>> balena.models.application.get_by_id(9020)
            {u'app_name': u'RPI1', u'__metadata': {u'type': u'', u'uri': u'/ewa/application(9020)'}, u'git_repository': u'g_trong_nghia_nguyen@git.balena.io:g_trong_nghia_nguyen/rpi1.git', u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'device_type': u'raspberry-pi', u'commit': None, u'id': 9020}

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

    def create(self, name, device_type, app_type=None):
        """
        Create an application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.
            device_type (str): device type (display form).
            app_type (Optional[str]): application type.

        Returns:
            dict: application info.

        Raises:
            InvalidDeviceType: if device type is not supported.
            InvalidApplicationType: if app type is not supported.

        Examples:
            >>> balena.models.application.create('Foobar', 'Raspberry Pi 3', 'microservices-starter')
            '{"id":1005767,"user":{"__deferred":{"uri":"/balena/user(32986)"},"__id":32986},"depends_on__application":null,"actor":2630233,"app_name":"Foobar","git_repository":"pythonsdk_test_balena/foobar","commit":null,"application_type":{"__deferred":{"uri":"/balena/application_type(5)"},"__id":5},"device_type":"raspberrypi3","should_track_latest_release":true,"is_accessible_by_support_until__date":null,"__metadata":{"uri":"/balena/application(1005767)","type":""}}'

        """

        device_types = self.config.get_device_types()
        device_slug = [device['slug'] for device in device_types
                       if device['name'] == device_type]
        if device_slug:

            data = {
                'app_name': name,
                'device_type': device_slug[0]
            }

            if app_type:

                params = {
                    'filter': 'slug',
                    'eq': app_type
                }

                app_type_detail = self.base_request.request(
                    'application_type', 'GET', params=params,
                    endpoint=self.settings.get('pine_endpoint'), login=True
                )['d']

                if not app_type_detail:
                    raise exceptions.InvalidApplicationType(app_type)

                data['application_type'] = app_type_detail[0]['id']

            return json.loads(self.base_request.request(
                'application', 'POST', data=data,
                endpoint=self.settings.get('pine_endpoint'), login=True
            ).decode('utf-8'))
        else:
            raise exceptions.InvalidDeviceType(device_type)

    def remove(self, name):
        """
        Remove application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.

        Examples:
            >>> balena.models.application.remove('Edison')
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
            >>> balena.models.application.restart('RPI1')
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
            >>> balena.models.application.get_config('106640')
            {u'applicationName': u'RPI3', u'username': u'nghiant2710', u'apiKey': u'kIaqS6ZLOoxkFzpzqSYhWtr2lj6m8KZi', u'vpnPort': 443, u'listenPort': 48484, u'pubnubSubscribeKey': u'sub-c-bbc12eba-ce4a-11e3-9782-02ee2ddab7fe', u'vpnEndpoint': u'vpn.balena.io', u'userId': 189, u'files': {u'network/network.config': u'[service_home_ethernet]\nType = ethernet\nNameservers = 8.8.8.8,8.8.4.4', u'network/settings': u'[global]\nOfflineMode=false\nTimeUpdates=manual\n\n[WiFi]\nEnable=true\nTethering=false\n\n[Wired]\nEnable=true\nTethering=false\n\n[Bluetooth]\nEnable=true\nTethering=false'}, u'pubnubPublishKey': u'pub-c-6cbce8db-bfd1-4fdf-a8c8-53671ae2b226', u'apiEndpoint': u'https://api.balena.io', u'connectivity': u'connman', u'deviceType': u'raspberrypi3', u'mixpanelToken': u'11111111111111111111111111111111', u'deltaEndpoint': u'https://delta.balena.io', u'appUpdatePollInterval': 60000, u'applicationId': 106640, u'registryEndpoint': u'registry.balena.io'}
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
            >> > balena.models.application.enable_rolling_updates('106640')
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
            >> > balena.models.application.disable_rolling_updates('106640')
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
            >> > balena.models.application.enable_device_urls('5685')
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
            >> > balena.models.application.disable_device_urls('5685')
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

    def grant_support_access(self, app_id, expiry_timestamp):
        """
        Grant support access to an application until a specified time.

        Args:
            app_id (str): application id.
            expiry_timestamp (int): a timestamp in ms for when the support access will expire.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.application.grant_support_access('5685', 1511974999000)
            'OK'

        """

        if not expiry_timestamp or expiry_timestamp <= int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000):
            raise exceptions.InvalidParameter('expiry_timestamp', expiry_timestamp)

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
            >> > balena.models.application.revoke_support_access('5685')
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
            >> > balena.models.application.generate_provisioning_key('5685')
            'GThZJps91PoJCdzfYqF7glHXzBDGrkr9'

        """

        # Make sure user has access to the app_id
        self.get_by_id(app_id)

        return self.base_request.request(
            '/api-key/application/{}/provisioning'.format(app_id),
            'POST',
            endpoint=self.settings.get('api_endpoint')
        )

    def set_to_release(self, app_id, commit_id):
        """
        Set an application to a specific commit.
        The commit will get updated on the next push unless rolling updates are disabled (there is a dedicated method for that which is balena.models.applicaion.disable_rolling_updates())

        Args:
            app_id (str): application id.
            commit_id (str) : commit id.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.application.set_to_release('5685', '7dba4e0c461215374edad74a5b78f470b894b5b7')
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': app_id
        }

        data = {
            'commit': commit_id
        }

        return self.base_request.request(
            'application', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )
