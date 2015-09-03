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
        Remove a device.

        Args:
            uuid (str): device uuid.

        """

        params = {
            'filter': 'uuid',
            'eq': uuid
        }
        return self.base_request.request(
            'device', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )

    def identify(self, uuid):
        """
        Identify device.

        Args:
            uuid (str): device uuid.

        """

        data = {
            'uuid': uuid
        }
        return self.base_request.request(
            '/blink', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def rename(self, uuid, new_name):
        """
        Rename a device.

        Args:
            uuid (str): device uuid.
            new_name (str): device new name.

        Raises:
            DeviceNotFound: if device couldn't be found.

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
        Register a new device with a Resin.io application.

        Args:
            app_name (str): application name.
            uuid (str): device uuid.

        Returns:
            dict: dictionary contains device info.

        """

        user_id = self.token.get_user_id()
        application = self.application.get(app_name)
        api_key = self.base_request.request(
            '/application/{0}/generate-api-key'.format(application['id']),
            'POST', endpoint=self.settings.get('pine_endpoint')
        )

        now = (datetime.utcnow() - datetime.utcfromtimestamp(0))

        data = {
            'user': user_id,
            'application': application['id'],
            'device_type': application['device_type'],
            'registered_at': now.total_seconds()
            'uuid': uuid
        }

        if api_key:
            data['apikey'] = api_key

        return self.base_request.request(
            'device', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint')
        )
