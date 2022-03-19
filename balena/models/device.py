import sys
import binascii
import os
from datetime import datetime
import json
from collections import defaultdict
import semver

try:  # Python 3 imports
    from urllib.parse import urljoin
except ImportError:  # Python 2 imports
    from urlparse import urljoin

from ..base_request import BaseRequest
from .config import Config
from .device_os import DeviceOs
from .device_type import DeviceType
from ..settings import Settings
from ..auth import Auth
from .. import exceptions
from ..resources import Message
from .application import Application
from .release import Release
from .hup import Hup


LOCAL_MODE_MIN_OS_VERSION = '2.0.0'
LOCAL_MODE_MIN_SUPERVISOR_VERSION = '4.0.0'
LOCAL_MODE_ENV_VAR = 'RESIN_SUPERVISOR_LOCAL_MODE'
OVERRIDE_LOCK_ENV_VAR = 'RESIN_OVERRIDE_LOCK'


# TODO: support both device uuid and device id
class DeviceStatus:
    """
    Balena device statuses.
    """

    IDLE = "Idle"
    CONFIGURING = "Configuring"
    UPDATING = "Updating"
    OFFLINE = "Offline"
    POST_PROVISIONING = "Post Provisioning"
    INACTIVE = "Inactive"


class Device:
    """
    This class implements device model for balena python SDK.

    Due to API changes, the returned Device object schema has changed. Here are the formats of the old and new returned objects.

    The old returned object's properties: `__metadata, actor, application, build, commit, created_at, custom_latitude, custom_longitude, device, device_type, download_progress, id, ip_address, is_connected_to_vpn, is_online, is_web_accessible, last_connectivity_event, last_vpn_event, latitude, local_id, location, lock_expiry_date, logs_channel, longitude, name, note, os_variant, os_version, provisioning_progress, provisioning_state, public_address, service_instance, status, supervisor_release, supervisor_version, support_expiry_date, user, uuid, vpn_address`.

    The new returned object's properties (since python SDK v2.0.0): `__metadata, actor, belongs_to__application, belongs_to__user, created_at, custom_latitude, custom_longitude, device_type, download_progress, id, ip_address, is_accessible_by_support_until__date, is_connected_to_vpn, is_locked_until__date, is_managed_by__device, is_managed_by__service_instance, is_on__commit, is_online, is_web_accessible, last_connectivity_event, last_vpn_event, latitude, local_id, location, logs_channel, longitude, name, note, os_variant, os_version, provisioning_progress, provisioning_state, public_address, should_be_managed_by__supervisor_release, should_be_running__build, status, supervisor_version, uuid, vpn_address`.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.config = Config()
        self.settings = Settings()
        self.application = Application()
        self.auth = Auth()
        self.release = Release()
        self.device_os = DeviceOs()
        self.device_type = DeviceType()
        self.hup = Hup()

    def __upsert_device_config_variable(self, device, name, value):
        try:
            data = {
                'device': device['id'],
                'name': name,
                'value': value
            }

            return self.base_request.request(
                'device_config_variable', 'POST', data=data,
                endpoint=self.settings.get('pine_endpoint')
            )
        except exceptions.RequestError as e:
            if 'Unique key constraint violated' in e.message or 'must be unique' in e.message:
                params = {
                    'filters': {
                        'device': device['id'],
                        'name': name
                    }
                }

                data = {
                    'value': value
                }

                return self.base_request.request(
                    'device_config_variable', 'PATCH', params=params, data=data,
                    endpoint=self.settings.get('pine_endpoint')
                )
            raise e

    def __get_applied_device_config_variable_value(self, uuid, name):
        raw_query = "$filter=uuid%20eq%20'{uuid}'&$expand=device_config_variable($select=value&$filter=name%20eq%20'{name}'),belongs_to__application($select=id&$expand=application_config_variable($select=value&$filter=name%20eq%20'{name}'))".format(name=name, uuid=uuid)

        raw_data = self.base_request.request(
            'device', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

        if len(raw_data) > 0:
            device_config = raw_data[0]['device_config_variable']
            app_config = raw_data[0]['belongs_to__application'][0]['application_config_variable']

            if device_config:
                return device_config[0]['value']
            elif app_config:
                return app_config[0]['value']

            return None
        else:
            raise exceptions.DeviceNotFound(uuid)

    def get(self, uuid):
        """
        Get a single device by device uuid.

        Args:
            uuid (str): device uuid.

        Returns:
            dict: device info.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.get('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            {u'__metadata': {u'type': u'', u'uri': u'/ewa/device(122950)'}, u'last_connectivity_event': u'1970-01-01T00:00:00.000Z', u'is_web_accessible': False, u'device_type': u'raspberry-pi', u'id': 122950, u'logs_channel': None, u'uuid': u'8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', u'application': {u'__deferred': {u'uri': u'/ewa/application(9020)'}, u'__id': 9020}, u'note': None, u'os_version': None, u'location': u'', u'latitude': u'', u'status': None, u'public_address': u'', u'provisioning_state': None, u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'is_online': False, u'supervisor_version': None, u'ip_address': None, u'vpn_address': None, u'name': u'floral-mountain', u'download_progress': None, u'longitude': u'', u'commit': None, u'provisioning_progress': None, u'supervisor_release': None}

        """

        params = {
            'filter': 'uuid',
            'eq': uuid
        }
        try:
            devices = self.base_request.request(
                'device', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d']
            if len(devices) > 1:
                raise exceptions.AmbiguousDevice(uuid)
            return devices[0]
        except IndexError:
            raise exceptions.DeviceNotFound(uuid)

    def get_all(self):
        """
        Get all devices.

        Returns:
            list: list contains info of devices.

        Examples:
            >>> balena.models.device.get_all()
            [{u'__metadata': {u'type': u'', u'uri': u'/ewa/device(122950)'}, u'last_connectivity_event': u'1970-01-01T00:00:00.000Z', u'is_web_accessible': False, u'device_type': u'raspberry-pi', u'id': 122950, u'logs_channel': None, u'uuid': u'8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', u'application': {u'__deferred': {u'uri': u'/ewa/application(9020)'}, u'__id': 9020}, u'note': None, u'os_version': None, u'location': u'', u'latitude': u'', u'status': None, u'public_address': u'', u'provisioning_state': None, u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'is_online': False, u'supervisor_version': None, u'ip_address': None, u'vpn_address': None, u'name': u'floral-mountain', u'download_progress': None, u'longitude': u'', u'commit': None, u'provisioning_progress': None, u'supervisor_release': None}]

        """

        return self.base_request.request(
            'device', 'GET', endpoint=self.settings.get('pine_endpoint'))['d']

    def get_all_by_application(self, name):
        """
        Get devices by application name.

        Args:
            name (str): application name.

        Returns:
            list: list contains info of devices.

        Examples:
            >>> balena.models.device.get_all_by_application('RPI1')
            [{u'__metadata': {u'type': u'', u'uri': u'/ewa/device(122950)'}, u'last_connectivity_event': u'1970-01-01T00:00:00.000Z', u'is_web_accessible': False, u'device_type': u'raspberry-pi', u'id': 122950, u'logs_channel': None, u'uuid': u'8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', u'application': {u'__deferred': {u'uri': u'/ewa/application(9020)'}, u'__id': 9020}, u'note': None, u'os_version': None, u'location': u'', u'latitude': u'', u'status': None, u'public_address': u'', u'provisioning_state': None, u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'is_online': False, u'supervisor_version': None, u'ip_address': None, u'vpn_address': None, u'name': u'floral-mountain', u'download_progress': None, u'longitude': u'', u'commit': None, u'provisioning_progress': None, u'supervisor_release': None}]

        """

        params = {
            'filter': 'app_name',
            'eq': name
        }

        app = self.base_request.request(
            'application', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

        if app:
            params = {
                'filter': 'belongs_to__application',
                'eq': app[0]['id']
            }
            return self.base_request.request(
                'device', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d']

    def get_all_by_application_id(self, appid):
        """
        Get devices by application name.

        Args:
            appid (str): application id.

        Returns:
            list: list contains info of devices.

        Examples:
            >>> balena.models.device.get_all_by_application_id(1234)
            [{u'__metadata': {u'type': u'', u'uri': u'/ewa/device(122950)'}, u'last_connectivity_event': u'1970-01-01T00:00:00.000Z', u'is_web_accessible': False, u'device_type': u'raspberry-pi', u'id': 122950, u'logs_channel': None, u'uuid': u'8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', u'application': {u'__deferred': {u'uri': u'/ewa/application(9020)'}, u'__id': 9020}, u'note': None, u'os_version': None, u'location': u'', u'latitude': u'', u'status': None, u'public_address': u'', u'provisioning_state': None, u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'is_online': False, u'supervisor_version': None, u'ip_address': None, u'vpn_address': None, u'name': u'floral-mountain', u'download_progress': None, u'longitude': u'', u'commit': None, u'provisioning_progress': None, u'supervisor_release': None}]

        """
        params = {
            'filter': 'belongs_to__application',
            'eq': appid
        }
        return self.base_request.request(
            'device', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def get_by_name(self, name):
        """
        Get devices by device name.

        Args:
            name (str): device name.

        Returns:
            list: list contains info of devices.

        Examples:
            >>> balena.models.device.get_by_name('floral-mountain')
            [{u'__metadata': {u'type': u'', u'uri': u'/ewa/device(122950)'}, u'last_connectivity_event': u'1970-01-01T00:00:00.000Z', u'is_web_accessible': False, u'device_type': u'raspberry-pi', u'id': 122950, u'logs_channel': None, u'uuid': u'8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', u'application': {u'__deferred': {u'uri': u'/ewa/application(9020)'}, u'__id': 9020}, u'note': None, u'os_version': None, u'location': u'', u'latitude': u'', u'status': None, u'public_address': u'', u'provisioning_state': None, u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'is_online': False, u'supervisor_version': None, u'ip_address': None, u'vpn_address': None, u'name': u'floral-mountain', u'download_progress': None, u'longitude': u'', u'commit': None, u'provisioning_progress': None, u'supervisor_release': None}]

        """

        params = {
            'filter': 'device_name',
            'eq': name
        }
        return self.base_request.request(
            'device', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

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

    def get_with_service_details(self, uuid, expand_release=True):
        """
        Get a single device along with its associated services' essential details.

        Args:
            uuid (str): device uuid.
            expand_release (Optional[bool]): Set this parameter to False then the commit of service details will not be included.

        Returns:
            dict: device info with associated services details.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.get_with_service_details('0fcd753af396247e035de53b4e43eec3')
            {u'os_variant': u'prod', u'__metadata': {u'type': u'', u'uri': u'/balena/device(1136312)'}, u'is_managed_by__service_instance': {u'__deferred': {u'uri': u'/balena/service_instance(182)'}, u'__id': 182}, u'should_be_running__release': None, u'belongs_to__user': {u'__deferred': {u'uri': u'/balena/user(32986)'}, u'__id': 32986}, u'is_web_accessible': False, u'device_type': u'raspberrypi3', u'belongs_to__application': {u'__deferred': {u'uri': u'/balena/application(1116729)'}, u'__id': 1116729}, u'id': 1136312, u'is_locked_until__date': None, u'logs_channel': u'1da2f8db7c5edbf268ba6c34d91974de8e910eef0033a1172386ad27807552', u'uuid': u'0fcd753af396247e035de53b4e43eec3', u'is_managed_by__device': None, u'should_be_managed_by__supervisor_release': None, u'is_accessible_by_support_until__date': None, u'actor': 2895243, u'note': None, u'os_version': u'Balena OS 2.12.7+rev1', u'longitude': u'105.85', u'last_connectivity_event': u'2018-05-27T05:43:54.027Z', u'is_on__commit': u'01defe8bbd1b5b832b32c6e1d35890317671cbb5', u'location': u'Hanoi, Thanh Pho Ha Noi, Vietnam', u'status': u'Idle', u'public_address': u'14.231.243.124', u'is_connected_to_vpn': False, u'custom_latitude': u'', u'is_active': True, u'provisioning_state': u'', u'latitude': u'21.0333', u'custom_longitude': u'', 'current_services': {u'frontend': [{u'status': u'Running', u'download_progress': None, u'__metadata': {u'type': u'', u'uri': u'/balena/image_install(8952657)'}, u'install_date': u'2018-05-25T19:00:12.989Z', 'image_id': 296863, 'commit': u'01defe8bbd1b5b832b32c6e1d35890317671cbb5', 'service_id': 52327, u'id': 8952657}], u'data': [{u'status': u'Running', u'download_progress': None, u'__metadata': {u'type': u'', u'uri': u'/balena/image_install(8952656)'}, u'install_date': u'2018-05-25T19:00:12.989Z', 'image_id': 296864, 'commit': u'01defe8bbd1b5b832b32c6e1d35890317671cbb5', 'service_id': 52329, u'id': 8952656}], u'proxy': [{u'status': u'Running', u'download_progress': None, u'__metadata': {u'type': u'', u'uri': u'/balena/image_install(8952655)'}, u'install_date': u'2018-05-25T19:00:12.985Z', 'image_id': 296862, 'commit': u'01defe8bbd1b5b832b32c6e1d35890317671cbb5', 'service_id': 52328, u'id': 8952655}]}, u'is_online': False, u'supervisor_version': u'7.4.3', u'ip_address': u'192.168.0.102', u'provisioning_progress': None, u'owns__device_log': {u'__deferred': {u'uri': u'/balena/device_log(1136312)'}, u'__id': 1136312}, u'created_at': u'2018-05-25T10:55:47.825Z', u'download_progress': None, u'last_vpn_event': u'2018-05-27T05:43:54.027Z', u'device_name': u'billowing-night', u'local_id': None, u'vpn_address': None, 'current_gateway_downloads': []}

        """

        release = ''
        if expand_release:
            release = ",is_provided_by__release($select=id,commit)"

        raw_query = "$filter=uuid%20eq%20'{uuid}'&$expand=image_install($select=id,download_progress,status,install_date&$filter=status%20ne%20'deleted'&$expand=image($select=id&$expand=is_a_build_of__service($select=id,service_name)){release}),gateway_download($select=id,download_progress,status&$filter=status%20ne%20'deleted'&$expand=image($select=id&$expand=is_a_build_of__service($select=id,service_name)))".format(uuid=uuid, release=release)

        raw_data = self.base_request.request(
            'device', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

        if len(raw_data) == 0:
            raise exceptions.DeviceNotFound(uuid)
        else:
            raw_data = raw_data[0]

        groupedServices = defaultdict(list)

        for obj in [self.__get_single_install_summary(i) for i in raw_data['image_install']]:
            groupedServices[obj.pop('service_name', None)].append(obj)

        raw_data['current_services'] = dict(groupedServices)
        raw_data['current_gateway_downloads'] = [self.__get_single_install_summary(i) for i in raw_data['gateway_download']]
        raw_data.pop('image_install', None)
        raw_data.pop('gateway_download', None)

        return raw_data

    def get_name(self, uuid):
        """
        Get device name by device uuid.

        Args:
            uuid (str): device uuid.

        Returns:
            str: device name.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        return self.get(uuid)['device_name']

    def get_application_name(self, uuid):
        """
        Get application name by device uuid.

        Args:
            uuid (str): device uuid.

        Returns:
            str: application name.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        app_id = self.get(uuid)['belongs_to__application']['__id']
        params = {
            'filter': 'id',
            'eq': app_id
        }
        return self.base_request.request(
            'application', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d'][0]['app_name']

    def has(self, uuid):
        """
        Check if a device exists.

        Args:
            uuid (str): device uuid.

        Returns:
            bool: True if device exists, False otherwise.

        """

        params = {
            'filter': 'uuid',
            'eq': uuid
        }

        return len(
            self.base_request.request(
                'device', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d']
        ) > 0

    def is_online(self, uuid):
        """
        Check if a device is online.

        Args:
            uuid (str): device uuid.

        Returns:
            bool: True if the device is online, False otherwise.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        return self.get(uuid)['is_online']

    def get_local_ip_address(self, uuid):
        """
        Get the local IP addresses of a device.

        Args:
            uuid (str): device uuid.

        Returns:
            list: IP addresses of a device.

        Raises:
            DeviceNotFound: if device couldn't be found.
            DeviceOffline: if device is offline.

        """

        if self.is_online(uuid):
            device = self.get(uuid)
            return list(set(device['ip_address'].split()))
        else:
            raise exceptions.DeviceOffline(uuid)

    def deactivate(self, uuid):
        """
        Deactivate a device.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.deactivate('44cc9d1861b9f992808c506276e5d31c')

        """

        if self.has(uuid):
            params = {
                'filter': 'uuid',
                'eq': uuid
            }

            data = {
                'is_active': False
            }

            return self.base_request.request(
                'device', 'PATCH', params=params, data=data,
                endpoint=self.settings.get('pine_endpoint')
            )
        else:
            raise exceptions.DeviceNotFound(uuid)

    def remove(self, uuid):
        """
        Remove a device. This function only works if you log in using credentials or Auth Token.

        Args:
            uuid (str): device uuid.

        """

        params = {
            'filter': 'uuid',
            'eq': uuid
        }
        return self.base_request.request(
            'device', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )

    def identify(self, uuid):
        """
        Identify device. This function only works if you log in using credentials or Auth Token.

        Args:
            uuid (str): device uuid.

        Examples:
            >>> balena.models.device.identify('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            'OK'

        """

        data = {
            'uuid': uuid
        }
        return self.base_request.request(
            'blink', 'POST', data=data,
            endpoint=self.settings.get('api_endpoint'), login=True
        )

    def rename(self, uuid, new_name):
        """
        Rename a device.

        Args:
            uuid (str): device uuid.
            new_name (str): device new name.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.rename('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', 'python-sdk-test-device')
            'OK'
            # Check device name.
            >>> balena.models.device.get_name('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            u'python-sdk-test-device'

        """

        if self.has(uuid):
            params = {
                'filter': 'uuid',
                'eq': uuid
            }
            data = {
                'device_name': new_name
            }
            return self.base_request.request(
                'device', 'PATCH', params=params, data=data,
                endpoint=self.settings.get('pine_endpoint')
            )
        else:
            raise exceptions.DeviceNotFound(uuid)

    def note(self, uuid, note):
        """
        Note a device.

        Args:
            uuid (str): device uuid.
            note (str): device note.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.note('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', 'test device')
            'OK'

        """

        if self.has(uuid):
            params = {
                'filter': 'uuid',
                'eq': uuid
            }
            data = {
                'note': note
            }
            return self.base_request.request(
                'device', 'PATCH', params=params, data=data,
                endpoint=self.settings.get('pine_endpoint')
            )
        else:
            raise exceptions.DeviceNotFound(uuid)

    def get_display_name(self, device_type_slug):
        """
        ***Deprecated***
        This method is deprecated and will be removed in next major release.
        Please use the DeviceType model instead.

        Get display name for a device.

        Args:
            device_type_slug (str): device type slug.

        Returns:
            str: device display name.

        Raises:
            InvalidDeviceType: if device type slug is not supported.

        Examples:
            >>> balena.models.device.get_display_name('intel-edison')
            u'Intel Edison'
            >>> balena.models.device.get_display_name('raspberry-pi')
            u'Raspberry Pi'

        """

        device_types = self.device_type.get_all_supported()
        display_name = [device['name'] for device in device_types
                        if device['slug'] == device_type_slug]
        if display_name:
            return display_name[0]
        else:
            raise exceptions.InvalidDeviceType(device_type_slug)

    def get_device_slug(self, device_type_name):
        """
        ***Deprecated***
        This method is deprecated and will be removed in next major release.
        Please use the DeviceType model instead.

        Get device slug.

        Args:
            device_type_name (str): device type name.

        Returns:
            str: device slug name.

        Raises:
            InvalidDeviceType: if device type name is not supported.

        Examples:
            >>> balena.models.device.get_device_slug('Intel Edison')
            u'intel-edison'
            >>> balena.models.device.get_device_slug('Raspberry Pi')
            u'raspberry-pi'

        """

        device_types = self.device_type.get_all_supported()
        slug_name = [device['slug'] for device in device_types
                     if device['name'] == device_type_name]
        if slug_name:
            return slug_name[0]
        else:
            raise exceptions.InvalidDeviceType(device_type_name)

    def get_supported_device_types(self):
        """
        ***Deprecated***
        This method is deprecated and will be removed in next major release.
        Please use the DeviceType model instead.
        
        Get device slug.

        Returns:
            list: list of supported device types.

        """

        device_types = self.device_type.get_all_supported()
        supported_device = [device['name'] for device in device_types]
        return supported_device

    def get_manifest_by_slug(self, slug):
        """
        Get a device manifest by slug.

        Args:
            slug (str): device slug name.

        Returns:
            dict: dictionary contains device manifest.

        Raises:
            InvalidDeviceType: if device slug name is not supported.

        """

        device_types = self.device_type.get_all_supported()
        manifest = [device for device in device_types
                    if device['slug'] == slug]
        if manifest:
            return manifest[0]
        else:
            raise exceptions.InvalidDeviceType(slug)

    def get_manifest_by_application(self, app_name):
        """
        Get a device manifest by application name.

        Args:
            app_name (str): application name.

        Returns:
            dict: dictionary contains device manifest.

        """

        raw_query = "$filter=app_name%20eq%20'{app_name}'&$select=id&$expand=is_for__device_type($select=slug)".format(app_name=app_name)

        application = self.base_request.request(
            'application', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

        if not application:
            raise exceptions.ApplicationNotFound(app_name)
        application = application[0]

        return self.get_manifest_by_slug(application['is_for__device_type'][0]['slug'])

    def generate_uuid(self):
        """
        Generate a random device UUID.

        Returns:
            str: a generated UUID.

        Examples:
            >>> balena.models.device.generate_uuid()
            '19dcb86aa288c66ffbd261c7bcd46117c4c25ec655107d7302aef88b99d14c'

        """

        # From balena-sdk
        # I'd be nice if the UUID matched the output of a SHA-256 function,
        # but although the length limit of the CN attribute in a X.509
        # certificate is 64 chars, a 32 byte UUID (64 chars in hex) doesn't
        # pass the certificate validation in OpenVPN This either means that
        # the RFC counts a final NULL byte as part of the CN or that the
        # OpenVPN/OpenSSL implementation has a bug.
        return binascii.hexlify(os.urandom(31))

    def register(self, app_id, uuid):
        """
        Register a new device with a balena application. This function only works if you log in using credentials or Auth Token.

        Args:
            app_id (str): application id.
            uuid (str): device uuid.

        Returns:
            dict: dictionary contains device info.

        Examples:
            >>> device_uuid = balena.models.device.generate_uuid()
            >>> balena.models.device.register('RPI1',device_uuid)
            {'id':122950,'application':{'__deferred':{'uri':'/ewa/application(9020)'},'__id':9020},'user':{'__deferred':{'uri':'/ewa/user(5397)'},'__id':5397},'name':'floral-mountain','device_type':'raspberry-pi','uuid':'8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143','commit':null,'note':null,'status':null,'is_online':false,'last_connectivity_event':'1970-01-01T00:00:00.000Z','ip_address':null,'vpn_address':null,'public_address':'','os_version':null,'supervisor_version':null,'supervisor_release':null,'provisioning_progress':null,'provisioning_state':null,'download_progress':null,'is_web_accessible':false,'longitude':'','latitude':'','location':'','logs_channel':null,'__metadata':{'uri':'/ewa/device(122950)','type':''}}

        """

        user_id = self.auth.get_user_id()

        raw_query = "$filter=id%20eq%20'{app_id}'&$select=id&$expand=is_for__device_type($select=slug)".format(app_id=app_id)

        application = self.base_request.request(
            'application', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

        if not application:
            raise exceptions.ApplicationNotFound(app_id)
        application = application[0]

        api_key = self.application.generate_provisioning_key(app_id)
        data = {
            'user': user_id,
            'application': app_id,
            'device_type': application['is_for__device_type'][0]['slug'],
            'uuid': uuid,
            'apikey': api_key
        }

        return json.loads(self.base_request.request(
            'device/register', 'POST', data=data,
            endpoint=self.settings.get('api_endpoint'), login=True
        ).decode('utf-8'))

    def restart(self, uuid):
        """
        Restart a user application container on device. This function only works if you log in using credentials or Auth Token.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.restart('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            'OK'

        """

        device = self.get(uuid)
        return self.base_request.request(
            'device/{0}/restart'.format(device['id']),
            'POST', endpoint=self.settings.get('api_endpoint'), login=True
        )

    def has_device_url(self, uuid):
        """
        Check if a device is web accessible with device urls

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.has_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            False

        """

        return self.get(uuid)['is_web_accessible']

    def get_device_url(self, uuid):
        """
        Get a device url for a device.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.get_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            'https://8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143.balenadevice.io'

        """
        if not self.has_device_url:
            raise exceptions.DeviceNotWebAccessible(uuid)

        device_url_base = self.config.get_all()['deviceUrlsBase']
        return 'https://{uuid}.{base_url}'.format(uuid=uuid, base_url=device_url_base)

    def enable_device_url(self, uuid):
        """
        Enable device url for a device.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            # Check if device url enabled.
            >>> balena.models.device.has_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            False
            # Enable device url.
            >>> balena.models.device.enable_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            'OK'
            # Check device url again.
            >>> balena.models.device.has_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            True

        """

        if not self.has(uuid):
            raise exceptions.DeviceNotFound(uuid)

        params = {
            'filter': 'uuid',
            'eq': uuid
        }
        data = {
            'is_web_accessible': True
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def disable_device_url(self, uuid):
        """
        Disable device url for a device.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.disable_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            'OK'

        """

        if not self.has(uuid):
            raise exceptions.DeviceNotFound(uuid)

        params = {
            'filter': 'uuid',
            'eq': uuid
        }
        data = {
            'is_web_accessible': False
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def move(self, uuid, app_name):
        """
        Move a device to another application.

        Args:
            uuid (str): device uuid.
            app_name (str): application name.

        Raises:
            DeviceNotFound: if device couldn't be found.
            ApplicationNotFound: if application couldn't be found.
            IncompatibleApplication: if moving a device to an application with different device-type.

        Examples:
            >>> balena.models.device.move('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', 'RPI1Test')
            'OK'

        """

        raw_query = "$filter=uuid%20eq%20'{uuid}'&$select=uuid&$expand=is_of__device_type($select=slug)".format(uuid=uuid)

        device = self.base_request.request(
            'device', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

        if not device:
            raise exceptions.DeviceNotFound(uuid)
        device = device[0]

        raw_query = "$filter=app_name%20eq%20'{app_name}'&$select=id&$expand=is_for__device_type($select=slug)".format(app_name=app_name)

        application = self.base_request.request(
            'application', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

        if not application:
            raise exceptions.ApplicationNotFound(app_name)
        application = application[0]

        all_device_types = self.device_type.get_all_supported()
        device_dev_type = list(filter(lambda dev_type: dev_type['slug'] == device['is_of__device_type'][0]['slug'], all_device_types))[0]
        app_dev_type = list(filter(lambda dev_type: dev_type['slug'] == application['is_for__device_type'][0]['slug'], all_device_types))[0]

        if not self.device_os.is_architecture_compatible_with(device_dev_type['is_of__cpu_architecture'][0]['slug'], app_dev_type['is_of__cpu_architecture'][0]['slug']):
            raise exceptions.IncompatibleApplication(app_name)

        if bool(device_dev_type.get('isDependent', None)) != bool(app_dev_type.get('isDependent', None)):
            raise exceptions.IncompatibleApplication(app_name)

        params = {
            'filter': 'uuid',
            'eq': uuid
        }
        data = {
            'belongs_to__application': application['id']
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def get_status(self, uuid):
        """
        Get the status of a device.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Returns:
            str: status of a device. List of available statuses: Idle, Configuring, Updating, Offline, Inactive and Post Provisioning.

        Examples:
            >>> balena.models.device.get_status('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            'Offline'

        """

        device = self.get_with_service_details(uuid)
        if not device['is_active']:
            return DeviceStatus.INACTIVE

        if device['provisioning_state'] == 'Post-Provisioning':
            return DeviceStatus.POST_PROVISIONING

        seen = device['last_connectivity_event'] and (datetime.strptime(device['last_connectivity_event'], "%Y-%m-%dT%H:%M:%S.%fZ")).year >= 2013
        if not device['is_online'] and not seen:
            return DeviceStatus.CONFIGURING

        if not device['is_online']:
            return DeviceStatus.OFFLINE

        if device['download_progress'] is not None and device['status'] == 'Downloading':
            return DeviceStatus.UPDATING

        if device['download_progress'] is not None:
            return DeviceStatus.CONFIGURING

        if device['current_services']:
            for service_name in device['current_services']:
                installs = device['current_services'][service_name]
                install = max(installs, key=lambda x: x['id'])
                if install and install['download_progress'] is not None and install['status'] == 'Downloading':
                    return DeviceStatus.UPDATING

        return DeviceStatus.IDLE

    def set_custom_location(self, uuid, location):
        """
        Set a custom location for a device.

        Args:
            uuid (str): device uuid.
            location (dict): device custom location, format: { 'latitude': <latitude>, 'longitude': <longitude> }.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> location = {
                'latitude': '21.032777',
                'longitude': '105.831586'
            }
            >>> balena.models.device.set_custom_location('df09262c283b1dc1462d0e82caa7a88e52588b8c5d7475dd22210edec1c50a',location)
            OK

        """

        if not self.has(uuid):
            raise exceptions.DeviceNotFound(uuid)

        params = {
            'filter': 'uuid',
            'eq': uuid
        }
        data = {
            'custom_latitude': location['latitude'],
            'custom_longitude': location['longitude']
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def unset_custom_location(self, uuid):
        """
        clear custom location for a device.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.unset_custom_location('df09262c283b1dc1462d0e82caa7a88e52588b8c5d7475dd22210edec1c50a')
            OK
        """

        return self.set_custom_location(uuid, {'latitude': '', 'longitude': ''})

    def generate_device_key(self, uuid):
        """
        Generate a device key.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> balena.models.device.generate_device_key('df09262c283b1dc1462d0e82caa7a88e52588b8c5d7475dd22210edec1c50a')
            2UrtMWeLqYXfTznZo1xNuZQXmEE6cOZk

        """

        device_id = self.get(uuid)['id']

        return self.base_request.request(
            '/api-key/device/{id}/device-key'.format(id=device_id), 'POST',
            endpoint=self.settings.get('api_endpoint')
        )

    def get_dashboard_url(self, uuid):
        """
        Get balena Dashboard URL for a specific device.

        Args:
            uuid (str): device uuid.

        Examples:
            >>> balena.models.device.get_dashboard_url('19619a6317072b65a240b451f45f855d')
            https://dashboard.balena-cloud.com/devices/19619a6317072b65a240b451f45f855d/summary

        """

        if not uuid:
            raise ValueError("Device UUID must be a non empty string")
        dashboard_url = self.settings.get('api_endpoint').replace('api', 'dashboard')
        return urljoin(
            dashboard_url,
            '/devices/{}/summary'.format(uuid)
        )

    def grant_support_access(self, uuid, expiry_timestamp):
        """
        Grant support access to a device until a specified time.

        Args:
            uuid (str): device uuid.
            expiry_timestamp (int): a timestamp in ms for when the support access will expire.

        Returns:
            OK.

        Examples:
            >> > balena.models.device.grant_support_access('49b2a76b7f188c1d6f781e67c8f34adb4a7bfd2eec3f91d40b1efb75fe413d', 1511974999000)
            'OK'

        """

        if not expiry_timestamp or expiry_timestamp <= int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000):
            raise exceptions.InvalidParameter('expiry_timestamp', expiry_timestamp)

        device_id = self.get(uuid)['id']
        params = {
            'filter': 'id',
            'eq': device_id
        }

        data = {
            'is_accessible_by_support_until__date': expiry_timestamp
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def revoke_support_access(self, uuid):
        """
        Revoke support access to a device.

        Args:
            uuid (str): device uuid.

        Returns:
            OK.

        Examples:
            >> > balena.models.device.revoke_support_access('49b2a76b7f188c1d6f781e67c8f34adb4a7bfd2eec3f91d40b1efb75fe413d')
            'OK'

        """

        device_id = self.get(uuid)['id']
        params = {
            'filter': 'id',
            'eq': device_id
        }

        data = {
            'is_accessible_by_support_until__date': None
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def set_to_release(self, uuid, commit_id):
        """
        Set device to a specific release.
        Set an empty commit_id will restore rolling releases to the device.

        Args:
            uuid (str): device uuid.
            commit_id (str) : commit id.

        Returns:
            OK.

        Examples:
            >>> balena.models.device.set_to_release('49b2a76b7f188c1d6f781e67c8f34adb4a7bfd2eec3f91d40b1efb75fe413d', '45c90004de73557ded7274d4896a6db90ea61e36')
            'OK'

        """

        device = self.get(uuid)
        query = {
            'commit': commit_id,
            'status': 'success',
            'belongs_to__application': device['belongs_to__application']['__id']
        }

        release_id = self.release._Release__get_by_option(**query)[0]['id'] if commit_id else None

        return self.set_to_release_by_id(uuid, release_id=release_id)

    def set_to_release_by_id(self, uuid, release_id=None):
        """
        Set device to a specific release by release id (please notice that release id is not the commit hash on balena dashboard).
        Remove release_id will restore rolling releases to the device.

        Args:
            uuid (str): device uuid.
            release_id (Optional[int]): release id.

        Returns:
            OK.

        Examples:
            >>> balena.models.device.set_to_release_by_id('49b2a76b7f188c1d6f781e67c8f34adb4a7bfd2eec3f91d40b1efb75fe413d', 165432)
            'OK'
            >>> balena.models.device.set_to_release_by_id('49b2a76b7f188c1d6f781e67c8f34adb4a7bfd2eec3f91d40b1efb75fe413d')
            'OK'

        """

        device_id = self.get(uuid)['id']

        params = {
            'filter': 'id',
            'eq': device_id
        }

        data = {
            'should_be_running__release': release_id
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def is_tracking_application_release(self, uuid):
        """
        Get whether the device is configured to track the current application release.

        Args:
            uuid (str): device uuid.

        Returns:
            bool: is tracking the current application release.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        return not bool(self.get(uuid)['should_be_running__release'])

    def track_application_release(self, uuid):
        """
        Configure a specific device to track the current application release.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        device_id = self.get(uuid)['id']

        params = {
            'filter': 'id',
            'eq': device_id
        }

        data = {
            'should_be_running__release': None
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def enable_lock_override(self, uuid):
        """
        Enable lock override.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        device = self.get(uuid)
        self.__upsert_device_config_variable(device, OVERRIDE_LOCK_ENV_VAR, '1')

    def disable_lock_override(self, uuid):
        """
        Disable lock override.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        device = self.get(uuid)
        self.__upsert_device_config_variable(device, OVERRIDE_LOCK_ENV_VAR, '0')

    def has_lock_override(self, uuid):
        """
        Check if a device has the lock override enabled.

        Args:
            uuid (str): device uuid.

        Returns:
            bool: lock override status.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        return self.__get_applied_device_config_variable_value(uuid, OVERRIDE_LOCK_ENV_VAR) == '1'

    def get_supervisor_state(self, uuid):
        """
        Get the supervisor state on a device

        Args:
            uuid (str): device uuid.

        Returns:
            dict: supervisor state.

        Examples:
            >>> balena.models.device.get_supervisor_state('b6070f4fea5edf808b576123157fe5ec')
            {u'status': u'Idle', u'update_failed': False, u'os_version': u'balenaOS 2.29.0+rev1', u'download_progress': None, u'update_pending': False, u'api_port': u'48484', u'commit': u'd26dd8a68a47c40daaa1d32e03c96d934f37c53b', u'update_downloaded': False, u'supervisor_version': u'9.0.1', u'ip_address': u'192.168.100.16'}

        """

        data = {
            'uuid': uuid,
            'method': 'GET'
        }

        return self.base_request.request(
            '/supervisor/v1/device', 'POST', data=data,
            endpoint=self.settings.get('api_endpoint')
        )

    def get_supervisor_target_state(self, uuid):
        """
        Get the supervisor target state on a device

        Args:
            uuid (str): device uuid.

        Returns:
            dict: supervisor target state.

        Examples:
            >>> balena.models.device.get_supervisor_target_state('b6070f4fea5edf808b576123157fe5ec')
            {u'local': {u'name': u'holy-darkness', u'config': {u'RESIN_SUPERVISOR_NATIVE_LOGGER': u'true', u'RESIN_SUPERVISOR_POLL_INTERVAL': u'900000'}, u'apps': {u'1398898': {u'name': u'test-nuc', u'commit': u'f9d139b80a7df94f90d7b9098b1353b14ca31b85', u'releaseId': 850293, u'services': {u'229592': {u'imageId': 1016025, u'serviceName': u'main', u'image': u'registry2.balena-cloud.com/v2/27aa30131b770a4f993da9a54eca6ed8@sha256:f489c30335a0036ecf1606df3150907b32ea39d73ec6de825a549385022e3e22', u'running': True, u'environment': {}, u'labels': {u'io.resin.features.dbus': u'1', u'io.resin.features.firmware': u'1', u'io.resin.features.kernel-modules': u'1', u'io.resin.features.resin-api': u'1', u'io.resin.features.supervisor-api': u'1'}, u'privileged': True, u'tty': True, u'restart': u'always', u'network_mode': u'host', u'volumes': ['resin-data:/data']}}, u'volumes': {u'resin-data': {}}, u'networks': {}}}}, u'dependent': {u'apps': {}, u'devices': {}}}

        """

        return self.base_request.request(
            '/device/v2/{0}/state'.format(uuid), 'GET',
            endpoint=self.settings.get('api_endpoint')
        )

    def __check_os_update_target(self, device_info, target_os_version):
        """
        """

        if 'uuid' not in device_info or not device_info['uuid']:
            raise exceptions.OsUpdateError('The uuid of the device is not available')

        if 'is_online' not in device_info or not device_info['is_online']:
            raise exceptions.OsUpdateError('The device is offline: {uuid}'.format(uuid=uuid))

        if 'os_version' not in device_info or not device_info['os_version']:
            raise exceptions.OsUpdateError('The current os version of the device is not available: {uuid}'.format(uuid=uuid))

        if 'is_of__device_type' not in device_info or not device_info['is_of__device_type']:
            raise exceptions.OsUpdateError('The device type of the device is not available: {uuid}'.format(uuid=uuid))

        if 'os_variant' not in device_info:
            raise exceptions.OsUpdateError('The os variant of the device is not available: {uuid}'.format(uuid=uuid))

        current_os_version = self.device_os.get_device_os_semver_with_variant(device_info['os_version'], device_info['os_variant'])
        self.hup.get_hup_action_type(device_info['is_of__device_type'][0]['slug'], current_os_version, target_os_version)

    def start_os_update(self, uuid, target_os_version):
        """
        Start an OS update on a device.

        Args:
            uuid (str): device uuid.
            target_os_version (str): semver-compatible version for the target device.
                Unsupported (unpublished) version will result in rejection.
                The version **must** be the exact version number, a "prod" variant and greater than the one running on the device.

        Returns:
            dict: action response.

        Raises:
            DeviceNotFound: if device couldn't be found.
            InvalidParameter|OsUpdateError: if target_os_version is invalid.

        Examples:
            >>> balena.models.device.start_os_update('b6070f4fea5edf808b576123157fe5ec', '2.29.2+rev1.prod')
            {u'status': u'in_progress', u'action': u'resinhup', u'parameters': {u'target_version': u'2.29.2+rev1.prod'}, u'last_run': 1554490809219L}
        """

        raw_query = "$filter=uuid%20eq%20'{uuid}'&$expand=is_of__device_type($select=slug)".format(uuid=uuid)

        device = self.base_request.request(
            'device', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

        if not device:
            raise exceptions.DeviceNotFound(uuid)
        device = device[0]

        # this will throw an error if the action is not available
        self.__check_os_update_target(device, target_os_version)

        all_versions = self.device_os.get_supported_versions(device['is_of__device_type'][0]['slug'])['versions']
        if not [v for v in all_versions if semver.compare(target_os_version, v) == 0]:
            raise exceptions.InvalidParameter('target_os_version', target_os_version)

        data = {
            'parameters': {
                'target_version': target_os_version
            }
        }

        return self.base_request.request(
            '{uuid}/{action_name}'.format(uuid=uuid, action_name=self.device_os.OS_UPDATE_ACTION_NAME),
            'POST',
            data=data,
            endpoint='https://actions.{device_url_base}/{device_actions_api_version}/'.format(
                device_url_base=self.config.get_all()['deviceUrlsBase'],
                device_actions_api_version=self.settings.get('device_actions_endpoint_version')
            )
        )

    def get_os_update_status(self, uuid):
        """
        Get the OS update status of a device.

        Args:
            uuid (str): device uuid.

        Returns:
            dict: action response.

        Examples:
            >>> balena.models.device.get_os_update_status('b6070f4fea5edf808b576123157fe5ec')
            {u'status': u'done', u'parameters': {u'target_version': u'2.29.2+rev1.prod'}, u'stdout': u'[1554490814][LOG]Normalized target version: 2.29.2+rev1\n', u'last_run': 1554491107242L, u'error': u'', u'action': u'resinhup'}
        """

        return self.base_request.request(
            '{uuid}/{action_name}'.format(uuid=uuid, action_name=self.device_os.OS_UPDATE_ACTION_NAME),
            'GET',
            endpoint='https://actions.{device_url_base}/{device_actions_api_version}/'.format(
                device_url_base=self.config.get_all()['deviceUrlsBase'],
                device_actions_api_version=self.settings.get('device_actions_endpoint_version')
            )
        )

    def __is_provisioned_device(self, device):
        return device['supervisor_version'] and device['last_connectivity_event']

    def __check_local_mode_supported(self, device):
        if not self.__is_provisioned_device(device):
            raise exceptions.LocalModeError(Message.DEVICE_NOT_PROVISIONED)

        if semver.compare(self.device_os._DeviceOs__normalize_balena_semver(device['os_version']), LOCAL_MODE_MIN_OS_VERSION) < 0:
            raise exceptions.LocalModeError(Message.DEVICE_OS_NOT_SUPPORT_LOCAL_MODE)

        if semver.compare(self.device_os._DeviceOs__normalize_balena_semver(device['supervisor_version']), LOCAL_MODE_MIN_SUPERVISOR_VERSION) < 0:
            raise exceptions.LocalModeError(Message.DEVICE_SUPERVISOR_NOT_SUPPORT_LOCAL_MODE)

        if device['os_variant'] != 'dev':
            raise exceptions.LocalModeError(Message.DEVICE_OS_TYPE_NOT_SUPPORT_LOCAL_MODE)

    def is_in_local_mode(self, uuid):
        """
        Check if local mode is enabled on the device.

        Args:
            uuid (str): device uuid.

        Returns:
            bool: True if local mode enabled, otherwise False.

        Examples:
            >>> balena.models.device.is_in_local_mode('b6070f4fea5edf808b576123157fe5ec')
            True

        """

        device = self.get(uuid)

        params = {
            'filters': {
                'device': device['id'],
                'name': LOCAL_MODE_ENV_VAR
            }
        }

        response = self.base_request.request(
            'device_config_variable', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

        if len(response) == 0:
            return False
        if response[0]['value'] == '1':
            return True
        return False

    def enable_local_mode(self, uuid):
        """
        Enable local mode.

        Args:
            uuid (str): device uuid.

        Returns:
            None.

        Examples:
            >>> balena.models.device.enable_local_mode('b6070f4fea5edf808b576123157fe5ec')

        Raises:
            LocalModeError: if local mode can't be enabled.

        """

        device = self.get(uuid)

        # this will throw an error if a device doesn't support local mode
        self.__check_local_mode_supported(device)

        self.__upsert_device_local_mode(device, LOCAL_MODE_ENV_VAR, '1')

    def disable_local_mode(self, uuid):
        """
        Disable local mode.

        Args:
            uuid (str): device uuid.

        Returns:
            None.

        Examples:
            >>> balena.models.device.disable_local_mode('b6070f4fea5edf808b576123157fe5ec')

        """

        device = self.get(uuid)
        self.__upsert_device_local_mode(device, LOCAL_MODE_ENV_VAR, '0')

    def get_local_mode_support(self, uuid):
        """
        Returns whether local mode is supported along with a message describing the reason why local mode is not supported.

        Args:
            uuid (str): device uuid.

        Returns:
            dict: local mode support information ({'supported': True/False, 'message': '...'}).

        Examples:
            >>> balena.models.device.get_local_mode_support('b6070f4fea5edf808b576123157fe5ec')
            {'message': 'Local mode is only supported on development OS versions', 'supported': False}
        """

        device = self.get(uuid)
        try:
            self.__check_local_mode_supported(device)
            return {
                'supported': True,
                'message': 'Supported'
            }
        except exceptions.LocalModeError as e:
            return {
                'supported': False,
                'message': e.message
            }

    def get_mac_address(self, uuid):
        """
        Get the MAC addresses of a device.

        Args:
            uuid (str): device uuid.

        Returns:
            list: MAC addresses of a device.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        device = self.get(uuid)
        if 'mac_address' in device:
            return device['mac_address'].split()
        else:
            return []

    def get_metrics(self, uuid):
        """
        Get the metrics related information for a device.

        Args:
            uuid (str): device uuid.

        Returns:
            dict: metrics of the device.

        Raises:
            DeviceNotFound: if device couldn't be found.

        """

        device = self.get(uuid)
        if "memory_usage" in device:
            metrics = ["memory_usage", "memory_total", "storage_block_device", "storage_usage", "storage_total", "cpu_usage", "cpu_temp", "cpu_id", "is_undervolted"]
            return {k: device.get(k, "") for k in metrics}
        else:
            return {}
