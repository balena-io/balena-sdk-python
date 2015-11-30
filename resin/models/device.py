import sys
import binascii
import os
from datetime import datetime

from ..base_request import BaseRequest
from .config import Config
from ..settings import Settings
from ..token import Token
from .. import exceptions
from .application import Application


class Device(object):
    """
    This class implements device model for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.config = Config()
        self.settings = Settings()
        self.token = Token()
        self.application = Application()

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
            >>> resin.models.device.get('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            {u'__metadata': {u'type': u'', u'uri': u'/ewa/device(122950)'}, u'last_seen_time': u'1970-01-01T00:00:00.000Z', u'is_web_accessible': False, u'device_type': u'raspberry-pi', u'id': 122950, u'logs_channel': None, u'uuid': u'8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', u'application': {u'__deferred': {u'uri': u'/ewa/application(9020)'}, u'__id': 9020}, u'note': None, u'os_version': None, u'location': u'', u'latitude': u'', u'status': None, u'public_address': u'', u'provisioning_state': None, u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'is_online': False, u'supervisor_version': None, u'ip_address': None, u'vpn_address': None, u'name': u'floral-mountain', u'download_progress': None, u'longitude': u'', u'commit': None, u'provisioning_progress': None, u'supervisor_release': None}

        """

        params = {
            'filter': 'uuid',
            'eq': uuid
        }
        try:
            return self.base_request.request(
                'device', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d'][0]
        except IndexError:
            raise exceptions.DeviceNotFound(uuid)

    def get_all(self):
        """
        Get all devices.

        Returns:
            list: list contains info of devices.

        Examples:
            >>> resin.models.device.get_all()
            [{u'__metadata': {u'type': u'', u'uri': u'/ewa/device(122950)'}, u'last_seen_time': u'1970-01-01T00:00:00.000Z', u'is_web_accessible': False, u'device_type': u'raspberry-pi', u'id': 122950, u'logs_channel': None, u'uuid': u'8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', u'application': {u'__deferred': {u'uri': u'/ewa/application(9020)'}, u'__id': 9020}, u'note': None, u'os_version': None, u'location': u'', u'latitude': u'', u'status': None, u'public_address': u'', u'provisioning_state': None, u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'is_online': False, u'supervisor_version': None, u'ip_address': None, u'vpn_address': None, u'name': u'floral-mountain', u'download_progress': None, u'longitude': u'', u'commit': None, u'provisioning_progress': None, u'supervisor_release': None}]

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
            >>> resin.models.device.get_all_by_application('RPI1')
            [{u'__metadata': {u'type': u'', u'uri': u'/ewa/device(122950)'}, u'last_seen_time': u'1970-01-01T00:00:00.000Z', u'is_web_accessible': False, u'device_type': u'raspberry-pi', u'id': 122950, u'logs_channel': None, u'uuid': u'8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', u'application': {u'__deferred': {u'uri': u'/ewa/application(9020)'}, u'__id': 9020}, u'note': None, u'os_version': None, u'location': u'', u'latitude': u'', u'status': None, u'public_address': u'', u'provisioning_state': None, u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'is_online': False, u'supervisor_version': None, u'ip_address': None, u'vpn_address': None, u'name': u'floral-mountain', u'download_progress': None, u'longitude': u'', u'commit': None, u'provisioning_progress': None, u'supervisor_release': None}]

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
                'filter': 'application',
                'eq': app[0]['id']
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
            >>> resin.models.device.get_by_name('floral-mountain')
            [{u'__metadata': {u'type': u'', u'uri': u'/ewa/device(122950)'}, u'last_seen_time': u'1970-01-01T00:00:00.000Z', u'is_web_accessible': False, u'device_type': u'raspberry-pi', u'id': 122950, u'logs_channel': None, u'uuid': u'8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', u'application': {u'__deferred': {u'uri': u'/ewa/application(9020)'}, u'__id': 9020}, u'note': None, u'os_version': None, u'location': u'', u'latitude': u'', u'status': None, u'public_address': u'', u'provisioning_state': None, u'user': {u'__deferred': {u'uri': u'/ewa/user(5397)'}, u'__id': 5397}, u'is_online': False, u'supervisor_version': None, u'ip_address': None, u'vpn_address': None, u'name': u'floral-mountain', u'download_progress': None, u'longitude': u'', u'commit': None, u'provisioning_progress': None, u'supervisor_release': None}]

        """

        params = {
            'filter': 'name',
            'eq': name
        }
        return self.base_request.request(
            'device', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

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

        return self.get(uuid)['name']

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

        app_id = self.get(uuid)['application']['__id']
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
            )
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
            ips = device['ip_address'].split()
            ips.remove(device['vpn_address'])
            return ips
        else:
            raise exceptions.DeviceOffline(uuid)

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
            >>> resin.models.device.identify('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
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
            >>> resin.models.device.rename('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', 'python-sdk-test-device')
            'OK'
            # Check device name.
            >>> resin.models.device.get_name('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            u'python-sdk-test-device'

        """

        if self.has(uuid):
            params = {
                'filter': 'uuid',
                'eq': uuid
            }
            data = {
                'name': new_name
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
            >>> resin.models.device.note('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', 'test device')
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
        Get display name for a device.

        Args:
            device_type_slug (str): device type slug.

        Returns:
            str: device display name.

        Raises:
            InvalidDeviceType: if device type slug is not supported.

        Examples:
            >>> resin.models.device.get_display_name('intel-edison')
            u'Intel Edison'
            >>> resin.models.device.get_display_name('raspberry-pi')
            u'Raspberry Pi'

        """

        device_types = self.config.get_device_types()
        display_name = [device['name'] for device in device_types
                        if device['slug'] == device_type_slug]
        if display_name:
            return display_name[0]
        else:
            raise exceptions.InvalidDeviceType(device_type_slug)

    def get_device_slug(self, device_type_name):
        """
        Get device slug.

        Args:
            device_type_name (str): device type name.

        Returns:
            str: device slug name.

        Raises:
            InvalidDeviceType: if device type name is not supported.

        Examples:
            >>> resin.models.device.get_device_slug('Intel Edison')
            u'intel-edison'
            >>> resin.models.device.get_device_slug('Raspberry Pi')
            u'raspberry-pi'

        """

        device_types = self.config.get_device_types()
        slug_name = [device['slug'] for device in device_types
                     if device['name'] == device_type_name]
        if slug_name:
            return slug_name[0]
        else:
            raise exceptions.InvalidDeviceType(device_type_name)

    def get_supported_device_types(self):
        """
        Get device slug.

        Returns:
            list: list of supported device types.

        """

        device_types = self.config.get_device_types()
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

        device_types = self.config.get_device_types()
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

        application = self.application.get(app_name)
        return self.get_manifest_by_slug(application['device_type'])

    def generate_uuid(self):
        """
        Generate a random device UUID.

        Returns:
            str: a generated UUID.

        Examples:
            >>> resin.models.device.generate_uuid()
            '19dcb86aa288c66ffbd261c7bcd46117c4c25ec655107d7302aef88b99d14c'

        """

        # From resin-sdk
        # I'd be nice if the UUID matched the output of a SHA-256 function,
        # but although the length limit of the CN attribute in a X.509
        # certificate is 64 chars, a 32 byte UUID (64 chars in hex) doesn't
        # pass the certificate validation in OpenVPN This either means that
        # the RFC counts a final NULL byte as part of the CN or that the
        # OpenVPN/OpenSSL implementation has a bug.
        return binascii.hexlify(os.urandom(31))

    def register(self, app_name, uuid):
        """
        Register a new device with a Resin.io application. This function only works if you log in using credentials or Auth Token.

        Args:
            app_name (str): application name.
            uuid (str): device uuid.

        Returns:
            str: dictionary contains device info (can be parsed to dict).

        Examples:
            >>> device_uuid = resin.models.device.generate_uuid()
            >>> resin.models.device.register('RPI1',device_uuid)
            '{"id":122950,"application":{"__deferred":{"uri":"/ewa/application(9020)"},"__id":9020},"user":{"__deferred":{"uri":"/ewa/user(5397)"},"__id":5397},"name":"floral-mountain","device_type":"raspberry-pi","uuid":"8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143","commit":null,"note":null,"status":null,"is_online":false,"last_seen_time":"1970-01-01T00:00:00.000Z","ip_address":null,"vpn_address":null,"public_address":"","os_version":null,"supervisor_version":null,"supervisor_release":null,"provisioning_progress":null,"provisioning_state":null,"download_progress":null,"is_web_accessible":false,"longitude":"","latitude":"","location":"","logs_channel":null,"__metadata":{"uri":"/ewa/device(122950)","type":""}}'

        """

        user_id = self.token.get_user_id()
        application = self.application.get(app_name)
        api_key = self.base_request.request(
            'application/{0}/generate-api-key'.format(application['id']),
            'POST', endpoint=self.settings.get('api_endpoint'), login=True
        )

        now = (datetime.utcnow() - datetime.utcfromtimestamp(0))

        data = {
            'user': user_id,
            'application': application['id'],
            'device_type': application['device_type'],
            'registered_at': now.total_seconds(),
            'uuid': uuid
        }

        if api_key:
            data['apikey'] = api_key

        return self.base_request.request(
            'device', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )

    def restart(self, uuid):
        """
        Restart a device. This function only works if you log in using credentials or Auth Token.

        Args:
            uuid (str): device uuid.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> resin.models.device.restart('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
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
            >>> resin.models.device.has_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
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
            >>> resin.models.device.get_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            'https://8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143.resindevice.io'

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
            >>> resin.models.device.has_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            False
            # Enable device url.
            >>> resin.models.device.enable_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
            'OK'
            # Check device url again.
            >>> resin.models.device.has_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
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
            >>> resin.models.device.disable_device_url('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143')
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
            >>> resin.models.device.move('8deb12a58e3b6d3920db1c2b6303d1ff32f23d5ab99781ce1dde6876e8d143', 'RPI1Test')
            'OK'

        """

        device = self.get(uuid)
        application = self.application.get(app_name)

        if device['device_type'] != application['device_type']:
            raise exceptions.IncompatibleApplication(app_name)

        params = {
            'filter': 'uuid',
            'eq': uuid
        }
        data = {
            'application': application['id']
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )
