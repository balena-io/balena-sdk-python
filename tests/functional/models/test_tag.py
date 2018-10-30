import unittest
import json
from datetime import datetime

from tests.helper import TestHelper


class BaseTagTest(object):

    def __init__(self, test_obj):
        self.test_obj = test_obj

    def test_get_all_by_application(self, test_runner, resource_id, app_id):
        # should become an empty array by default
        test_runner.assertEqual(self.test_obj.get_all_by_application(app_id), [])

        # given a tag
        self.test_obj.set(resource_id, 'Foo', 'Bar')

        # should retrieve the tag by resource id
        tags = self.test_obj.get_all_by_application(app_id)
        test_runner.assertEqual(len(tags), 1)
        test_runner.assertEqual(tags[0]['tag_key'], 'Foo')
        test_runner.assertEqual(tags[0]['value'], 'Bar')

    def test_get_all(self, test_runner, resource_id):
        # should become an empty array by default
        test_runner.assertEqual(self.test_obj.get_all(), [])

        # given a tag
        self.test_obj.set(resource_id, 'Foo', 'Bar')
        self.test_obj.set(resource_id, 'Foo1', 'Bar1')

        # should retrieve all the tags
        tags = self.test_obj.get_all()
        tags = sorted(tags, key=lambda k: k['tag_key'])
        test_runner.assertEqual(len(tags), 2)
        test_runner.assertEqual(tags[0]['tag_key'], 'Foo')
        test_runner.assertEqual(tags[0]['value'], 'Bar')
        test_runner.assertEqual(tags[1]['tag_key'], 'Foo1')
        test_runner.assertEqual(tags[1]['value'], 'Bar1')

    def test_set(self, test_runner, resource_id):
        # should be able to create a tag given a resource id
        self.test_obj.set(resource_id, 'Foo', 'Bar')
        tags = self.test_obj.get_all()
        test_runner.assertEqual(len(tags), 1)
        test_runner.assertEqual(tags[0]['tag_key'], 'Foo')
        test_runner.assertEqual(tags[0]['value'], 'Bar')

        # should be able to create a numeric tag
        self.test_obj.set(resource_id, 'Foo', '1')
        tags = self.test_obj.get_all()
        test_runner.assertEqual(len(tags), 1)
        test_runner.assertEqual(tags[0]['tag_key'], 'Foo')
        test_runner.assertEqual(tags[0]['value'], '1')

        # should not allow creating a balena tag
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(resource_id, 'io.balena.test', 'not allowed')
        test_runner.assertIn('Tag keys beginning with io.balena. are reserved.', cm.exception.message)

        # should not allow creating a resin tag
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(resource_id, 'io.resin.test', 'not allowed')
        test_runner.assertIn('Tag keys beginning with io.resin. are reserved.', cm.exception.message)

        # should not allow creating a tag with a name containing a whitespace
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(resource_id, 'Foo 1', 'not allowed')
        test_runner.assertIn('Tag keys cannot contain whitespace.', cm.exception.message)

        # should be rejected if the resource id does not exist
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(99999999, 'Foo', 'not allowed')

        # should be rejected if the tag_key is None
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(resource_id, None, 'not allowed')
        test_runner.assertIn('cannot be null', cm.exception.message)

        # should be rejected if the tag_key is empty
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(resource_id, '', 'not allowed')
        test_runner.assertIn('Tag key cannot be empty.', cm.exception.message)

        # given 2 tags, should be able to update a tag without affecting the rest
        self.test_obj.set(resource_id, 'Foo', 'Bar')
        self.test_obj.set(resource_id, 'Foo1', 'Bar1')

        self.test_obj.set(resource_id, 'Foo', 'BarBar')
        tags = self.test_obj.get_all()
        tags = sorted(tags, key=lambda k: k['tag_key'])
        test_runner.assertEqual(len(tags), 2)
        test_runner.assertEqual(tags[0]['tag_key'], 'Foo')
        test_runner.assertEqual(tags[0]['value'], 'BarBar')
        test_runner.assertEqual(tags[1]['tag_key'], 'Foo1')
        test_runner.assertEqual(tags[1]['value'], 'Bar1')

    def test_remove(self, test_runner, resource_id):
        # should be able to remove a tag by resource id
        tag = self.test_obj.set(resource_id, 'Foo', 'Bar')
        test_runner.assertEqual(len(self.test_obj.get_all()), 1)

        self.test_obj.remove(resource_id, tag['tag_key'])
        test_runner.assertEqual(len(self.test_obj.get_all()), 0)


class TestReleaseTag(unittest.TestCase):

    helper = None
    balena = None
    release_tag = None
    base_tag_test = None

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.release_tag = cls.balena.models.tag.release
        cls.base_tag_test = BaseTagTest(cls.release_tag)

    def tearDown(self):
        # Wipe all apps after every test case.
        self.helper.wipe_application()

    def test_get_all_by_application(self):
        app_info = self.helper.create_multicontainer_app()
        self.base_tag_test.test_get_all_by_application(self, app_info['current_release']['id'], app_info['app']['id'])

    def test_get_all(self):
        app_info = self.helper.create_multicontainer_app()
        self.base_tag_test.test_get_all(self, app_info['current_release']['id'])

    def test_set(self):
        app_info = self.helper.create_multicontainer_app()
        self.base_tag_test.test_set(self, app_info['current_release']['id'])

    def test_remove(self):
        app_info = self.helper.create_multicontainer_app()
        self.base_tag_test.test_remove(self, app_info['current_release']['id'])

    def test_get_all_by_release(self):
        app_info = self.helper.create_multicontainer_app()
        release_id = app_info['current_release']['id']
        # should become an empty array by default
        self.assertEqual(self.release_tag.get_all_by_release(release_id), [])

        # given a tag
        self.release_tag.set(release_id, 'Foo', 'Bar')

        # should retrieve the tag by uuid
        tags = self.release_tag.get_all_by_release(release_id)
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]['tag_key'], 'Foo')
        self.assertEqual(tags[0]['value'], 'Bar')

        # given 2 tags
        self.release_tag.set(release_id, 'Foo1', 'Bar1')

        # should retrieve all the tags by uuid
        tags = self.release_tag.get_all_by_release(release_id)
        tags = sorted(tags, key=lambda k: k['tag_key'])
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0]['tag_key'], 'Foo')
        self.assertEqual(tags[0]['value'], 'Bar')
        self.assertEqual(tags[1]['tag_key'], 'Foo1')
        self.assertEqual(tags[1]['value'], 'Bar1')


if __name__ == '__main__':
    unittest.main()
