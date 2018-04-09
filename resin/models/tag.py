import json

from ..base_request import BaseRequest
from .device import Device
from ..settings import Settings
from .. import exceptions


class Tag(object):
    """
    This class is a wrapper for Tag models.

    """

    def __init__(self):
        self.device = DeviceTag()


class BaseTag(object):
    """
    an abstract implementation for resource tags. This class won't be included in the docs.

    """

    def __init__(self, resource):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.resource = resource

    def get_all(self, params=None, data=None, raw_query=None):
        if raw_query:
            return self.base_request.request(
                '{}_tag'.format(self.resource), 'GET', raw_query=raw_query,
                endpoint=self.settings.get('pine_endpoint')
            )['d']
        else:
            return self.base_request.request(
                '{}_tag'.format(self.resource), 'GET', params=params, data=data,
                endpoint=self.settings.get('pine_endpoint')
            )['d']

    def get(self, resource_id, tag_key):
        params = {
            'filters': {
                self.resource: resource_id,
                'tag_key': tag_key
            }
        }

        return self.base_request.request(
            '{}_tag'.format(self.resource), 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def set(self, resource_id, tag_key, value):
        if len(self.get(resource_id,tag_key)) > 0:
            params = {
                'filters': {
                    self.resource: resource_id,
                    'tag_key': tag_key
                }
            }

            data = {
                'value': value
            }

            return self.base_request.request(
                '{}_tag'.format(self.resource), 'PATCH', params=params, data=data,
                endpoint=self.settings.get('pine_endpoint')
            )
        else:
            data = {
                self.resource: resource_id,
                'tag_key': tag_key,
                'value': value
            }

            return json.loads(self.base_request.request(
                '{}_tag'.format(self.resource), 'POST', data=data,
                endpoint=self.settings.get('pine_endpoint')
            ).decode('utf-8'))

    def remove(self, resource_id, tag_key):
        params = {
                'filters': {
                    self.resource: resource_id,
                    'tag_key': tag_key
            }
        }

        return self.base_request.request(
                '{}_tag'.format(self.resource), 'DELETE', params=params,
                endpoint=self.settings.get('pine_endpoint')
        )


class DeviceTag(BaseTag):
    """
    This class implements device tag model for Resin Python SDK.

    """

    def __init__(self):
        super(DeviceTag, self).__init__('device')
        self.device = Device()

    def get_all_by_application(self, app_id):
        """
        Get all device tags for an application.

        Args:
            app_id (str): application id .

        Returns:
            list: list contains device tags.

        Examples:
            >>> resin.models.tag.device.get_all_by_application('1005160')
            [{u'device': {u'__deferred': {u'uri': u'/resin/device(1055117)'}, u'__id': 1055117}, u'tag_key': u'group1', u'id': 20158, u'value': u'aaa', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20158)'}}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1055116)'}, u'__id': 1055116}, u'tag_key': u'group1', u'id': 20159, u'value': u'bbb', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20159)'}}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1055116)'}, u'__id': 1055116}, u'tag_key': u'db_tag', u'id': 20160, u'value': u'aaa', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20160)'}}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1036574)'}, u'__id': 1036574}, u'tag_key': u'db_tag', u'id': 20157, u'value': u'rpi3', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20157)'}}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1036574)'}, u'__id': 1036574}, u'tag_key': u'newtag', u'id': 20161, u'value': u'test1', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20161)'}}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1036574)'}, u'__id': 1036574}, u'tag_key': u'newtag1', u'id': 20162, u'value': u'test1', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20162)'}}]


        """

        query = '$filter=device/any(d:d/belongs_to__application%20eq%20{app_id})'.format(app_id=app_id)

        return super(DeviceTag, self).get_all(raw_query=query)

    def get_all_by_device(self, uuid):
        """
        Get all device tags for a device.

        Args:
            uuid (str): device uuid.

        Returns:
            list: list contains device tags.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> resin.models.tag.device.get_all_by_device('a03ab646c01f39e39a1e3deb7fce76b93075c6d599fd5be4a889b8145e2f8f')
            [{u'device': {u'__deferred': {u'uri': u'/resin/device(1055116)'}, u'__id': 1055116}, u'tag_key': u'group1', u'id': 20159, u'value': u'bbb', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20159)'}}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1055116)'}, u'__id': 1055116}, u'tag_key': u'db_tag', u'id': 20160, u'value': u'aaa', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20160)'}}]

        """

        device = self.device.get(uuid)

        params = {
            'filter': 'device',
            'eq': device['id']
        }

        return super(DeviceTag, self).get_all(params=params)

    def get_all(self):
        """
        Get all device tags.

        Returns:
            list: list contains device tags.

        Examples:
            >>> resin.models.tag.device.get_all()
            [{u'device': {u'__deferred': {u'uri': u'/resin/device(1036574)'}, u'__id': 1036574}, u'tag_key': u'db_tag', u'id': 20157, u'value': u'rpi3', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20157)'}}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1055117)'}, u'__id': 1055117}, u'tag_key': u'group1', u'id': 20158, u'value': u'aaa', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20158)'}}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1055116)'}, u'__id': 1055116}, u'tag_key': u'group1', u'id': 20159, u'value': u'bbb', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20159)'}}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1055116)'}, u'__id': 1055116}, u'tag_key': u'db_tag', u'id': 20160, u'value': u'aaa', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20160)'}}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1036574)'}, u'__id': 1036574}, u'tag_key': u'newtag', u'id': 20161, u'value': u'test1', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20161)'}}, {u'device': {u'__deferred': {u'uri': u'/resin/device(1036574)'}, u'__id': 1036574}, u'tag_key': u'newtag1', u'id': 20162, u'value': u'test1', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20162)'}}]

        """

        return super(DeviceTag, self).get_all()

    def set(self, uuid, tag_key, value):
        """
        Set a device tag (update tag value if it exists).

        Args:
            uuid (str): device uuid.
            tag_key (str): tag key.
            value (str): tag value.

        Returns:
            dict: dict contains device tag info if tag doesn't exist.
            OK: if tag exists.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> resin.models.tag.device.set('f5213eac0d63ac47721b037a7406d306', 'testtag','test1')
            {u'device': {u'__deferred': {u'uri': u'/resin/device(1036574)'}, u'__id': 1036574}, u'tag_key': u'testtag', u'id': 20163, u'value': u'test1', u'__metadata': {u'type': u'', u'uri': u'/resin/device_tag(20163)'}}
            >>> resin.models.tag.device.set('f5213eac0d63ac47721b037a7406d306', 'testtag','test2'))
            OK

        """

        device = self.device.get(uuid)

        return super(DeviceTag, self).set(device['id'], tag_key, value)

    def remove(self, uuid, tag_key):
        """
        Remove a device tag.

        Args:
            uuid (str): device uuid.
            tag_key (str): tag key.

        Raises:
            DeviceNotFound: if device couldn't be found.

        Examples:
            >>> resin.models.tag.device.remove('f5213eac0d63ac47721b037a7406d306', 'testtag'))
            OK

        """

        device = self.device.get(uuid)

        return super(DeviceTag, self).remove(device['id'], tag_key)
