import unittest
import json
from datetime import datetime

from tests.helper import TestHelper


class TestApplication(unittest.TestCase):

    helper = None
    resin = None

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.resin = cls.helper.resin

    def tearDown(self):
        # Wipe all apps after every test case.
        self.helper.wipe_application()

    def test_create(self):
        # should be rejected if the device type is invalid
        with self.assertRaises(self.helper.resin_exceptions.InvalidDeviceType):
            self.resin.models.application.create('FooBar', 'Foo')

        # should be rejected if the name has less than four characters
        with self.assertRaises(Exception) as cm:
            self.resin.models.application.create('Fo', 'Raspberry Pi 2')
        self.assertIn('It is necessary that each app name that is of a user (Auth), has a Length (Type) that is greater than or equal to 4', cm.exception.message)

        # should be able to create an application
        app = json.loads(self.resin.models.application.create('FooBar', 'Raspberry Pi 2').decode('utf-8'))
        self.assertEqual(app['app_name'], 'FooBar')

    def test_get_all(self):
        # given no applications, it should return empty list.
        self.assertEqual(self.resin.models.application.get_all(), [])

        # given there is an application, it should return a list with length 2.
        self.resin.models.application.create('FooBar', 'Raspberry Pi 2')
        self.resin.models.application.create('FooBar1', 'Raspberry Pi 2')
        all_apps = self.resin.models.application.get_all()
        self.assertEqual(len(all_apps), 2)
        self.assertNotEqual(all_apps[0]['app_name'], all_apps[1]['app_name'])

    def test_get(self):
        # raise resin.exceptions.ApplicationNotFound if no application found.
        with self.assertRaises(self.helper.resin_exceptions.ApplicationNotFound):
            self.resin.models.application.get('AppNotExist')

        # found an application, it should return an application with matched name.
        self.resin.models.application.create('FooBar', 'Raspberry Pi 2')
        self.assertEqual(self.resin.models.application.get('FooBar')['app_name'], 'FooBar')

    def test_has(self):
        # should be true if the application name exists, otherwise it should return false.
        self.resin.models.application.create('FooBar', 'Raspberry Pi 2')
        self.assertFalse(self.resin.models.application.has('FooBar1'))
        self.assertTrue(self.resin.models.application.has('FooBar'))

    def test_has_any(self):
        # given no applications, it should return false.
        self.assertFalse(self.resin.models.application.has_any())

        # should return true if at least one application exists.
        self.resin.models.application.create('FooBar', 'Raspberry Pi 2')
        self.assertTrue(self.resin.models.application.has_any())

    def test_get_by_id(self):
        # raise resin.exceptions.ApplicationNotFound if no application found.
        with self.assertRaises(self.helper.resin_exceptions.ApplicationNotFound):
            self.resin.models.application.get_by_id(1)

        # found an application, it should return an application with matched id.
        app = json.loads(self.resin.models.application.create('FooBar', 'Raspberry Pi 2').decode('utf-8'))
        self.assertEqual(self.resin.models.application.get_by_id(app['id'])['id'], app['id'])

    def test_remove(self):
        # should be able to remove an existing application by name.
        app = json.loads(self.resin.models.application.create('FooBar', 'Raspberry Pi 2').decode('utf-8'))
        self.assertEqual(len(self.resin.models.application.get_all()), 1)
        self.resin.models.application.remove('FooBar')
        self.assertEqual(len(self.resin.models.application.get_all()), 0)

    def test_generate_provisioning_key(self):
        # should be rejected if the application id does not exist.
        with self.assertRaises(self.helper.resin_exceptions.ApplicationNotFound):
            self.resin.models.application.generate_provisioning_key('5685')

        # should be able to generate a provisioning key by app id.
        app = json.loads(self.resin.models.application.create('FooBar', 'Raspberry Pi 2').decode('utf-8'))
        key = self.resin.models.application.generate_provisioning_key(app['id'])
        self.assertEqual(len(key), 32)

    def test_enable_rolling_updates(self):
        # should enable rolling update for the applications devices.
        app = json.loads(self.resin.models.application.create('FooBar', 'Raspberry Pi 2').decode('utf-8'))
        self.resin.models.application.disable_rolling_updates(app['id'])
        self.resin.models.application.enable_rolling_updates(app['id'])
        app = self.resin.models.application.get('FooBar')
        self.assertTrue(app['should_track_latest_release'])

    def test_disable_rolling_updates(self):
        # should disable rolling update for the applications devices.
        app = json.loads(self.resin.models.application.create('FooBar', 'Raspberry Pi 2').decode('utf-8'))
        self.resin.models.application.enable_rolling_updates(app['id'])
        self.resin.models.application.disable_rolling_updates(app['id'])
        app = self.resin.models.application.get('FooBar')
        self.assertFalse(app['should_track_latest_release'])

    def test_enable_device_urls(self):
        # should enable the device url for the applications devices.
        app = json.loads(self.resin.models.application.create('FooBar', 'Raspberry Pi 2').decode('utf-8'))
        device = json.loads(self.resin.models.device.register(app['id'], self.resin.models.device.generate_uuid()).decode('utf-8'))
        self.resin.models.application.enable_device_urls(app['id'])
        self.assertTrue(self.resin.models.device.has_device_url(device['uuid']))

    def test_disable_device_urls(self):
        # should disable the device url for the applications devices.
        app = json.loads(self.resin.models.application.create('FooBar', 'Raspberry Pi 2').decode('utf-8'))
        device = json.loads(self.resin.models.device.register(app['id'], self.resin.models.device.generate_uuid()).decode('utf-8'))
        self.resin.models.application.enable_device_urls(app['id'])
        self.resin.models.application.disable_device_urls(app['id'])
        self.assertFalse(self.resin.models.device.has_device_url(device['uuid']))

    def test_grant_support_access(self):
        app = json.loads(self.resin.models.application.create('FooBar', 'Raspberry Pi 2').decode('utf-8'))
        # should throw an error if the expiry timestamp is in the past.
        expiry_timestamp = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) - 10000)
        with self.assertRaises(self.helper.resin_exceptions.InvalidParameter):
            self.resin.models.application.grant_support_access(app['id'], expiry_timestamp)

        # should grant support access until the specified time.
        expiry_time = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) + 3600 * 1000)
        self.resin.models.application.grant_support_access(app['id'], expiry_time)
        support_date = datetime.strptime(self.resin.models.application.get('FooBar')['is_accessible_by_support_until__date'], '%Y-%m-%dT%H:%M:%S.%fZ')
        self.assertEqual(self.helper.datetime_to_epoch_ms(support_date), expiry_time)

    def test_revoke_support_access(self):
        # should revoke support access.
        app = json.loads(self.resin.models.application.create('FooBar', 'Raspberry Pi 2').decode('utf-8'))
        expiry_time = int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000 + 3600 * 1000)
        self.resin.models.application.grant_support_access(app['id'], expiry_time)
        self.resin.models.application.revoke_support_access(app['id'])
        app = self.resin.models.application.get('FooBar')
        self.assertIsNone(app['is_accessible_by_support_until__date'])

if __name__ == '__main__':
    unittest.main()
