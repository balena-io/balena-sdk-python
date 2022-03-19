from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions
from ..utils import is_id


class DeviceType(object):
    """
    This class implements user API key model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def get_all(self):
        """
        Get all device types.

        Returns:
            list: list contains info of device types.

        """

        return self.base_request.request(
            'device_type', 'GET',
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def get_all_supported(self):
        """
        Get all supported device types.

        Returns:
            list: list contains info of all supported device types.

        """
        
        raw_query = '$expand=is_of__cpu_architecture($select=slug)&$filter=is_default_for__application/any(idfa:idfa/is_host%20eq%20true%20and%20is_archived%20eq%20false)'

        return self.base_request.request(
            'device_type', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def get(self, id_or_slug):
        """
        Get a single device type.

        Args:
            id_or_slug (str): device type slug or alias (string) or id (number).

        """
        
        if not id_or_slug:
            raise exceptions.InvalidDeviceType(id_or_slug)

        if is_id(id_or_slug):
            # ID
            params = {
                'filter': 'id',
                'eq': id_or_slug
            }

            device_type = self.base_request.request(
                'device_type', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d']
        else:
            # Slug or alias
            
            raw_query = "$top=1&$filter=device_type_alias/any(dta:dta/is_referenced_by__alias%20eq%20'{slug}')".format(slug=id_or_slug)

            device_type = self.base_request.request(
                'device_type', 'GET', raw_query=raw_query,
                endpoint=self.settings.get('pine_endpoint')
            )['d']
    
        if not device_type:
            raise exceptions.InvalidDeviceType(id_or_slug)
        
        return device_type[0]

    def get_by_slug_or_name(self, slug_or_name):
        """
        Get a single device type by slug or name.

        Args:
            slug_or_name (str): device type slug or name.

        """
        
        raw_query = "$top=1&$filter=name%20eq%20'{slug_or_name}'%20or%20slug%20eq%20'{slug_or_name}'".format(slug_or_name=slug_or_name)

        device_type = self.base_request.request(
            'device_type', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']
    
        if not device_type:
            raise exceptions.InvalidDeviceType(slug_or_name)
        
        return device_type[0]

    def get_name(self, slug):
        """
        Get display name for a device.

        Args:
            slug (str): device type slug.

        """
        
        return self.get_by_slug_or_name(slug)['name']

    def get_slug_by_name(self, name):
        """
        Get device slug.

        Args:
            name (str): device type name.

        """
        
        return self.get_by_slug_or_name(name)['slug']
