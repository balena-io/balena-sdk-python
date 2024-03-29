import unittest

from tests.helper import TestHelper


def find_with_tag_key(tag_list, tag_key):
    for item in tag_list:
        if item["tag_key"] == tag_key:
            return item
    return None


class BaseTagTest:
    def __init__(
        self,
        test_obj,
        associated_resource_name,
    ):
        self.test_obj = test_obj
        self.associated_resource_name = associated_resource_name

    def assert_get_all_by_associated_resource(self, test_runner, tags):
        tags = sorted(tags, key=lambda k: k["tag_key"])
        test_runner.assertEqual(len(tags), 4)
        test_runner.assertEqual(tags[0]["tag_key"], "Foo")
        test_runner.assertEqual(tags[0]["value"], "Bar")
        test_runner.assertEqual(tags[1]["tag_key"], "Foo1")
        test_runner.assertEqual(tags[1]["value"], "1")
        test_runner.assertEqual(tags[2]["tag_key"], "Foo2")
        test_runner.assertEqual(tags[2]["value"], "BarBar")
        test_runner.assertEqual(tags[3]["tag_key"], "Foo21")
        test_runner.assertEqual(tags[3]["value"], "Bar1")

    def test_get_all_by_application(self, test_runner, resource_id, app_id):
        # given a tag
        self.test_obj.set(resource_id, "Foo_get_all_by_application", "Bar")

        # should retrieve the tag by resource id
        tags = self.test_obj.get_all_by_application(app_id)
        tag = find_with_tag_key(tags, "Foo_get_all_by_application")
        test_runner.assertEqual(tag["value"], "Bar")

    def test_get_all(self, test_runner, resource_id):
        # given 2 tags
        current_length = len(self.test_obj.get_all())
        self.test_obj.set(resource_id, "Foo_get_all", "Bar")
        self.test_obj.set(resource_id, "Foo1_get_all", "Bar1")

        # should retrieve all the tags
        test_runner.assertEqual(len(self.test_obj.get_all()), (current_length + 2))

    def test_set(self, test_runner, resource_id):
        # should be able to create a tag given a resource id
        current_length = len(self.test_obj.get_all())
        self.test_obj.set(resource_id, "Foo", "Bar")

        new_tag_value = self.test_obj.get(resource_id, "Foo")

        test_runner.assertEqual(len(self.test_obj.get_all()), (current_length + 1))
        test_runner.assertEqual(new_tag_value, "Bar")

        # should be able to create a numeric tag
        current_length = len(self.test_obj.get_all())
        self.test_obj.set(resource_id, "Foo1", "1")

        new_tag_value = self.test_obj.get(resource_id, "Foo1")

        test_runner.assertEqual(len(self.test_obj.get_all()), (current_length + 1))
        test_runner.assertEqual(new_tag_value, "1")

        # should not allow creating a balena tag
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(resource_id, "io.balena.test", "not allowed")
        test_runner.assertIn("Tag keys beginning with io.balena. are reserved.", cm.exception.message)

        # should not allow creating a resin tag
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(resource_id, "io.resin.test", "not allowed")
        test_runner.assertIn("Tag keys beginning with io.resin. are reserved.", cm.exception.message)

        # should not allow creating a tag with a name containing a whitespace
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(resource_id, "Foo 1", "not allowed")
        test_runner.assertIn("Tag keys cannot contain whitespace.", cm.exception.message)

        # should be rejected if the resource id does not exist
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(99999999, "Foo", "not allowed")

        # should be rejected if the tag_key is None
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(resource_id, None, "not allowed")
        test_runner.assertIn("cannot be null", cm.exception.message)

        # should be rejected if the tag_key is empty
        with test_runner.assertRaises(Exception) as cm:
            self.test_obj.set(resource_id, "", "not allowed")
        test_runner.assertIn(
            (
                f"It is necessary that each {self.associated_resource_name} tag has a "
                "tag key that has a Length (Type) that is greater than 0."
            ),
            cm.exception.message,
        )

        # given 2 tags, should be able to update a tag without affecting the rest
        self.test_obj.set(resource_id, "Foo2", "Bar")
        self.test_obj.set(resource_id, "Foo21", "Bar1")
        self.test_obj.set(resource_id, "Foo2", "BarBar")
        tag_list = self.test_obj.get_all()

        tag1 = find_with_tag_key(tag_list, "Foo2")
        tag2 = find_with_tag_key(tag_list, "Foo21")

        test_runner.assertEqual(tag1["value"], "BarBar")
        test_runner.assertEqual(tag2["value"], "Bar1")

    def test_remove(self, test_runner, resource_id, get_resources_func=None):
        # should be able to remove a tag by resource id
        self.test_obj.set(resource_id, "Foo_remove", "Bar")
        if get_resources_func is not None:
            previous_length = len(get_resources_func(resource_id))
        else:
            previous_length = len(self.test_obj.get_all())

        self.test_obj.remove(resource_id, "Foo_remove")
        # after removing a tag, current_length should be reduced by 1
        if get_resources_func is not None:
            current_length = len(get_resources_func(resource_id))
        else:
            current_length = len(self.test_obj.get_all())

        test_runner.assertEqual(current_length, previous_length - 1)


class TestDeviceTag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.device_tag = cls.balena.models.device.tags
        cls.base_tag_test = BaseTagTest(cls.device_tag, "device")
        # Wipe all apps before every test case.
        cls.helper.wipe_application()
        app, device = cls.helper.create_device()
        cls.app = app
        cls.device = device

    @classmethod
    def tearDownClass(cls):
        # Wipe all apps after every test case.
        cls.helper.wipe_application()

    def test_01_set(self):
        self.base_tag_test.test_set(self, self.device["uuid"])

    def test_02_get_all_by_device(self):
        device_uuid = self.device["uuid"]

        # should retrieve all the tags by uuid
        tags = self.device_tag.get_all_by_device(device_uuid)
        self.base_tag_test.assert_get_all_by_associated_resource(self, tags)

    def test_03_get_all_by_application(self):
        self.base_tag_test.test_get_all_by_application(self, self.device["uuid"], self.app["id"])

    def test_04_get_all(self):
        self.base_tag_test.test_get_all(self, self.device["uuid"])

    def test_05_remove(self):
        self.base_tag_test.test_remove(self, self.device["uuid"])


class TestApplicationTag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.base_tag_test = BaseTagTest(cls.balena.models.application.tags, "application")
        app, device = cls.helper.create_device()
        cls.app = app
        cls.device = device

    @classmethod
    def tearDownClass(cls):
        # Wipe all apps after every test case.
        cls.helper.wipe_application()

    def test_01_get_all_by_application(self):
        self.base_tag_test.test_get_all_by_application(self, type(self).app["id"], type(self).app["id"])

    def test_03_remove(self):
        self.base_tag_test.test_remove(
            self, type(self).app["id"], self.balena.models.application.tags.get_all_by_application
        )


class TestReleaseTag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.release_tag = cls.balena.models.release.tags
        cls.base_tag_test = BaseTagTest(cls.release_tag, "release")
        # Wipe all apps before every test case.
        cls.helper.wipe_application()
        cls.app_info = cls.helper.create_multicontainer_app()

    @classmethod
    def tearDownClass(cls):
        # Wipe all apps after every test case.
        cls.helper.wipe_application()

    def test_01_set(self):
        self.base_tag_test.test_set(self, type(self).app_info["current_release"]["id"])

    def test_02_get_all_by_release(self):
        release_id = type(self).app_info["current_release"]["id"]

        # should retrieve all the tags by uuid
        tags = self.release_tag.get_all_by_release(release_id)
        self.base_tag_test.assert_get_all_by_associated_resource(self, tags)

    def test_03_get_all_by_application(self):
        self.base_tag_test.test_get_all_by_application(
            self,
            type(self).app_info["current_release"]["id"],
            type(self).app_info["app"]["id"],
        )

    def test_04_get_all(self):
        self.base_tag_test.test_get_all(self, type(self).app_info["current_release"]["id"])

    def test_05_remove(self):
        self.base_tag_test.test_remove(self, type(self).app_info["current_release"]["id"])


if __name__ == "__main__":
    unittest.main()
