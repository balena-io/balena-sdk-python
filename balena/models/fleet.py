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

def _get_role_by_name(role_name):
    """

    Get fleet membership role
    
    Args:
        role_name (str): role name.

    Returns:
        int: fleet membership role id.

    """

    base_request = BaseRequest()
    settings = Settings()

    params = {
        'filter': 'name',
        'eq': role_name
    }

    roles = base_request.request(
        'fleet_membership_role', 'GET', params=params,
        endpoint=settings.get('pine_endpoint')
    )['d']

    if not roles:
        raise exceptions.BalenaFleetMembershipRoleNotFound(role_name=role_name)
    else:
        return roles[0]['id']


# TODO: support both fleet_id and app_name
class Fleet(object):
    """
    This class implements fleet model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()
        self.auth = Auth()
        self.release = Release()
        self.invite = FleetInvite()
        self.membership = FleetMembership()

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
        Get all fleets (including collaborator fleets).

        Returns:
            list: list contains info of fleets.

        Examples:
            >>> balena.models.fleet.get_all()

        """

        return self.base_request.request(
            'my_fleet', 'GET', endpoint=self.settings.get('pine_endpoint')
        )['d']

    def get_all_with_device_service_details(self, expand_release=False):
        """
        Get all fleets (including collaborator fleets) along with associated services' essential details.
        This method is deprecated and will be removed in next major release.

        Args:
            expand_release (Optional[bool]): Set this parameter to True then the commit of service details will be included.

        Returns:
            list: list contains info of fleets.

        """

        release = ''
        if expand_release:
            release = ",is_provided_by__release($select=id,commit)"

        raw_query = "$expand=owns__device($expand=image_install($select=id,download_progress,status,install_date&$filter=status%20ne%20'deleted'&$expand=image($select=id&$expand=is_a_build_of__service($select=id,service_name)){release}),gateway_download($select=id,download_progress,status&$filter=status%20ne%20'deleted'&$expand=image($select=id&$expand=is_a_build_of__service($select=id,service_name))))".format(release=release)

        raw_data = self.base_request.request(
            'my_fleet', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

        for app in raw_data:
            map(self.__generate_current_service_details, app['owns__device'])

        return raw_data

    def get(self, name):
        """
        Get a single fleet.

        Args:
            name (str): fleet name.

        Returns:
            dict: fleet info.

        Raises:
            FleetNotFound: if fleet couldn't be found.
            AmbiguousFleet: when more than one fleet is returned.

        Examples:
            >>> balena.models.fleet.get('foo')

        """

        params = {
            'filter': 'fleet_name',
            'eq': name
        }
        try:
            apps = self.base_request.request(
                'fleet', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d']
            if len(apps) > 1:
                raise exceptions.AmbiguousFleet(name)
            return apps[0]
        except IndexError:
            raise exceptions.FleetNotFound(name)

    def get_with_device_service_details(self, name, expand_release=False):
        """
        Get a single fleet along with its associated services' essential details.

        Args:
            name (str): fleet name.
            expand_release (Optional[bool]): Set this parameter to True then the commit of service details will be included.

        Returns:
            dict: fleet info.

        Raises:
            FleetNotFound: if fleet couldn't be found.
            AmbiguousFleet: when more than one fleet is returned.

        Examples:
            >>> balena.models.fleet.get('test-fleet')

        """

        release = ''
        if expand_release:
            release = ",is_provided_by__release($select=id,commit)"

        raw_query = "$filter=fleet_name%20eq%20'{fleet_name}'&$expand=owns__device($expand=image_install($select=id,download_progress,status,install_date&$filter=status%20ne%20'deleted'&$expand=image($select=id&$expand=is_a_build_of__service($select=id,service_name)){release}),gateway_download($select=id,download_progress,status&$filter=status%20ne%20'deleted'&$expand=image($select=id&$expand=is_a_build_of__service($select=id,service_name))))".format(fleet_name=name, release=release)

        try:
            raw_data = self.base_request.request(
                'fleet', 'GET', raw_query=raw_query,
                endpoint=self.settings.get('pine_endpoint')
            )['d']

            if raw_data and 'owns__device' in raw_data:
                map(self.__generate_current_service_details, raw_data['owns__device'])
            if len(raw_data) > 1:
                raise exceptions.AmbiguousFleet(name)
            return raw_data[0]
        except IndexError:
            raise exceptions.FleetNotFound(name)

    def get_by_owner(self, name, owner):
        """
        Get a single fleet using the fleet name and the handle of the owning organization.

        Args:
            name (str): fleet name.
            owner (str): The handle of the owning organization.

        Returns:
            dict: fleet info.

        Raises:
            FleetNotFound: if fleet couldn't be found.
            AmbiguousFleet: when more than one fleet is returned.

        Examples:
            >>> balena.models.fleet.get_by_owner('foo', 'my_org')

        """

        slug = '{owner}/{fleet_name}'.format(owner=owner.lower(), fleet_name=name.lower())

        params = {
            'filter': 'slug',
            'eq': slug
        }
        try:
            apps = self.base_request.request(
                'fleet', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d']
            if len(apps) > 1:
                raise exceptions.AmbiguousFleet(slug)
            return apps[0]
        except IndexError:
            raise exceptions.FleetNotFound(slug)

    def has(self, name):
        """
        Check if an fleet exists.

        Args:
            name (str): fleet name.

        Returns:
            bool: True if fleet exists, False otherwise.

        Examples:
            >>> balena.models.fleet.has('foo')
            True

        """

        params = {
            'filter': 'fleet_name',
            'eq': name
        }
        app = self.base_request.request(
            'fleet', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']
        return bool(app)

    def has_any(self):
        """
        Check if the user has any fleets.

        Returns:
            bool: True if user has any fleets, False otherwise.

        Examples:
            >>> balena.models.fleet.has_any()
            True

        """

        return len(self.get_all()) > 0

    def get_by_id(self, fleet_id):
        """
        Get a single fleet by fleet id.

        Args:
            fleet_id (str): fleet id.

        Returns:
            dict: fleet info.

        Raises:
            FleetNotFound: if fleet couldn't be found.

        Examples:
            >>> balena.models.fleet.get_by_id(12345)

        """

        params = {
            'filter': 'id',
            'eq': fleet_id
        }
        try:
            return self.base_request.request(
                'fleet', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint')
            )['d'][0]
        except IndexError:
            raise exceptions.FleetNotFound(fleet_id)

    def create(self, name, device_type, organization, fleet_type=None):
        """
        Create an fleet. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): fleet name.
            device_type (str): device type (display form).
            organization (str): handle or id of the organization that the fleet will belong to.
            fleet_type (Optional[str]): fleet type.

        Returns:
            dict: fleet info.

        Raises:
            InvalidDeviceType: if device type is not supported.
            InvalidFleetType: if fleet type is not supported.
            InvalidParameter: if organization is missing.
            OrganizationNotFound: if organization couldn't be found.

        Examples:
            >>> balena.models.fleet.create('foo', 'Raspberry Pi 3', 12345, 'microservices-starter')

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

            params = {
                'filter': 'slug',
                'eq': device_manifest[0]['slug']
            }

            device_type_detail = self.base_request.request(
                'device_type', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint'), login=True
            )['d'][0]
        else:
            raise exceptions.InvalidDeviceType(device_type)

        data = {
            'fleet_name': name,
            'is_for__device_type': device_type_detail['id'],
            'organization': org[0]['id']
        }

        if fleet_type:
            params = {
                'filter': 'slug',
                'eq': fleet_type
            }

            fleet_type_detail = self.base_request.request(
                'fleet_type', 'GET', params=params,
                endpoint=self.settings.get('pine_endpoint'), login=True
            )['d']

            if not fleet_type_detail:
                raise exceptions.InvalidFleetType(fleet_type)

            data['fleet_type'] = fleet_type_detail[0]['id']

        return json.loads(self.base_request.request(
            'fleet', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint'), login=True
        ).decode('utf-8'))

    def remove(self, name):
        """
        Remove fleet. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): fleet name.

        Examples:
            >>> balena.models.fleet.remove('Edison')
            'OK'

        """

        params = {
            'filter': 'fleet_name',
            'eq': name
        }
        return self.base_request.request(
            'fleet', 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )
        
    def rename(self, fleet_id, new_name):
        """
        Rename fleet. This function only works if you log in using credentials or Auth Token.

        Args:
            fleet_id (int): fleet id.
            new_name (str): new fleet name.

        Examples:
            >>> balena.models.fleet.rename(1681618, 'py-test-app')
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': fleet_id
        }
        data = {
            'fleet_name': new_name
        }

        return self.base_request.request(
            'fleet', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def restart(self, name):
        """
        Restart fleet. This function only works if you log in using credentials or Auth Token.

        Args:
            name (str): fleet name.

        Raises:
            FleetNotFound: if fleet couldn't be found.

        Examples:
            >>> balena.models.fleet.restart('RPI1')
            'OK'

        """

        fleet = self.get(name)
        return self.base_request.request(
            'fleet/{0}/restart'.format(fleet['id']), 'POST',
            endpoint=self.settings.get('api_endpoint'), login=True
        )

    def get_config(self, fleet_id, version, **options):
        """
        Download fleet config.json.

        Args:
            fleet_id (str): fleet id.
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
            dict: fleet config.json content.

        Raises:
            FleetNotFound: if fleet couldn't be found.

        """

        # Fleet not found will be raised if can't get fleet by id.
        self.get_by_id(fleet_id)

        if not version:
            raise exceptions.MissingOption('An OS version is required when calling fleet.get_config()')

        if 'network' not in options:
            options['network'] = 'ethernet'

        options['fleetId'] = fleet_id
        options['version'] = version

        return self.base_request.request(
            '/download-config', 'POST', data=options,
            endpoint=self.settings.get('api_endpoint')
        )

    def enable_rolling_updates(self, fleet_id):
        """
        Enable Rolling update on fleet.

        Args:
            fleet_id (str): fleet id.

        Returns:
            OK/error.

        Raises:
            FleetNotFound: if fleet couldn't be found.

        Examples:
            >> > balena.models.fleet.enable_rolling_updates('106640')
            'OK'
        """

        params = {
            'filter': 'id',
            'eq': fleet_id
        }
        data = {
            'should_track_latest_release': True
        }

        return self.base_request.request(
            'fleet', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def disable_rolling_updates(self, fleet_id):
        """
        Disable Rolling update on fleet.

        Args:
            fleet_id (str): fleet id.

        Returns:
            OK/error.

        Raises:
            FleetNotFound: if fleet couldn't be found.

        Examples:
            >> > balena.models.fleet.disable_rolling_updates('106640')
            'OK'
        """

        params = {
            'filter': 'id',
            'eq': fleet_id
        }
        data = {
            'should_track_latest_release': False
        }

        return self.base_request.request(
            'fleet', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def enable_device_urls(self, fleet_id):
        """
        Enable device urls for all devices that belong to an fleet

        Args:
            fleet_id (str): fleet id.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.fleet.enable_device_urls('5685')
            'OK'

        """

        params = {
            'filter': 'belongs_to__fleet',
            'eq': fleet_id
        }
        data = {
            'is_web_accessible': True
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def disable_device_urls(self, fleet_id):
        """
        Disable device urls for all devices that belong to an fleet.

        Args:
            fleet_id (str): fleet id.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.fleet.disable_device_urls('5685')
            'OK'

        """

        params = {
            'filter': 'belongs_to__fleet',
            'eq': fleet_id
        }
        data = {
            'is_web_accessible': False
        }

        return self.base_request.request(
            'device', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def grant_support_access(self, fleet_id, expiry_timestamp):
        """
        Grant support access to an fleet until a specified time.

        Args:
            fleet_id (str): fleet id.
            expiry_timestamp (int): a timestamp in ms for when the support access will expire.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.fleet.grant_support_access('5685', 1511974999000)
            'OK'

        """

        if not expiry_timestamp or expiry_timestamp <= int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000):
            raise exceptions.InvalidParameter('expiry_timestamp', expiry_timestamp)

        params = {
            'filter': 'id',
            'eq': fleet_id
        }

        data = {
            'is_accessible_by_support_until__date': expiry_timestamp
        }

        return self.base_request.request(
            'fleet', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def revoke_support_access(self, fleet_id):
        """
        Revoke support access to an fleet.

        Args:
            fleet_id (str): fleet id.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.fleet.revoke_support_access('5685')
            'OK'

        """

        params = {
            'filter': 'id',
            'eq': fleet_id
        }

        data = {
            'is_accessible_by_support_until__date': None
        }

        return self.base_request.request(
            'fleet', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def generate_provisioning_key(self, fleet_id):
        """
        Generate a device provisioning key for a specific fleet.

        Args:
            fleet_id (str): fleet id.

        Returns:
            str: device provisioning key.

        Examples:
            >> > balena.models.fleet.generate_provisioning_key('5685')
            'GThZJps91PoJCdzfYqF7glHXzBDGrkr9'

        """

        # Make sure user has access to the fleet_id
        self.get_by_id(fleet_id)

        return self.base_request.request(
            '/api-key/fleet/{}/provisioning'.format(fleet_id),
            'POST',
            endpoint=self.settings.get('api_endpoint')
        )

    def set_to_release(self, fleet_id, full_release_hash):
        """
        Set an fleet to a specific commit.

        Args:
            fleet_id (str): fleet id.
            full_release_hash (str) : full_release_hash.

        Returns:
            OK/error.

        Examples:
            >> > balena.models.fleet.set_to_release('5685', '7dba4e0c461215374edad74a5b78f470b894b5b7')
            'OK'

        """

        raw_query = "$filter=startswith(commit, '{release_hash}')&$top=1&select=id&filter=belongs_to__fleet%20eq%20'{fleet_id}'%20and%20status%20eq%20'success'".format(
            release_hash=full_release_hash,
            fleet_id=fleet_id
        )

        try:
            release = self.release._Release__get_by_raw_query(raw_query)[0]
        except exceptions.ReleaseNotFound:
            raise exceptions.ReleaseNotFound(full_release_hash)

        params = {
            'filter': 'id',
            'eq': fleet_id
        }

        data = {
            'should_be_running__release': release['id'],
            'should_track_latest_release': False
        }

        return self.base_request.request(
            'fleet', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def will_track_new_releases(self, fleet_id):
        """
        Get whether the fleet is configured to receive updates whenever a new release is available.

        Args:
            fleet_id (str): fleet id.

        Returns:
            bool: is tracking the latest release.

        Examples:
            >> > balena.models.fleet.will_track_new_releases('5685')
            True

        """

        return bool(self.get_by_id(fleet_id)['should_track_latest_release'])

    def is_tracking_latest_release(self, fleet_id):
        """
        Get whether the fleet is up to date and is tracking the latest release for updates.

        Args:
            fleet_id (str): fleet id.

        Returns:
            bool: is tracking the latest release.

        Examples:
            >> > balena.models.fleet.is_tracking_latest_release('5685')
            True

        """

        raw_query = "$filter=id%20eq%20'{fleet_id}'&$select=should_track_latest_release&$expand=should_be_running__release($select=id),owns__release($select=id&$top=1&$filter=status%20eq%20'success'&$orderby=created_at%20desc)".format(fleet_id=fleet_id)

        fleet = self.base_request.request(
            'fleet', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )['d']

        if not fleet:
            raise exceptions.FleetNotFound(fleet_id)

        fleet = fleet[0]

        latest_release = None
        if fleet['owns__release']:
            latest_release = fleet['owns__release'][0]

        tracked_release = None
        if fleet['should_be_running__release']:
            tracked_release = fleet['should_be_running__release'][0]

        return bool(fleet['should_track_latest_release']) and (not latest_release or (tracked_release and tracked_release['id'] == latest_release['id']))

    def get_target_release_hash(self, fleet_id):
        """
        Get the hash of the current release for a specific fleet.

        Args:
            fleet_id (str): fleet id.

        Returns:
            str: The release hash of the current release.

        Examples:
            >>> balena.models.fleet.get_target_release_hash('5685')

        """

        raw_query = "$filter=id%20eq%20'{fleet_id}'&$select=id&$expand=should_be_running__release($select=commit)".format(fleet_id=fleet_id)

        fleet = self.base_request.request(
            'fleet', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )['d']

        if not fleet:
            raise exceptions.FleetNotFound(fleet_id)

        fleet = fleet[0]

        if fleet['should_be_running__release']:
            return fleet['should_be_running__release'][0]['commit']

        return ''

    def track_latest_release(self, fleet_id):
        """
        Configure a specific fleet to track the latest available release.

        Args:
            fleet_id (str): fleet id.

        Examples:
            >>> balena.models.fleet.track_latest_release('5685')

        """

        latest_release = None

        try:
            latest_release = self.release.get_latest_by_fleet(fleet_id)
        except exceptions.ReleaseNotFound:
            pass

        params = {
            'filter': 'id',
            'eq': fleet_id
        }

        data = {
            'should_track_latest_release': True
        }

        if latest_release:
            data['should_be_running__release'] = latest_release['id']

        return self.base_request.request(
            'fleet', 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def get_dashboard_url(self, fleet_id):
        """
        Get Dashboard URL for a specific fleet.

        Args:
            fleet_id (str): fleet id.

        Raises:
            InvalidParameter: if the fleet_id is not a finite number.

        Returns:
            str: Dashboard URL for the specific fleet.

        Examples:
            >>> balena.models.fleet.get_dashboard_url('1476418')
            https://dashboard.balena-cloud.com/apps/1476418

        """
        try:
            if isinf(int(fleet_id)):
                raise exceptions.InvalidParameter('fleet_id', fleet_id)
        except ValueError:
            raise exceptions.InvalidParameter('fleet_id', fleet_id)

        return urljoin(
            self.settings.get('api_endpoint').replace('api', 'dashboard'),
            '/fleets/{fleet_id}'.format(fleet_id=fleet_id)
        )


class FleetInvite():
    """
    This class implements fleet invite model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()
        self.auth = Auth()
        self.release = Release()
        self.RESOURCE = 'invitee__is_invited_to__fleet'

    def get_all(self):
        """
        Get all invites.

        Returns:
            list: list contains info of invites.
            
        Examples:
            >>> balena.models.fleet.invite.get_all()

        """

        return self.base_request.request(
            self.RESOURCE, 'GET', endpoint=self.settings.get('pine_endpoint')
        )['d']
        
    def get_all_by_fleet(self, fleet_id):
        """
        Get all invites by fleet.

        Args:
            fleet_id (int): fleet id.

        Returns:
            list: list contains info of invites.
            
        Examples:
            >>> balena.models.fleet.invite.get_all_by_fleet(1681618)

        """

        params = {
            'filter': 'is_invited_to__fleet',
            'eq': fleet_id
        }

        return self.base_request.request(
            self.RESOURCE, 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']
        
    def create(self, fleet_id, invitee, role_name=None, message=None):
        """
        Creates a new invite for an fleet.

        Args:
            fleet_id (int): fleet id.
            invitee (str): the email of the invitee.
            role_name (Optional[str]): the role name to be granted to the invitee.
            message (Optional[str]): the message to send along with the invite.

        Returns:
            dict: fleet invite.

        Examples:
            >>> balena.models.fleet.invite.create(1681618, 'james@resin.io', 'developer', 'Test invite')

        """
        
        data = {
            'invitee': invitee,
            'is_invited_to__fleet': fleet_id,
            'message': message
        }

        if role_name:
            data['fleet_membership_role '] = _get_role_by_name(role_name)
        
        return json.loads(self.base_request.request(
            self.RESOURCE, 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint'), login=True
        ).decode('utf-8'))
        
    def revoke(self, invite_id):
        """
        Revoke an invite.

        Args:
            invite_id (int): fleet invite id.

        Examples:
            >>> balena.models.fleet.invite.revoke(5860)
            'OK'

        """
        
        params = {
            'filter': 'id',
            'eq': invite_id
        }

        return self.base_request.request(
            self.RESOURCE, 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )
        
    def accept(self, invite_token):
        """
        Accepts an invite.

        Args:
            invite_token (str): invitationToken - invite token.

        """
        
        return self.base_request.request(
            '/user/v1/invitation/{0}'.format(invite_token), 'POST',
            endpoint=self.settings.get('api_endpoint'), login=True
        )


class FleetMembership():
    """
    This class implements fleet membership model for balena python SDK.
    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()
        self.auth = Auth()
        self.RESOURCE = 'user__is_member_of__fleet'

    def get_all(self):
        """
        Get all fleet memberships.

        Returns:
            list: list contains info of fleet memberships.
            
        Examples:
            >>> balena.models.fleet.membership.get_all()

        """

        return self.base_request.request(
            self.RESOURCE, 'GET', endpoint=self.settings.get('pine_endpoint')
        )['d']

    def get(self, membership_id):
        """
        Get a single fleet membership.

        Args:
            membership_id (int): fleet membership id.

        Returns:
            dict: fleet membership.
            
        Examples:
            >>> balena.models.fleet.membership.get(55074)

        """

        params = {
            'filter': 'id',
            'eq': membership_id
        }

        result = self.base_request.request(
            self.RESOURCE, 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']
        
        if not result:
            raise exceptions.FleetMembershipNotFound(membership_id)

        return result[0]

    def get_all_by_fleet(self, fleet_id):
        """
        Get all memberships by fleet.

        Args:
            fleet_id (int): fleet id.

        Returns:
            list: list contains info of fleet memberships.
            
        Examples:
            >>> balena.models.fleet.membership.get_all_by_fleet(1681618)

        """

        params = {
            'filter': 'is_member_of__fleet',
            'eq': fleet_id
        }

        return self.base_request.request(
            self.RESOURCE, 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def create(self, fleet_id, user_name, role_name=None):
        """
        Creates a new membership for an fleet.

        Args:
            fleet_id (int): fleet id.
            user_name (str): the username of the balena user that will become a member.
            role_name (Optional[str]): the role name to be granted to the membership.

        Returns:
            dict: fleet invite.

        Examples:
            >>> balena.models.fleet.membership.create(1681618, 'nghiant2710')

        """
        
        data = {
            'username': user_name,
            'is_member_of__fleet': fleet_id
        }

        if role_name:
            data['fleet_membership_role '] = _get_role_by_name(role_name)

        return json.loads(self.base_request.request(
            self.RESOURCE, 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint'), login=True
        ).decode('utf-8'))

    def change_role(self, membership_id, role_name):
        """
        Changes the role of an fleet member.

        Args:
            membership_id (int): the id of the membership that will be changed.
            role_name (str): the role name to be granted to the membership.

        Examples:
            >>> balena.models.fleet.membership.change_role(55074, 'observer')
            'OK'

        """

        role_id = _get_role_by_name(role_name)

        params = {
            'filter': 'id',
            'eq': membership_id
        }

        data = {
            'fleet_membership_role': role_id
        }

        return self.base_request.request(
            self.RESOURCE, 'PATCH', params=params, data=data,
            endpoint=self.settings.get('pine_endpoint')
        )

    def remove(self, membership_id):
        """
        Remove a membership.

        Args:
            membership_id (int): fleet membership id.

        """
        
        params = {
            'filter': 'id',
            'eq': membership_id
        }

        return self.base_request.request(
            self.RESOURCE, 'DELETE', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )
