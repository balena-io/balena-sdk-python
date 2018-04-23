import unittest
import json
from datetime import datetime

from tests.helper import TestHelper


class TestDevice(unittest.TestCase):

    helper = None
    resin = None

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.resin = cls.helper.resin

    def tearDown(self):
        # Wipe all apps after every test case.
        self.helper.wipe_application()

    def test_get_display_name(self):
        # should get the display name for a known slug.
        self.assertEqual(
            self.resin.models.device.get_display_name('raspberry-pi'),
            'Raspberry Pi (v1 or Zero)'
        )

        # should be rejected if the slug is invalid.
        with self.assertRaises(self.helper.resin_exceptions.InvalidDeviceType):
            self.resin.models.device.get_display_name('PYTHONSDK')

    def test_get_device_slug(self):
        # should be the slug from a display name.
        self.assertEqual(
            self.resin.models.device.get_device_slug('Raspberry Pi (v1 or Zero)'),
            'raspberry-pi'
        )

        # should be rejected if the display name is invalid.
        with self.assertRaises(self.helper.resin_exceptions.InvalidDeviceType):
            self.resin.models.device.get_device_slug('PYTHONSDK')

    def test_get_supported_device_types(self):
        # should return a non empty array.
        self.assertGreater(
            len(self.resin.models.device.get_supported_device_types()),
            0
        )

        # should return all valid display names.
        for dev_type in self.resin.models.device.get_supported_device_types():
            self.assertTrue(self.resin.models.device.get_device_slug(dev_type))

    def test_get_manifest_by_slug(self):
        # should become the manifest if the slug is valid.
        manifest = self.resin.models.device.get_manifest_by_slug('raspberry-pi')
        self.assertTrue(manifest['slug'])
        self.assertTrue(manifest['name'])
        self.assertTrue(manifest['options'])

        # should be rejected if the device slug is invalid.
        with self.assertRaises(self.helper.resin_exceptions.InvalidDeviceType):
            self.resin.models.device.get_manifest_by_slug('PYTHONSDK')

    def test_generate_uuid(self):
        # should generate a valid uuid.
        uuid = self.resin.models.device.generate_uuid()
        self.assertEqual(len(uuid), 62)
        self.assertRegexpMatches(uuid.decode('utf-8'), '^[a-z0-9]{62}$')

        # should generate different uuids.
        self.assertNotEqual(
            self.resin.models.device.generate_uuid(),
            self.resin.models.device.generate_uuid()
        )

    def test_register(self):
        app = self.resin.models.application.create('FooBar', 'Raspberry Pi 2')

        # should be able to register a device to a valid application id.
        self.resin.models.device.register(app['id'], self.resin.models.device.generate_uuid())
        self.assertEqual(
            len(self.resin.models.device.get_all_by_application(app['app_name'])),
            1
        )

        # should become valid device registration info.
        uuid = self.resin.models.device.generate_uuid()
        device = self.resin.models.device.register(app['id'], uuid)
        self.assertEqual(
            device['uuid'],
            uuid.decode('utf-8')
        )

        # should be rejected if the application id does not exist.
        with self.assertRaises(self.helper.resin_exceptions.ApplicationNotFound):
            self.resin.models.device.register('999999', self.resin.models.device.generate_uuid())

    def test_get_all(self):
        # should return empty list.
        self.assertEqual(len(self.resin.models.device.get_all()), 0)

        # should return correct total of device in all applications.
        self.helper.create_device('app1')
        self.helper.create_device('app2')
        self.assertEqual(len(self.resin.models.device.get_all()), 2)

    def test_get_all_by_application_id(self):
        app = self.resin.models.application.create('FooBar', 'Raspberry Pi 2')
        # should return empty
        self.assertEqual(len(self.resin.models.device.get_all_by_application_id(app['id'])), 0)

        # should return correct number of device in an application.
        self.resin.models.device.register(app['id'], self.resin.models.device.generate_uuid())
        self.resin.models.device.register(app['id'], self.resin.models.device.generate_uuid())
        self.assertEqual(len(self.resin.models.device.get_all_by_application_id(app['id'])), 2)

    def test_get_all_by_application(self):
        app = self.resin.models.application.create('FooBar', 'Raspberry Pi 2')
        # should return empty
        self.assertEqual(len(self.resin.models.device.get_all_by_application(app['app_name'])), 0)

        # should return correct number of device in an application.
        self.resin.models.device.register(app['id'], self.resin.models.device.generate_uuid())
        self.resin.models.device.register(app['id'], self.resin.models.device.generate_uuid())
        self.assertEqual(len(self.resin.models.device.get_all_by_application(app['app_name'])), 2)

    def test_get(self):
        # should be able to get the device by uuid.
        app, device = self.helper.create_device()
        self.assertEqual(
            self.resin.models.device.get(device['uuid'])['id'],
            device['id']
        )

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.resin_exceptions.DeviceNotFound):
            self.resin.models.device.get('999999999999')

    def test_rename(self):
        app, device = self.helper.create_device()

        # should be able to rename the device by uuid.
        self.resin.models.device.rename(device['uuid'], 'test-device')
        self.assertEqual(
            self.resin.models.device.get_name(device['uuid']),
            'test-device'
        )

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.resin_exceptions.DeviceNotFound):
            self.resin.models.device.rename('99999999999', 'new-test-device')

    def test_get_by_name(self):
        # should be able to get the device.
        app, device = self.helper.create_device()
        self.resin.models.device.rename(device['uuid'], 'test-device')
        self.assertEqual(
            self.resin.models.device.get_by_name('test-device')[0]['uuid'],
            device['uuid']
        )

    def test_get_name(self):
        # should get the correct name by uuid.
        app, device = self.helper.create_device()
        self.resin.models.device.rename(device['uuid'], 'test-device')
        self.assertEqual(
            self.resin.models.device.get_name(device['uuid']),
            'test-device'
        )

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.resin_exceptions.DeviceNotFound):
            self.resin.models.device.get_name('9999999999999999')

    def test_get_application_name(self):
        # should get the correct application name from a device uuid.
        app, device = self.helper.create_device()
        self.assertEqual(
            self.resin.models.device.get_application_name(device['uuid']),
            app['app_name']
        )

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.resin_exceptions.DeviceNotFound):
            self.resin.models.device.get_application_name('9999999999999999')

    def test_has(self):
        # should eventually be true if the device uuid exists.
        app, device = self.helper.create_device()
        self.assertTrue(self.resin.models.device.has(device['uuid']))

        # should eventually be false if the device uuid does not exist.
        self.assertFalse(self.resin.models.device.has('999999999'))

    def test_is_online(self):
        # should eventually be false if the device uuid exists.
        app, device = self.helper.create_device()
        self.assertFalse(self.resin.models.device.is_online(device['uuid']))

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.resin_exceptions.DeviceNotFound):
            self.resin.models.device.is_online('9999999999999999')

    def test_remove(self):
        app, device = self.helper.create_device()

        # should be able to remove the device by uuid
        self.resin.models.device.remove(device['uuid'])
        self.assertEqual(len(self.resin.models.device.get_all()), 0)
        self.assertEqual(len(self.resin.models.device.get_all_by_application_id(app['id'])), 0)

    def test_note(self):
        app, device = self.helper.create_device()

        # should be able to note a device by uuid.
        self.resin.models.device.note(device['uuid'], 'Python SDK Test')
        self.assertEqual(
            self.resin.models.device.get(device['uuid'])['note'],
            'Python SDK Test'
        )

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.resin_exceptions.DeviceNotFound):
            self.resin.models.device.note('99999999999', 'new-test-device')

    def test_enable_device_url(self):
        app, device = self.helper.create_device()

        # should be able to enable web access using a uuid.
        self.resin.models.device.enable_device_url(device['uuid'])
        self.assertTrue(self.resin.models.device.has_device_url(device['uuid']))

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.resin_exceptions.DeviceNotFound):
            self.resin.models.device.has_device_url('99999999999')

    def test_disable_device_url(self):
        app, device = self.helper.create_device()

        # should be able to disable web access using a uuid.
        self.resin.models.device.enable_device_url(device['uuid'])
        self.resin.models.device.disable_device_url(device['uuid'])
        self.assertFalse(self.resin.models.device.has_device_url(device['uuid']))

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.resin_exceptions.DeviceNotFound):
            self.resin.models.device.has_device_url('99999999999')

    def test_move(self):
        app, device = self.helper.create_device()
        app2 = self.resin.models.application.create('FooBarBar', 'Raspberry Pi 2')

        # should be able to move a device by device uuid and application name.
        self.resin.models.device.move(device['uuid'], 'FooBarBar')
        self.assertEqual(self.resin.models.device.get_application_name(device['uuid']), 'FooBarBar')

        # should be rejected with an incompatibility error.
        self.resin.models.application.create('FooBarBarBar', 'Intel NUC')
        with self.assertRaises(self.helper.resin_exceptions.IncompatibleApplication):
            self.resin.models.device.move(device['uuid'], 'FooBarBarBar')

    def test_set_custom_location(self):
        app, device = self.helper.create_device()
        location = {
            'latitude': '41.383333',
            'longitude': '2.183333'
        }

        # should be able to set the location of a device by uuid.
        self.resin.models.device.set_custom_location(device['uuid'], location)
        device = self.resin.models.device.get(device['uuid'])
        self.assertEqual(device['custom_latitude'], '41.383333')
        self.assertEqual(device['custom_longitude'], '2.183333')

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.resin_exceptions.DeviceNotFound):
            self.resin.models.device.set_custom_location('99999999', location)

    def test_unset_custom_location(self):
        app, device = self.helper.create_device()
        location = {
            'latitude': '41.383333',
            'longitude': '2.183333'
        }
        self.resin.models.device.set_custom_location(device['uuid'], location)

        # should be able to unset the location of a device by uuid.
        self.resin.models.device.unset_custom_location(device['uuid'])
        device = self.resin.models.device.get(device['uuid'])
        self.assertEqual(device['custom_latitude'], '')
        self.assertEqual(device['custom_longitude'], '')

        # should be rejected if the device uuid does not exist.
        with self.assertRaises(self.helper.resin_exceptions.DeviceNotFound):
            self.resin.models.device.unset_custom_location('99999999')

    def test_grant_support_access(self):
        app, device = self.helper.create_device()

        # should throw an error if the expiry timestamp is in the past.
        expiry_timestamp = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) - 10000)

        with self.assertRaises(self.helper.resin_exceptions.InvalidParameter):
            self.resin.models.device.grant_support_access(device['uuid'], expiry_timestamp)

        # should grant support access for the correct amount of time.
        expiry_time = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) + 3600 * 1000)
        self.resin.models.device.grant_support_access(device['uuid'], expiry_time)
        support_date = datetime.strptime(self.resin.models.device.get(device['uuid'])['is_accessible_by_support_until__date'], '%Y-%m-%dT%H:%M:%S.%fZ')
        self.assertEqual(self.helper.datetime_to_epoch_ms(support_date), expiry_time)

    def test_revoke_support_access(self):
        app, device = self.helper.create_device()

        # should revoke support access
        expiry_time = int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000 + 3600 * 1000)
        self.resin.models.device.grant_support_access(device['uuid'], expiry_time)
        self.resin.models.device.revoke_support_access(device['uuid'])
        self.assertIsNone(self.resin.models.device.get(device['uuid'])['is_accessible_by_support_until__date'])


if __name__ == '__main__':
    unittest.main()
