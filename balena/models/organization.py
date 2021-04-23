try:  # Python 3 imports
    from urllib.parse import urljoin
except ImportError:  # Python 2 imports
    from urlparse import urljoin

from ..auth import Auth
from ..base_request import BaseRequest
from ..settings import Settings
from .config import Config
from ..utils import is_id
from .tag import BaseTag
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
        self.membership = OrganizationMembership()

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


class OrganizationMembership (object):
    """
    This class implements organization membership model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()
        self.auth = Auth()
        self.tag = OrganizationMembershipTag()

    def get_all(self):
        """
        Get all organization memberships.

        Returns:
            list: organization memberships.

        Examples:
            >>> balena.models.organization.membership.get_all()
            '[{'id': 17608, 'created_at': '2017-08-03T11:16:03.022Z', 'user': {'__id': 22294, '__deferred': {'uri': '/resin/user(@id)?@id=22294'}}, 'is_member_of__organization': {'__id': 3014, '__deferred': {'uri': '/resin/organization(@id)?@id=3014'}}, 'organization_membership_role': {'__id': 3, '__deferred': {'uri': '/resin/organization_membership_role(@id)?@id=3'}}, '__metadata': {'uri': '/resin/organization_membership(@id)?@id=17608'}}]'

        """

        return self.base_request.request(
            'organization_membership', 'GET', endpoint=self.settings.get('pine_endpoint'), login=True
        )['d']

    def get_all_by_organization(self, handle_or_id):
        """
        Get all memberships by organization.

        Args:
            handle_or_id (str): organization handle (string) or id (number).

        Returns:
            list: organization memberships.

        Raises:
            OrganizationNotFound: if organization couldn't be found.

        Examples:
            >>> balena.models.organization.membership.get_all_by_organization(3014)
            '[{'id': 17608, 'created_at': '2017-08-03T11:16:03.022Z', 'user': {'__id': 22294, '__deferred': {'uri': '/resin/user(@id)?@id=22294'}}, 'is_member_of__organization': {'__id': 3014, '__deferred': {'uri': '/resin/organization(@id)?@id=3014'}}, 'organization_membership_role': {'__id': 3, '__deferred': {'uri': '/resin/organization_membership_role(@id)?@id=3'}}, '__metadata': {'uri': '/resin/organization_membership(@id)?@id=17608'}}]'

        """

        params = {
            'filter': 'is_member_of__organization',
            'eq': handle_or_id
        }

        if not is_id(handle_or_id):
            params1 = {
                'filter': 'handle',
                'eq': handle_or_id
            }

            org = self.base_request.request(
                'organization', 'GET', params=params1,
                endpoint=self.settings.get('pine_endpoint'), login=True
            )['d']

            if not org:
                raise exceptions.OrganizationNotFound(handle_or_id)

            params['eq'] = org['id']

        return self.base_request.request(
            'organization_membership', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )['d']

    def get(self, membership_id):
        """
        Get a single organization membership.

        Args:
            membership_id (str): membership id.

        Returns:
            Organization membership.

        Raises:
            OrganizationNotFound: if organization couldn't be found.

        Examples:
            >>> balena.models.organization.membership.get(17608)
            '[{'id': 17608, 'created_at': '2017-08-03T11:16:03.022Z', 'user': {'__id': 22294, '__deferred': {'uri': '/resin/user(@id)?@id=22294'}}, 'is_member_of__organization': {'__id': 3014, '__deferred': {'uri': '/resin/organization(@id)?@id=3014'}}, 'organization_membership_role': {'__id': 3, '__deferred': {'uri': '/resin/organization_membership_role(@id)?@id=3'}}, '__metadata': {'uri': '/resin/organization_membership(@id)?@id=17608'}}]'

        """

        params = {
            'filter': 'id',
            'eq': membership_id
        }

        org_membership = self.base_request.request(
            'organization_membership', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )['d']

        if len(org_membership) > 0:
            return org_membership[0]
        else:
            raise exceptions.OrganizationMembershipNotFound(membership_id)


class OrganizationMembershipTag(BaseTag):
    """
    This class implements organization membership tag model for balena python SDK.

    """

    def __init__(self):
        super(OrganizationMembershipTag, self).__init__('organization_membership')

    def get_all_by_organization(self, handle_or_id):
        """
        Get all organization membership tags for an organization.

        Args:
            handle_or_id (str): organization handle (string) or id (number).

        Returns:
            list: organization membership tags.

        Raises:
            OrganizationNotFound: if organization couldn't be found.

        Examples:
            >>> balena.models.organization.membership.tag.get_all_by_organization(3014)
            [{'id': 991, 'organization_membership': {'__id': 17608, '__deferred': {'uri': '/resin/organization_membership(@id)?@id=17608'}}, 'tag_key': 'mTag1', 'value': 'Python SDK 1', '__metadata': {'uri': '/resin/organization_membership_tag(@id)?@id=991'}}]

        """

        org_id = handle_or_id

        if not is_id(handle_or_id):
            params1 = {
                'filter': 'handle',
                'eq': handle_or_id
            }

            org = self.base_request.request(
                'organization', 'GET', params=params1,
                endpoint=self.settings.get('pine_endpoint'), login=True
            )['d']

            if not org:
                raise exceptions.OrganizationNotFound(handle_or_id)

            org_id = org['id']

        query = '$filter=organization_membership/any(d:d/is_member_of__organization%20eq%20{org_id})'.format(org_id=org_id)

        return super(OrganizationMembershipTag, self).get_all(raw_query=query)

    def get_all_by_organization_membership(self, membership_id):
        """
        Get all organization membership tags for all memberships of an organization.

        Args:
            membership_id (str): organization membership id.

        Returns:
            list: organization membership tags.

        Examples:
            >>> balena.models.organization.membership.tag.get_all_by_organization_membership(17608)
            [{'id': 991, 'organization_membership': {'__id': 17608, '__deferred': {'uri': '/resin/organization_membership(@id)?@id=17608'}}, 'tag_key': 'mTag1', 'value': 'Python SDK 1', '__metadata': {'uri': '/resin/organization_membership_tag(@id)?@id=991'}}]

        """

        params = {
            'filter': 'organization_membership',
            'eq': membership_id
        }

        return super(OrganizationMembershipTag, self).get_all(params=params)

    def get_all(self):
        """
        Get all organization membership tags.

        Returns:
            list: organization membership tags.

        Examples:
            >>> balena.models.organization.membership.tag.get_all()
            [{'id': 991, 'organization_membership': {'__id': 17608, '__deferred': {'uri': '/resin/organization_membership(@id)?@id=17608'}}, 'tag_key': 'mTag1', 'value': 'Python SDK 1', '__metadata': {'uri': '/resin/organization_membership_tag(@id)?@id=991'}}]

        """

        return super(OrganizationMembershipTag, self).get_all()

    def set(self, membership_id, tag_key, value):
        """
        Set an organization membership tag.

        Args:
            membership_id: organization membership id.
            tag_key (str): tag key.
            value (str): tag value.

        Returns:
            dict: dict contains organization membership tag info if tag doesn't exist.
            OK: if tag exists.

        Examples:
            >>> balena.models.organization.membership.tag.set(17608, 'mTag1', 'Python SDK')
            {'id': 991, 'organization_membership': {'__id': 17608, '__deferred': {'uri': '/resin/organization_membership(@id)?@id=17608'}}, 'tag_key': 'mTag1', 'value': 'Python SDK', '__metadata': {'uri': '/resin/organization_membership_tag(@id)?@id=991'}}
            >>> balena.models.organization.membership.tag.set(17608, 'mTag1', 'Python SDK 1')
            'OK'

        """

        return super(OrganizationMembershipTag, self).set(membership_id, tag_key, value)

    def remove(self, membership_id, tag_key):
        """
        Remove an organization membership tag.

        Args:
            membership_id: organization membership id.
            tag_key (str): tag key.

        Examples:
            >>> balena.models.organization.membership.tag.remove(17608, 'mTag1')
            'OK'

        """

        return super(OrganizationMembershipTag, self).remove(membership_id, tag_key)
