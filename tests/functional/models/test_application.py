import unittest
import json
from datetime import datetime

from tests.helper import TestHelper


class TestApplication(unittest.TestCase):

    helper = None
    balena = None

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena

    def tearDown(self):
        # Wipe all apps after every test case.
        self.helper.wipe_application()

    def test_create(self):
        # should be rejected if the device type is invalid
        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.application.create('FooBar', 'Foo', self.helper.default_organization['id'])

        # should be rejected if the name has less than four characters
        with self.assertRaises(Exception) as cm:
            self.balena.models.application.create('Fo', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertIn('It is necessary that each application has an app name that has a Length (Type) that is greater than or equal to 4 and is less than or equal to 100', cm.exception.message)

        # should be able to create an application
        app = self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertEqual(app['app_name'], 'FooBar')

        # should be rejected if the application type is invalid
        with self.assertRaises(self.helper.balena_exceptions.InvalidApplicationType):
            self.balena.models.application.create('FooBar1', 'Raspberry Pi 3', self.helper.default_organization['id'], 'microservices-starterrrrrr')

        # should be able to create an application with a specific application type
        app = self.balena.models.application.create('FooBar1', 'Raspberry Pi 3', self.helper.default_organization['id'], 'microservices-starter')
        self.assertEqual(app['app_name'], 'FooBar1')

    def test_get_all(self):
        # given no applications, it should return empty list.
        self.assertEqual(self.balena.models.application.get_all(), [])

        # given there is an application, it should return a list with length 2.
        self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.balena.models.application.create('FooBar1', 'Raspberry Pi 2', self.helper.default_organization['id'])
        all_apps = self.balena.models.application.get_all()
        self.assertEqual(len(all_apps), 2)
        self.assertNotEqual(all_apps[0]['app_name'], all_apps[1]['app_name'])

    def test_get(self):
        # raise balena.exceptions.ApplicationNotFound if no application found.
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.get('AppNotExist')

        # found an application, it should return an application with matched name.
        self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertEqual(self.balena.models.application.get('FooBar')['app_name'], 'FooBar')

    def test_get_by_owner(self):
        # raise balena.exceptions.ApplicationNotFound if no application found.
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.get_by_owner('AppNotExist', self.helper.credentials['user_id'])

        # found an application, it should return an application with matched name.
        self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertEqual(self.balena.models.application.get_by_owner('FooBar', self.helper.default_organization['handle'])['app_name'], 'FooBar')

        # should not find the created application with a different username
        with self.assertRaises(Exception) as cm:
            self.balena.models.application.get_by_owner('FooBar', 'random_username')
        self.assertIn('Application not found: random_username/foobar', cm.exception.message)

    def test_has(self):
        # should be true if the application name exists, otherwise it should return false.
        self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertFalse(self.balena.models.application.has('FooBar1'))
        self.assertTrue(self.balena.models.application.has('FooBar'))

    def test_has_any(self):
        # given no applications, it should return false.
        self.assertFalse(self.balena.models.application.has_any())

        # should return true if at least one application exists.
        self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertTrue(self.balena.models.application.has_any())

    def test_get_by_id(self):
        # raise balena.exceptions.ApplicationNotFound if no application found.
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.get_by_id(1)

        # found an application, it should return an application with matched id.
        app = self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertEqual(self.balena.models.application.get_by_id(app['id'])['id'], app['id'])

    def test_remove(self):
        # should be able to remove an existing application by name.
        app = self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.assertEqual(len(self.balena.models.application.get_all()), 1)
        self.balena.models.application.remove('FooBar')
        self.assertEqual(len(self.balena.models.application.get_all()), 0)

    def test_generate_provisioning_key(self):
        # should be rejected if the application id does not exist.
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.generate_provisioning_key('5685')

        # should be able to generate a provisioning key by app id.
        app = self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        key = self.balena.models.application.generate_provisioning_key(app['id'])
        self.assertEqual(len(key), 32)

    def test_enable_rolling_updates(self):
        # should enable rolling update for the applications devices.
        app = self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.balena.models.application.disable_rolling_updates(app['id'])
        self.balena.models.application.enable_rolling_updates(app['id'])
        app = self.balena.models.application.get('FooBar')
        self.assertTrue(app['should_track_latest_release'])

    def test_disable_rolling_updates(self):
        # should disable rolling update for the applications devices.
        app = self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        self.balena.models.application.enable_rolling_updates(app['id'])
        self.balena.models.application.disable_rolling_updates(app['id'])
        app = self.balena.models.application.get('FooBar')
        self.assertFalse(app['should_track_latest_release'])

    def test_enable_device_urls(self):
        # should enable the device url for the applications devices.
        app = self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        device = self.balena.models.device.register(app['id'], self.balena.models.device.generate_uuid())
        self.balena.models.application.enable_device_urls(app['id'])
        self.assertTrue(self.balena.models.device.has_device_url(device['uuid']))

    def test_disable_device_urls(self):
        # should disable the device url for the applications devices.
        app = self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        device = self.balena.models.device.register(app['id'], self.balena.models.device.generate_uuid())
        self.balena.models.application.enable_device_urls(app['id'])
        self.balena.models.application.disable_device_urls(app['id'])
        self.assertFalse(self.balena.models.device.has_device_url(device['uuid']))

    def test_grant_support_access(self):
        app = self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        # should throw an error if the expiry timestamp is in the past.
        expiry_timestamp = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) - 10000)
        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.application.grant_support_access(app['id'], expiry_timestamp)

        # should grant support access until the specified time.
        expiry_time = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) + 3600 * 1000)
        self.balena.models.application.grant_support_access(app['id'], expiry_time)
        support_date = datetime.strptime(self.balena.models.application.get('FooBar')['is_accessible_by_support_until__date'], '%Y-%m-%dT%H:%M:%S.%fZ')
        self.assertEqual(self.helper.datetime_to_epoch_ms(support_date), expiry_time)

    def test_revoke_support_access(self):
        # should revoke support access.
        app = self.balena.models.application.create('FooBar', 'Raspberry Pi 2', self.helper.default_organization['id'])
        expiry_time = int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000 + 3600 * 1000)
        self.balena.models.application.grant_support_access(app['id'], expiry_time)
        self.balena.models.application.revoke_support_access(app['id'])
        app = self.balena.models.application.get('FooBar')
        self.assertIsNone(app['is_accessible_by_support_until__date'])

    def test_will_track_new_releases(self):
        # should be configured to track new releases by default.
        app_info = self.helper.create_app_with_releases()
        self.assertTrue(self.balena.models.application.will_track_new_releases(app_info['app']['id']))

        # should be false when should_track_latest_release is false.
        self.balena.models.application.disable_rolling_updates(app_info['app']['id'])
        self.assertFalse(self.balena.models.application.will_track_new_releases(app_info['app']['id']))
        self.balena.models.application.enable_rolling_updates(app_info['app']['id'])
        self.assertTrue(self.balena.models.application.will_track_new_releases(app_info['app']['id']))

    def test_is_tracking_latest_release(self):
        # should be tracking the latest release by default.
        app_info = self.helper.create_app_with_releases()
        self.assertTrue(self.balena.models.application.is_tracking_latest_release(app_info['app']['id']))

        # should be false when should_track_latest_release is false.
        self.balena.models.application.disable_rolling_updates(app_info['app']['id'])
        self.assertFalse(self.balena.models.application.is_tracking_latest_release(app_info['app']['id']))
        self.balena.models.application.enable_rolling_updates(app_info['app']['id'])
        self.assertTrue(self.balena.models.application.is_tracking_latest_release(app_info['app']['id']))

        # should be false when the current commit is not of the latest release.
        self.balena.models.application.set_to_release(app_info['app']['id'], app_info['old_release']['commit'])
        # app.set_to_release() will set should_track_latest_release to false so need to set it to true again.
        self.balena.models.application.enable_rolling_updates(app_info['app']['id'])
        self.assertFalse(self.balena.models.application.is_tracking_latest_release(app_info['app']['id']))

    def test_get_target_release_hash(self):
        # should retrieve the commit hash of the current release.
        app_info = self.helper.create_app_with_releases()
        self.assertEqual(self.balena.models.application.get_target_release_hash(app_info['app']['id']), app_info['current_release']['commit'])

    def test_set_to_release(self):
        # should set the application to specific release & disable latest release tracking
        app_info = self.helper.create_app_with_releases()
        self.balena.models.application.set_to_release(app_info['app']['id'], app_info['old_release']['commit'])
        self.assertEqual(self.balena.models.application.get_target_release_hash(app_info['app']['id']), app_info['old_release']['commit'])
        self.assertFalse(self.balena.models.application.will_track_new_releases(app_info['app']['id']))
        self.assertFalse(self.balena.models.application.is_tracking_latest_release(app_info['app']['id']))

    def test_track_latest_release(self):
        # should re-enable latest release tracking
        app_info = self.helper.create_app_with_releases()
        self.balena.models.application.set_to_release(app_info['app']['id'], app_info['old_release']['commit'])
        self.assertEqual(self.balena.models.application.get_target_release_hash(app_info['app']['id']), app_info['old_release']['commit'])
        self.assertFalse(self.balena.models.application.will_track_new_releases(app_info['app']['id']))
        self.assertFalse(self.balena.models.application.is_tracking_latest_release(app_info['app']['id']))
        self.balena.models.application.track_latest_release(app_info['app']['id'])
        self.assertEqual(self.balena.models.application.get_target_release_hash(app_info['app']['id']), app_info['current_release']['commit'])
        self.assertTrue(self.balena.models.application.will_track_new_releases(app_info['app']['id']))
        self.assertTrue(self.balena.models.application.is_tracking_latest_release(app_info['app']['id']))

    def test_get_dashboard_url(self):
        # raise balena.exceptions.InvalidParameter if application id is not a number.
        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.application.get_dashboard_url('1476418a')

        # should return the respective dashboard url when an application id is provided.
        url = self.balena.models.application.get_dashboard_url('1476418')
        self.assertEqual(
            url,
            'https://dashboard.balena-cloud.com/apps/1476418'
        )

if __name__ == '__main__':
    unittest.main()
