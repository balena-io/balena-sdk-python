try:  # Python 3 imports
    from urllib.parse import urljoin
except ImportError:  # Python 2 imports
    from urlparse import urljoin

from ..auth import Auth
from ..base_request import BaseRequest
from ..settings import Settings
from .config import Config
from .. import exceptions

from datetime import datetime
import json
from math import isinf
from collections import defaultdict


class Organization (object):
    """
    This class implements organization model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()
        self.auth = Auth()

    def create(self, name, handle=None):
        """
        Creates a new organization.

        Args:
            name (str): the name of the organization that will be created.
            handle (Optional[str]): The handle of the organization that will be created.

        Returns:
            dict: organization info.

        Examples:
            >>> balena.models.organization.create('My Org', 'test_org')
            '{'id': 147950, 'created_at': '2020-06-23T09:33:25.187Z', 'name': 'My Org', 'handle': 'test_org', 'billing_account_code': None, '__metadata': {'uri': '/resin/organization(@id)?@id=147950'}}'

        """

        data = {
            'name': name
        }

        if handle:
            data['handle'] = handle

        return json.loads(self.base_request.request(
            'organization', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint'), login=True
        ).decode('utf-8'))

    def get_all(self):
        """
        Get all organizations.

        Returns:
            list: list contains information of organizations.

        Examples:
            >>> balena.models.organization.get_all()
            '[{'id': 26474, 'created_at': '2018-08-14T00:24:33.144Z', 'name': 'test_account1', 'handle': 'test_account1', 'billing_account_code': None, '__metadata': {'uri': '/resin/organization(@id)?@id=26474'}}]'

        """

        return self.base_request.request(
            'organization', 'GET', endpoint=self.settings.get('pine_endpoint'), login=True
        )['d']

    def get(self, org_id):
        """
        Get a single organization by id.

        Args:
            org_id (str): organization id.

        Returns:
            dict: organization info.

        Raises:
            OrganizationNotFound: if organization couldn't be found.

        Examples:
            >>> balena.models.organization.get('26474')
            '{'id': 26474, 'created_at': '2018-08-14T00:24:33.144Z', 'name': 'test_account1', 'handle': 'test_account1', 'billing_account_code': None, '__metadata': {'uri': '/resin/organization(@id)?@id=26474'}}'

        """

        params = {
            'filter': 'id',
            'eq': org_id
        }

        org = self.base_request.request(
            'organization', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )['d']

        if not org:
            raise exceptions.OrganizationNotFound(org_id)

        return org[0]

    def get_by_handle(self, handle):
        """
        Get a single organization by handle.

        Args:
            handle (str): organization handle.

        Returns:
            dict: organization info.

        Raises:
            OrganizationNotFound: if organization couldn't be found.

        Examples:
            >>> balena.models.organization.get_by_handle('test_account1')
            ''{'id': 26474, 'created_at': '2018-08-14T00:24:33.144Z', 'name': 'test_account1', 'handle': 'test_account1', 'billing_account_code': None, '__metadata': {'uri': '/resin/organization(@id)?@id=26474'}}''

        """

        params = {
            'filter': 'handle',
            'eq': handle
        }

        org = self.base_request.request(
            'organization', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )['d']

        if not org:
            raise exceptions.OrganizationNotFound(handle)

        return org[0]

    def remove(self, org_id):
        """
        Remove an organization.

        Args:
            org_id (str): organization id.

        Returns:
            dict: organization info.

        Examples:
            >>> balena.models.organization.remove('148003')
            'OK

        """

        return self.base_request.request(
            'organization({org_id})'.format(org_id=org_id), 'DELETE',
            endpoint=self.settings.get('pine_endpoint'), login=True
        )
