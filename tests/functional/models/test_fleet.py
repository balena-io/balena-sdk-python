import unittest
import json
from datetime import datetime

from tests.helper import TestHelper


class TestFleet(unittest.TestCase):

    helper = None
    balena = None

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena

    def tearDown(self):
        # Wipe all fleets after every test case.
        self.helper.wipe_fleet()

    def test_create(self):
        # should be rejected if the device type is invalid
        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.fleet.create('FooBar', 'Foo', self.helper.default_organization['id'])

        # should be rejected if the name has less than four characters
        with self.assertRaises(Exception) as cm:
            self.balena.models.fleet.create('Fo', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertIn('It is necessary that each fleet has an fleet name that has a Length (Type) that is greater than or equal to 4 and is less than or equal to 100', cm.exception.message)

        # should be able to create an fleet
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertEqual(fleet['fleet_name'], 'FooBar')

        # should be rejected if the fleet type is invalid
        with self.assertRaises(self.helper.balena_exceptions.InvalidFleetType):
            self.balena.models.fleet.create('FooBar1', 'Raspberry Pi 3', self.helper.default_organization['id'], 'microservices-starterrrrrr')

        # should be able to create an fleet with a specific fleet type
        fleet = self.balena.models.fleet.create('FooBar1', 'Raspberry Pi 3', self.helper.default_organization['id'], 'microservices-starter')
        self.assertEqual(fleet['fleet_name'], 'FooBar1')

    def test_get_all(self):
        # given no fleets, it should return empty list.
        self.assertEqual(self.balena.models.fleet.get_all(), [])

        # given there is an fleet, it should return a list with length 2.
        self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.balena.models.fleet.create('FooBar1', 'Raspberry Pi 2', self.helper.default_organization['id'])
        all_fleets = self.balena.models.fleet.get_all()
        self.assertEqual(len(all_fleets), 2)
        self.assertNotEqual(all_fleets[0]['fleet_name'], all_fleets[1]['fleet_name'])

    def test_get(self):
        # raise balena.exceptions.FleetNotFound if no fleet found.
        with self.assertRaises(self.helper.balena_exceptions.FleetNotFound):
            self.balena.models.fleet.get('FleetNotExist')

        # found an fleet, it should return an fleet with matched name.
        self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertEqual(self.balena.models.fleet.get('FooBar')['fleet_name'], 'FooBar')

    def test_get_by_owner(self):
        # raise balena.exceptions.FleetNotFound if no fleet found.
        with self.assertRaises(self.helper.balena_exceptions.FleetNotFound):
            self.balena.models.fleet.get_by_owner('FleetNotExist', self.helper.credentials['user_id'])

        # found an fleet, it should return an fleet with matched name.
        self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertEqual(self.balena.models.fleet.get_by_owner('FooBar', self.helper.default_organization['handle'])['fleet_name'], 'FooBar')

        # should not find the created fleet with a different username
        with self.assertRaises(Exception) as cm:
            self.balena.models.fleet.get_by_owner('FooBar', 'random_username')
        self.assertIn('Fleet not found: random_username/foobar', cm.exception.message)

    def test_has(self):
        # should be true if the fleet name exists, otherwise it should return false.
        self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertFalse(self.balena.models.fleet.has('FooBar1'))
        self.assertTrue(self.balena.models.fleet.has('FooBar'))

    def test_has_any(self):
        # given no fleets, it should return false.
        self.assertFalse(self.balena.models.fleet.has_any())

        # should return true if at least one fleet exists.
        self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertTrue(self.balena.models.fleet.has_any())

    def test_get_by_id(self):
        # raise balena.exceptions.FleetNotFound if no fleet found.
        with self.assertRaises(self.helper.balena_exceptions.FleetNotFound):
            self.balena.models.fleet.get_by_id(1)

        # found an fleet, it should return an fleet with matched id.
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertEqual(self.balena.models.fleet.get_by_id(fleet['id'])['id'], fleet['id'])

    def test_remove(self):
        # should be able to remove an existing fleet by name.
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertEqual(len(self.balena.models.fleet.get_all()), 1)
        self.balena.models.fleet.remove('FooBar')
        self.assertEqual(len(self.balena.models.fleet.get_all()), 0)

    def test_generate_provisioning_key(self):
        # should be rejected if the fleet id does not exist.
        with self.assertRaises(self.helper.balena_exceptions.FleetNotFound):
            self.balena.models.fleet.generate_provisioning_key('5685')

        # should be able to generate a provisioning key by fleet id.
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        key = self.balena.models.fleet.generate_provisioning_key(fleet['id'])
        self.assertEqual(len(key), 32)

    def test_enable_rolling_updates(self):
        # should enable rolling update for the fleets devices.
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.balena.models.fleet.disable_rolling_updates(fleet['id'])
        self.balena.models.fleet.enable_rolling_updates(fleet['id'])
        fleet = self.balena.models.fleet.get('FooBar')
        self.assertTrue(fleet['should_track_latest_release'])

    def test_disable_rolling_updates(self):
        # should disable rolling update for the fleets devices.
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.balena.models.fleet.enable_rolling_updates(fleet['id'])
        self.balena.models.fleet.disable_rolling_updates(fleet['id'])
        fleet = self.balena.models.fleet.get('FooBar')
        self.assertFalse(fleet['should_track_latest_release'])

    def test_enable_device_urls(self):
        # should enable the device url for the fleets devices.
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        device = self.balena.models.device.register(fleet['id'], self.balena.models.device.generate_uuid())
        self.balena.models.fleet.enable_device_urls(fleet['id'])
        self.assertTrue(self.balena.models.device.has_device_url(device['uuid']))

    def test_disable_device_urls(self):
        # should disable the device url for the fleets devices.
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        device = self.balena.models.device.register(fleet['id'], self.balena.models.device.generate_uuid())
        self.balena.models.fleet.enable_device_urls(fleet['id'])
        self.balena.models.fleet.disable_device_urls(fleet['id'])
        self.assertFalse(self.balena.models.device.has_device_url(device['uuid']))

    def test_grant_support_access(self):
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        # should throw an error if the expiry timestamp is in the past.
        expiry_timestamp = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) - 10000)
        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.fleet.grant_support_access(fleet['id'], expiry_timestamp)

        # should grant support access until the specified time.
        expiry_time = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) + 3600 * 1000)
        self.balena.models.fleet.grant_support_access(fleet['id'], expiry_time)
        support_date = datetime.strptime(self.balena.models.fleet.get('FooBar')['is_accessible_by_support_until__date'], '%Y-%m-%dT%H:%M:%S.%fZ')
        self.assertEqual(self.helper.datetime_to_epoch_ms(support_date), expiry_time)

    def test_revoke_support_access(self):
        # should revoke support access.
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        expiry_time = int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000 + 3600 * 1000)
        self.balena.models.fleet.grant_support_access(fleet['id'], expiry_time)
        self.balena.models.fleet.revoke_support_access(fleet['id'])
        fleet = self.balena.models.fleet.get('FooBar')
        self.assertIsNone(fleet['is_accessible_by_support_until__date'])

    def test_will_track_new_releases(self):
        # should be configured to track new releases by default.
        fleet_info = self.helper.create_fleet_with_releases()
        self.assertTrue(self.balena.models.fleet.will_track_new_releases(fleet_info['fleet']['id']))

        # should be false when should_track_latest_release is false.
        self.balena.models.fleet.disable_rolling_updates(fleet_info['fleet']['id'])
        self.assertFalse(self.balena.models.fleet.will_track_new_releases(fleet_info['fleet']['id']))
        self.balena.models.fleet.enable_rolling_updates(fleet_info['fleet']['id'])
        self.assertTrue(self.balena.models.fleet.will_track_new_releases(fleet_info['fleet']['id']))

    def test_is_tracking_latest_release(self):
        # should be tracking the latest release by default.
        fleet_info = self.helper.create_fleet_with_releases()
        self.assertTrue(self.balena.models.fleet.is_tracking_latest_release(fleet_info['fleet']['id']))

        # should be false when should_track_latest_release is false.
        self.balena.models.fleet.disable_rolling_updates(fleet_info['fleet']['id'])
        self.assertFalse(self.balena.models.fleet.is_tracking_latest_release(fleet_info['fleet']['id']))
        self.balena.models.fleet.enable_rolling_updates(fleet_info['fleet']['id'])
        self.assertTrue(self.balena.models.fleet.is_tracking_latest_release(fleet_info['fleet']['id']))

        # should be false when the current commit is not of the latest release.
        self.balena.models.fleet.set_to_release(fleet_info['fleet']['id'], fleet_info['old_release']['commit'])
        # fleet.set_to_release() will set should_track_latest_release to false so need to set it to true again.
        self.balena.models.fleet.enable_rolling_updates(fleet_info['fleet']['id'])
        self.assertFalse(self.balena.models.fleet.is_tracking_latest_release(fleet_info['fleet']['id']))

    def test_get_target_release_hash(self):
        # should retrieve the commit hash of the current release.
        fleet_info = self.helper.create_fleet_with_releases()
        self.assertEqual(self.balena.models.fleet.get_target_release_hash(fleet_info['fleet']['id']), fleet_info['current_release']['commit'])

    def test_set_to_release(self):
        # should set the fleet to specific release & disable latest release tracking
        fleet_info = self.helper.create_fleet_with_releases()
        self.balena.models.fleet.set_to_release(fleet_info['fleet']['id'], fleet_info['old_release']['commit'])
        self.assertEqual(self.balena.models.fleet.get_target_release_hash(fleet_info['fleet']['id']), fleet_info['old_release']['commit'])
        self.assertFalse(self.balena.models.fleet.will_track_new_releases(fleet_info['fleet']['id']))
        self.assertFalse(self.balena.models.fleet.is_tracking_latest_release(fleet_info['fleet']['id']))

    def test_track_latest_release(self):
        # should re-enable latest release tracking
        fleet_info = self.helper.create_fleet_with_releases()
        self.balena.models.fleet.set_to_release(fleet_info['fleet']['id'], fleet_info['old_release']['commit'])
        self.assertEqual(self.balena.models.fleet.get_target_release_hash(fleet_info['fleet']['id']), fleet_info['old_release']['commit'])
        self.assertFalse(self.balena.models.fleet.will_track_new_releases(fleet_info['fleet']['id']))
        self.assertFalse(self.balena.models.fleet.is_tracking_latest_release(fleet_info['fleet']['id']))
        self.balena.models.fleet.track_latest_release(fleet_info['fleet']['id'])
        self.assertEqual(self.balena.models.fleet.get_target_release_hash(fleet_info['fleet']['id']), fleet_info['current_release']['commit'])
        self.assertTrue(self.balena.models.fleet.will_track_new_releases(fleet_info['fleet']['id']))
        self.assertTrue(self.balena.models.fleet.is_tracking_latest_release(fleet_info['fleet']['id']))

    def test_get_dashboard_url(self):
        # raise balena.exceptions.InvalidParameter if fleet id is not a number.
        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.fleet.get_dashboard_url('1476418a')

        # should return the respective dashboard url when an fleet id is provided.
        url = self.balena.models.fleet.get_dashboard_url('1476418')
        self.assertEqual(
            url,
            'https://dashboard.balena-cloud.com/fleets/1476418'
        )
        
    def test_invite_create(self):
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])

        # should create and return an fleet invite
        invite = self.balena.models.fleet.invite.create(fleet['id'], 'james@resin.io', 'developer', 'Python SDK test invite')
        self.assertEqual(invite['message'], 'Python SDK test invite')
        self.assertEqual(invite['is_invited_to__fleet']['__id'], fleet['id'])
        self.balena.models.fleet.invite.revoke(invite['id'])
        
        # should throw an error when role is not found
        # raise balena.exceptions.BalenaFleetMembershipRoleNotFound if  role is not found.
        with self.assertRaises(self.helper.balena_exceptions.BalenaFleetMembershipRoleNotFound):
            self.balena.models.fleet.invite.create(fleet['id'], 'james@resin.io', 'developer1', 'Python SDK test invite')
            
    def test_invite_get_all(self):
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])

        # shoud return an empty list
        invite_list = self.balena.models.fleet.invite.get_all()
        self.assertEqual(0, len(invite_list))
        
        # shoud return an invite list with length equals 1.
        self.balena.models.fleet.invite.create(fleet['id'], 'james@resin.io', 'developer', 'Python SDK test invite')
        invite_list = self.balena.models.fleet.invite.get_all()
        self.assertEqual(1, len(invite_list))
        
    def test_invite_get_all_by_fleet(self):
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])

        # shoud return an empty list
        invite_list = self.balena.models.fleet.invite.get_all_by_fleet(fleet['id'])
        self.assertEqual(0, len(invite_list))
        
        # shoud return an invite list with length equals 1.
        self.balena.models.fleet.invite.create(fleet['id'], 'james@resin.io', 'developer', 'Python SDK test invite')
        invite_list = self.balena.models.fleet.invite.get_all_by_fleet(fleet['id'])
        self.assertEqual(1, len(invite_list))

    def test_membership_create(self):
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])

        # should create and return an fleet membership
        membership = self.balena.models.fleet.membership.create(fleet['id'], 'nghiant2710')
        self.assertEqual(membership['is_member_of__fleet']['__id'], fleet['id'])
        self.balena.models.fleet.membership.remove(membership['id'])
        
        # should throw an error when role is not found
        # raise balena.exceptions.BalenaFleetMembershipRoleNotFound if  role is not found.
        with self.assertRaises(self.helper.balena_exceptions.BalenaFleetMembershipRoleNotFound):
            self.balena.models.fleet.membership.create(fleet['id'], 'james@resin.io', 'developer1')
            
    def test_membership_get_all(self):
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])

        # shoud return an empty list
        membership_list = self.balena.models.fleet.membership.get_all()
        self.assertEqual(0, len(membership_list))
        
        # shoud return a list with length equals 1.
        self.balena.models.fleet.membership.create(fleet['id'], 'james@resin.io')
        membership_list = self.balena.models.fleet.membership.get_all()
        self.assertEqual(1, len(membership_list))
        
    def test_membership_get_all_by_fleet(self):
        fleet = self.balena.models.fleet.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])

        # shoud return an empty list
        membership_list = self.balena.models.fleet.membership.get_all_by_fleet(fleet['id'])
        self.assertEqual(0, len(membership_list))
        
        # shoud return a list with length equals 1.
        self.balena.models.fleet.membership.create(fleet['id'], 'james@resin.io')
        membership_list = self.balena.models.fleet.membership.get_all_by_fleet(fleet['id'])
        self.assertEqual(1, len(membership_list))


if __name__ == '__main__':
    unittest.main()
