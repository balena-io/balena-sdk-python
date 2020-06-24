try:  # Python 3 imports
    from urllib.parse import urljoin
except ImportError:  # Python 2 imports
    from urlparse import urljoin

from ..auth import Auth
from ..base_request import BaseRequest
from ..settings import Settings
from .config import Config
from .release import Release
from .. import exceptions
from ..utils import is_id

from datetime import datetime
import json
from math import isinf
from collections import defaultdict


# TODO: support both app_id and app_name
class Application(object):
    """
    This class implements application model for balena python SDK.

    The returned objects properties are `__metadata, actor, app_name, application_type, commit, depends_on__application, device_type, id, is_accessible_by_support_until__date, should_track_latest_release, slug, user`.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()
        self.auth = Auth()
        self.release = Release()

    def __get_single_install_summary(self, raw_data):
        """
        Builds summary data for an image install or gateway download

        """

        image = raw_data['image'][0]
        service = image['is_a_build_of__service'][0]
        release = None

        if 'is_provided_by__release' in raw_data:
            release = raw_data['is_provided_by__release'][0]

        install = {
            'service_name': service['service_name'],
            'image_id': image['id'],
            'service_id': service['id'],
        }

        if release:
            install['commit'] = release['commit']

        raw_data.pop('is_provided_by__release', None)
        raw_data.pop('image', None)
        install.update(raw_data)

        return install

    def __generate_current_service_details(self, raw_data):
        groupedServices = defaultdict(list)

        for obj in [self.__get_single_install_summary(i) for i in raw_data['image_install']]:
            groupedServices[obj.pop('service_name', None)].append(obj)

        raw_data['current_services'] = dict(groupedServices)
        raw_data['current_gateway_downloads'] = [self.__get_single_install_summary(i) for i in raw_data['gateway_download']]
        raw_data.pop('image_install', None)
        raw_data.pop('gateway_download', None)

        return raw_data

    def get_all(self):
        """
        Get all applications (including collaborator applications).

        Returns:
            list: list contains info of applications.

        Examples:
            >>> balena.models.application.get_all()
            '[{u'depends_on__application': None, u'should_track_latest_release': True, u'app_name': u'foo', u'application_type': {u'__deferred': {u'uri': u'/resin/application_type(5)'}, u'__id': 5}, u'__metadata': {u'type': u'', u'uri': u'/resin/application(12345)'}, u'is_accessible_by_support_until__date': None, u'actor': 12345, u'id': 12345, u'user': {u'__deferred': {u'uri': u'/resin/user(12345)'}, u'__id': 12345}, u'device_type': u'raspberrypi3', u'commit': None, u'slug': u'my_user/foo'}, {u'depends_on__application': None, u'should_track_latest_release': True, u'app_name': u'bar', u'application_type': {u'__deferred': {u'uri': u'/resin/application_type(5)'}, u'__id': 5}, u'__metadata': {u'type': u'', u'uri': u'/resin/application(12346)'}, u'is_accessible_by_support_until__date': None, u'actor': 12345, u'id': 12346, u'user': {u'__deferred': {u'uri': u'/resin/user(12345)'}, u'__id': 12345}, u'device_type': u'raspberrypi3', u'commit': None, u'slug': u'my_user/bar'}]'

        """

        return self.base_request.request(
            'my_application', 'GET', endpoint=self.settings.get('pine_endpoint')
        )['d']

    def get_all_with_device_service_details(self, expand_release=False):
        """
        Get all applications (including collaborator applications) along with associated services' essential details.

        Args:
            expand_release (Optional[bool]): Set this parameter to True then the commit of service details will be included.

        Returns:
            list: list contains info of applications.

        """

        release = ''
        if expand_release:
            release = ",is_provided_by__release($select=id,commit)"

        raw_query = "$expand=owns__device($expand=image_install($select=id,download_progress,status,install_date&$filter=status%20ne%20'deleted'&$expand=image($select=id&$expand=is_a_build_of__service($select=id,service_name)){release}),gateway_download($select=id,download_progress,status&$filter=status%20ne%20'deleted'&$expand=image($select=id&$expand=is_a_build_of__service($select=id,service_name))))".format(release=release)

        raw_data = self.base_request.request(
            'my_application', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

        for app in raw_data:
            map(self.__generate_current_service_details, app['owns__device'])

        return raw_data

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
            >>> balena.models.application.get('foo')
            '{u'depends_on__application': None, u'should_track_latest_release': True, u'app_name': u'foo', u'application_type': {u'__deferred': {u'uri': u'/resin/application_type(5)'}, u'__id': 5}, u'__metadata': {u'type': u'', u'uri': u'/resin/application(12345)'}, u'is_accessible_by_support_until__date': None, u'actor': 12345, u'id': 12345, u'user': {u'__deferred': {u'uri': u'/resin/user(12345)'}, u'__id': 12345}, u'device_type': u'raspberrypi3', u'commit': None, u'slug': u'my_user/foo'}'

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

    def get_with_device_service_details(self, name, expand_release=False):
        """
        Get a single application along with its associated services' essential details.

        Args:
            name (str): application name.
            expand_release (Optional[bool]): Set this parameter to True then the commit of service details will be included.

        Returns:
            dict: application info.

        Raises:
            ApplicationNotFound: if application couldn't be found.
            AmbiguousApplication: when more than one application is returned.

        Examples:
            >>> balena.models.application.get('test-app')
            '{u'depends_on__application': None, u'should_track_latest_release': True, u'app_name': u'test-app', u'application_type': {u'__deferred': {u'uri': u'/resin/application_type(5)'}, u'__id': 5}, u'__metadata': {u'type': u'', u'uri': u'/resin/application(1252573)'}, u'is_accessible_by_support_until__date': None, u'actor': 3259381, u'slug': u'nghiant27101/test-app', u'owns__device': [{u'os_variant': u'prod', u'__metadata': {u'type': u'', u'uri': u'/resin/device(1460194)'}, u'is_managed_by__service_instance': {u'__deferred': {u'uri': u'/resin/service_instance(117953)'}, u'__id': 117953}, u'should_be_running__release': None, u'belongs_to__user': {u'__deferred': {u'uri': u'/resin/user(5227)'}, u'__id': 5227}, u'is_web_accessible': False, u'device_type': u'raspberrypi3', u'belongs_to__application': {u'__deferred': {u'uri': u'/resin/application(1252573)'}, u'__id': 1252573}, u'id': 1460194, u'is_locked_until__date': None, u'logs_channel': None, u'uuid': u'b6070f4fea5edf808b576123157fe5ec', u'is_managed_by__device': None, u'should_be_managed_by__supervisor_release': None, u'actor': 3505229, u'note': None, u'os_version': u'balenaOS 2.29.2+rev2', u'longitude': u'105.8516', u'last_connectivity_event': u'2019-05-06T07:30:20.230Z', u'is_on__commit': u'ddf95bef72a981f826bf5303df11f318dbdbff23', u'gateway_download': [], u'location': u'Hanoi, Hanoi, Vietnam', u'status': u'Idle', u'public_address': u'14.162.159.155', u'is_connected_to_vpn': False, u'custom_latitude': u'', u'is_active': True, u'provisioning_state': u'', u'latitude': u'21.0313', u'custom_longitude': u'', u'is_online': False, u'supervisor_version': u'9.0.1', u'ip_address': u'192.168.100.20', u'provisioning_progress': None, u'is_accessible_by_support_until__date': None, u'created_at': u'2019-01-09T11:41:19.336Z', u'download_progress': None, u'last_vpn_event': u'2019-05-06T07:30:20.230Z', u'device_name': u'spring-morning', u'image_install': [{u'status': u'Running', u'__metadata': {u'type': u'', u'uri': u'/resin/image_install(34691843)'}, u'image': [{u'is_a_build_of__service': [{u'service_name': u'main', u'__metadata': {u'type': u'', u'uri': u'/resin/service(92238)'}, u'id': 92238}], u'__metadata': {u'type': u'', u'uri': u'/resin/image(1117181)'}, u'id': 1117181}], u'download_progress': None, u'install_date': u'2019-04-29T10:24:23.476Z', u'id': 34691843}], u'local_id': None, u'vpn_address': None}, {u'os_variant': u'prod', u'__metadata': {u'type': u'', u'uri': u'/resin/device(1308755)'}, u'is_managed_by__service_instance': {u'__deferred': {u'uri': u'/resin/service_instance(2205)'}, u'__id': 2205}, u'should_be_running__release': None, u'belongs_to__user': {u'__deferred': {u'uri': u'/resin/user(5227)'}, u'__id': 5227}, u'is_web_accessible': False, u'device_type': u'raspberrypi3', u'belongs_to__application': {u'__deferred': {u'uri': u'/resin/application(1252573)'}, u'__id': 1252573}, u'id': 1308755, u'is_locked_until__date': None, u'logs_channel': None, u'uuid': u'531e5cc893b7df1e1118121059d93eee', u'is_managed_by__device': None, u'should_be_managed_by__supervisor_release': None, u'actor': 3259425, u'note': None, u'os_version': u'Resin OS 2.15.1+rev1', u'longitude': u'105.85', u'last_connectivity_event': u'2018-09-27T14:48:53.034Z', u'is_on__commit': u'19ab64483292f0a52989d0ce15ee3d21348dbfce', u'gateway_download': [], u'location': u'Hanoi, Hanoi, Vietnam', u'status': u'Idle', u'public_address': u'14.231.247.155', u'is_connected_to_vpn': False, u'custom_latitude': u'', u'is_active': True, u'provisioning_state': u'', u'latitude': u'21.0333', u'custom_longitude': u'', u'is_online': False, u'supervisor_version': u'7.16.6', u'ip_address': u'192.168.0.102', u'provisioning_progress': None, u'is_accessible_by_support_until__date': None, u'created_at': u'2018-09-12T04:30:13.549Z', u'download_progress': None, u'last_vpn_event': u'2018-09-27T14:48:53.034Z', u'device_name': u'nameless-resonance', u'image_install': [{u'status': u'Running', u'__metadata': {u'type': u'', u'uri': u'/resin/image_install(33844685)'}, u'image': [{u'is_a_build_of__service': [{u'service_name': u'main', u'__metadata': {u'type': u'', u'uri': u'/resin/service(92238)'}, u'id': 92238}], u'__metadata': {u'type': u'', u'uri': u'/resin/image(513014)'}, u'id': 513014}], u'download_progress': None, u'install_date': u'2018-09-27T13:53:04.748Z', u'id': 33844685}], u'local_id': None, u'vpn_address': None}], u'user': {u'__deferred': {u'uri': u'/resin/user(5227)'}, u'__id': 5227}, u'device_type': u'raspberrypi3', u'commit': u'ddf95bef72a981f826bf5303df11f318dbdbff23', u'id': 1252573}'

        """

        release = ''
        if expand_release:
            release = ",is_provided_by__release($select=id,commit)"

        raw_query = "$filter=app_name%20eq%20'{app_name}'&$expand=owns__device($expand=image_install($select=id,download_progress,status,install_date&$filter=status%20ne%20'deleted'&$expand=image($select=id&$expand=is_a_build_of__service($select=id,service_name)){release}),gateway_download($select=id,download_progress,status&$filter=status%20ne%20'deleted'&$expand=image($select=id&$expand=is_a_build_of__service($select=id,service_name))))".format(app_name=name, release=release)

        try:
            raw_data = self.base_request.request(
                'application', 'GET', raw_query=raw_query,
                endpoint=self.settings.get('pine_endpoint')
            )['d']

            if raw_data and 'owns__device' in raw_data:
                map(self.__generate_current_service_details, raw_data['owns__device'])
            if len(raw_data) > 1:
                raise exceptions.AmbiguousApplication(name)
            return raw_data[0]
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
            >>> balena.models.application.get_by_owner('foo', 'my_user')
            '{u'depends_on__application': None, u'should_track_latest_release': True, u'app_name': u'foo', u'application_type': {u'__deferred': {u'uri': u'/resin/application_type(5)'}, u'__id': 5}, u'__metadata': {u'type': u'', u'uri': u'/resin/application(12345)'}, u'is_accessible_by_support_until__date': None, u'actor': 12345, u'id': 12345, u'user': {u'__deferred': {u'uri': u'/resin/user(12345)'}, u'__id': 12345}, u'device_type': u'raspberrypi3', u'commit': None, u'slug': u'my_user/foo'}'

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
            >>> balena.models.application.has('foo')
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

        return len(self.get_all()) > 0

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
            >>> balena.models.application.get_by_id(12345)
            '{u'depends_on__application': None, u'should_track_latest_release': True, u'app_name': u'foo', u'application_type': {u'__deferred': {u'uri': u'/resin/application_type(5)'}, u'__id': 5}, u'__metadata': {u'type': u'', u'uri': u'/resin/application(12345)'}, u'is_accessible_by_support_until__date': None, u'actor': 12345, u'id': 12345, u'user': {u'__deferred': {u'uri': u'/resin/user(12345)'}, u'__id': 12345}, u'device_type': u'raspberrypi3', u'commit': None, u'slug': u'my_user/foo'}'

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

    def create(self, name, device_type, organization, app_type=None):
        """
        Create an application. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): application name.
            device_type (str): device type (display form).
            organization (str): handle or id of the organization that the application will belong to.
            app_type (Optional[str]): application type.

        Returns:
            dict: application info.

        Raises:
            InvalidDeviceType: if device type is not supported.
            InvalidApplicationType: if app type is not supported.
            InvalidParameter: if organization is missing.
            OrganizationNotFound: if organization couldn't be found.

        Examples:
            >>> balena.models.application.create('foo', 'Raspberry Pi 3', 12345, 'microservices-starter')
            '{u'depends_on__application': None, u'should_track_latest_release': True, u'app_name': u'foo', u'application_type': {u'__deferred': {u'uri': u'/resin/application_type(5)'}, u'__id': 5}, u'__metadata': {u'type': u'', u'uri': u'/resin/application(12345)'}, u'is_accessible_by_support_until__date': None, u'actor': 12345, u'id': 12345, u'user': {u'__deferred': {u'uri': u'/resin/user(12345)'}, u'__id': 12345}, u'device_type': u'raspberrypi3', u'commit': None, u'slug': u'my_user/foo'}'

        """

        if not organization:
            raise exceptions.InvalidParameter('organization', organization)
        else:
            if is_id(organization):
                key = 'id'
            else:
                key = 'handle'
            raw_query = "$top=1&$select=id&$filter={key}%20eq%20'{value}'".format(key=key, value=organization)

            org = self.base_request.request(
                'organization', 'GET', raw_query=raw_query,
                endpoint=self.settings.get('pine_endpoint'), login=True
            )['d']

            if not org:
                raise exceptions.OrganizationNotFound(organization)

        device_types = self.config.get_device_types()
        device_manifest = [device for device in device_types if device['name'] == device_type]

        if device_manifest:
            if device_manifest[0]['state'] == 'DISCONTINUED':
                raise exceptions.BalenaDiscontinuedDeviceType(device_type)

            data = {
                'app_name': name,
                'device_type': device_manifest[0]['slug'],
                'organization': org['id']
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

    def get_config(self, app_id, version, **options):
        """
        Download application config.json.

        Args:
            app_id (str): application id.
            version (str): the OS version of the image.
            **options (dict): OS configuration keyword arguments to use. The available options are listed below:
                network (Optional[str]): the network type that the device will use, one of 'ethernet' or 'wifi' and defaults to 'ethernet' if not specified.
                appUpdatePollInterval (Optional[str]): how often the OS checks for updates, in minutes.
                wifiKey (Optional[str]): the key for the wifi network the device will connect to.
                wifiSsid (Optional[str]): the ssid for the wifi network the device will connect to.
                ip (Optional[str]): static ip address.
                gateway (Optional[str]): static ip gateway.
                netmask (Optional[str]): static ip netmask.

        Returns:
            dict: application config.json content.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        """

        # Application not found will be raised if can't get app by id.
        self.get_by_id(app_id)

        if not version:
            raise exceptions.MissingOption('An OS version is required when calling application.get_config()')

        if 'network' not in options:
            options['network'] = 'ethernet'

        options['appId'] = app_id
        options['version'] = version

        return self.base_request.request(
            '/download-config', 'POST', data=options,
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

    def set_to_release(self, app_id, full_release_hash):
        """
        Set an application to a specific commit.

        Args:
            app_id (str): application id.
            full_release_hash (str) : full_release_hash.

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
            'commit': full_release_hash,
            'should_track_latest_release': False
        }

        return self.base_request.request(
            'application', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def will_track_new_releases(self, app_id):
        """
        Get whether the application is configured to receive updates whenever a new release is available.

        Args:
            app_id (str): application id.

        Returns:
            bool: is tracking the latest release.

        Examples:
            >> > balena.models.application.will_track_new_releases('5685')
            True

        """

        return bool(self.get_by_id(app_id)['should_track_latest_release'])

    def is_tracking_latest_release(self, app_id):
        """
        Get whether the application is up to date and is tracking the latest release for updates.

        Args:
            app_id (str): application id.

        Returns:
            bool: is tracking the latest release.

        Examples:
            >> > balena.models.application.is_tracking_latest_release('5685')
            True

        """

        app = self.get_by_id(app_id)
        latest_release = None

        try:
            latest_release = self.release.get_latest_by_application(app_id)
        except exceptions.ReleaseNotFound:
            pass

        return bool(app['should_track_latest_release']) and (not latest_release or app['commit'] == latest_release['commit'])

    def get_target_release_hash(self, app_id):
        """
        Get the hash of the current release for a specific application.

        Args:
            app_id (str): application id.

        Returns:
            str: The release hash of the current release.

        Examples:
            >>> balena.models.application.get_target_release_hash('5685')

        """

        return self.get_by_id(app_id)['commit']

    def track_latest_release(self, app_id):
        """
        Configure a specific application to track the latest available release.

        Args:
            app_id (str): application id.

        Examples:
            >>> balena.models.application.track_latest_release('5685')

        """

        latest_release = None

        try:
            latest_release = self.release.get_latest_by_application(app_id)
        except exceptions.ReleaseNotFound:
            pass

        params = {
            'filter': 'id',
            'eq': app_id
        }

        data = {
            'should_track_latest_release': True
        }

        if latest_release:
            data['commit'] = latest_release['commit']

        return self.base_request.request(
            'application', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def get_dashboard_url(self, app_id):
        """
        Get Dashboard URL for a specific application.

        Args:
            app_id (str): application id.

        Raises:
            InvalidParameter: if the app_id is not a finite number.

        Returns:
            str: Dashboard URL for the specific application.

        Examples:
            >>> balena.models.application.get_dashboard_url('1476418')
            https://dashboard.balena-cloud.com/apps/1476418

        """
        try:
            if isinf(int(app_id)):
                raise exceptions.InvalidParameter('app_id', app_id)
        except ValueError:
            raise exceptions.InvalidParameter('app_id', app_id)

        return urljoin(
            self.settings.get('api_endpoint').replace('api', 'dashboard'),
            '/apps/{app_id}'.format(app_id=app_id)
        )
