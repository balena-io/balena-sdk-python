import unittest
from datetime import datetime

from tests.helper import TestHelper


class TestApplication(unittest.TestCase):
    helper = None
    balena = None
    app = None
    app1 = None
    device = None

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.organization_name = cls.helper.default_organization["name"]
        cls.balena = cls.helper.balena
        cls.org_handle = cls.helper.default_organization["handle"]
        cls.app_slug = f"{cls.org_handle}/FooBar"

        # Wipe all apps before the tests run.
        cls.helper.wipe_application()

    @classmethod
    def tearDownClass(cls):
        # Wipe all apps after the tests run.
        cls.helper.wipe_application()
        cls.helper.wipe_organization()

    def test_01_get_all_empty(self):
        # given no applications, it should return empty list.
        self.assertEqual(self.balena.models.application.get_all(), [])

    def test_02_has_any_empty(self):
        # given no applications, it should return false.
        self.assertFalse(self.balena.models.application.has_any())

    def test_03_create(self):
        # should be rejected if the device type is invalid
        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.application.create("FooBar", "Foo", self.helper.default_organization["id"])

        # should be rejected if the name has less than four characters
        with self.assertRaises(Exception) as cm:
            self.balena.models.application.create("Fo", "raspberry-pi2", self.helper.default_organization["id"])
        self.assertIn(
            "It is necessary that each application has an app name that has a Length"
            " (Type) that is greater than or equal to 4 and is less than or equal"
            " to 100",
            cm.exception.message,
        )

        # should be able to create an application
        type(self).app = self.balena.models.application.create(
            "FooBar", "raspberry-pi2", self.helper.default_organization["id"]
        )
        self.assertEqual(type(self).app["app_name"], "FooBar")

        # should be able to create an application with a application class
        type(self).app1 = self.balena.models.application.create(
            "FooBar1", "raspberrypi3", self.helper.default_organization["id"], "block"
        )
        self.assertEqual(type(self).app1["app_name"], "FooBar1")
        self.assertEqual(type(self).app1["is_of__class"], "block")

    def test_04_get_all(self):
        # given there is an application, it should return a list with length 2.
        all_apps = self.balena.models.application.get_all()
        self.assertEqual(len(all_apps), 2)
        self.assertNotEqual(all_apps[0]["app_name"], all_apps[1]["app_name"])

    def test_05_get(self):

        # raise balena.exceptions.ApplicationNotFound if no application found.
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.get("AppNotExist")

        # found an application, it should return an application with matched name.
        self.assertEqual(self.balena.models.application.get(self.app_slug)["app_name"], "FooBar")

    def test_06_get_by_owner(self):
        # raise balena.exceptions.ApplicationNotFound if no application found.
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.get_by_owner("AppNotExist", self.helper.credentials["user_id"])

        # found an application, it should return an application with matched name.
        self.assertEqual(
            self.balena.models.application.get_by_owner("FooBar", self.helper.default_organization["handle"])[
                "app_name"
            ],
            "FooBar",
        )

        # should not find the created application with a different username
        with self.assertRaises(Exception) as cm:
            self.balena.models.application.get_by_owner("FooBar", "random_username")
        self.assertIn("Application not found: random_username/foobar", cm.exception.message)

    def test_07_has(self):
        # should be true if the application name exists, otherwise it should return false.

        self.assertFalse(self.balena.models.application.has("AppNotExist"))
        self.assertTrue(self.balena.models.application.has(self.app_slug))

    def test_08_has_any(self):
        # should return true if at least one application exists.
        self.assertTrue(self.balena.models.application.has_any())

    def test_09_get_by_id(self):
        # raise balena.exceptions.ApplicationNotFound if no application found.
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.get(1)

        # found an application, it should return an application with matched id.
        app = type(self).app
        self.assertEqual(self.balena.models.application.get(app["id"])["id"], app["id"])

    def test_10_remove(self):
        # should be able to remove an existing application by name.
        self.assertEqual(len(self.balena.models.application.get_all()), 2)
        self.balena.models.application.remove(f"{self.org_handle}/FooBar1")
        self.assertEqual(len(self.balena.models.application.get_all()), 1)

    def test_11_generate_provisioning_key(self):
        # should be rejected if the application id does not exist.
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.generate_provisioning_key("app/notexists")

        # should be able to generate a provisioning key by app id.
        app = type(self).app
        key = self.balena.models.application.generate_provisioning_key(app["id"])
        self.assertEqual(len(key), 32)

        # should be able to generate a provisioning key with key name and description by app id.
        key = self.balena.models.application.generate_provisioning_key(
            app["id"], "FooBar Key", "FooBar Key Description"
        )
        self.assertEqual(len(key), 32)

    def test_14_enable_device_urls(self):
        # should enable the device url for the applications devices.
        app = type(self).app
        device = self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())
        type(self).device = device
        self.balena.models.application.enable_device_urls(app["id"])
        self.assertTrue(self.balena.models.device.has_device_url(device["uuid"]))

    def test_15_disable_device_urls(self):
        # should disable the device url for the applications devices.
        app = type(self).app
        device = type(self).device
        self.balena.models.application.enable_device_urls(app["id"])
        self.balena.models.application.disable_device_urls(app["id"])
        self.assertFalse(self.balena.models.device.has_device_url(device["uuid"]))

    def test_16_grant_support_access(self):
        app = type(self).app
        # should throw an error if the expiry timestamp is in the past.
        expiry_timestamp = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) - 10000)
        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.application.grant_support_access(app["id"], expiry_timestamp)

        # should grant support access until the specified time.
        expiry_time = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) + 3600 * 1000)
        self.balena.models.application.grant_support_access(app["id"], expiry_time)

        support_date = datetime.strptime(
            self.balena.models.application.get(self.app_slug)["is_accessible_by_support_until__date"],
            "%Y-%m-%dT%H:%M:%S.%fZ",
        )
        self.assertEqual(self.helper.datetime_to_epoch_ms(support_date), expiry_time)

    def test_17_revoke_support_access(self):
        # should revoke support access.
        app = type(self).app
        expiry_time = int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000 + 3600 * 1000)
        self.balena.models.application.grant_support_access(app["id"], expiry_time)
        self.balena.models.application.revoke_support_access(app["id"])

        app = self.balena.models.application.get(self.app_slug)
        self.assertIsNone(app["is_accessible_by_support_until__date"])

    def test_18_will_track_new_releases(self):
        # should be configured to track new releases by default.
        app_info = self.helper.create_app_with_releases(app_name="FooBarWithReleases")
        type(self).app_info = app_info
        self.assertTrue(self.balena.models.application.will_track_new_releases(app_info["app"]["id"]))

    def test_19_get_target_release_hash(self):
        # should retrieve the commit hash of the current release.
        app_info = type(self).app_info
        self.assertEqual(
            self.balena.models.application.get_target_release_hash(app_info["app"]["id"]),
            app_info["current_release"]["commit"],
        )

    def test_21_pin_to_release(self):
        # should set the application to specific release & disable latest release tracking
        app_info = type(self).app_info
        self.balena.models.application.pin_to_release(app_info["app"]["id"], app_info["old_release"]["commit"])
        self.assertEqual(
            self.balena.models.application.get_target_release_hash(app_info["app"]["id"]),
            app_info["old_release"]["commit"],
        )
        self.assertFalse(self.balena.models.application.will_track_new_releases(app_info["app"]["id"]))
        self.assertFalse(self.balena.models.application.is_tracking_latest_release(app_info["app"]["id"]))

    def test_22_track_latest_release(self):
        # should re-enable latest release tracking
        app_info = type(self).app_info
        self.balena.models.application.pin_to_release(app_info["app"]["id"], app_info["old_release"]["commit"])
        self.assertEqual(
            self.balena.models.application.get_target_release_hash(app_info["app"]["id"]),
            app_info["old_release"]["commit"],
        )
        self.assertFalse(self.balena.models.application.will_track_new_releases(app_info["app"]["id"]))
        self.assertFalse(self.balena.models.application.is_tracking_latest_release(app_info["app"]["id"]))
        self.balena.models.application.track_latest_release(app_info["app"]["id"])
        self.assertEqual(
            self.balena.models.application.get_target_release_hash(app_info["app"]["id"]),
            app_info["current_release"]["commit"],
        )
        self.assertTrue(self.balena.models.application.will_track_new_releases(app_info["app"]["id"]))
        self.assertTrue(self.balena.models.application.is_tracking_latest_release(app_info["app"]["id"]))

    def test_23_get_dashboard_url(self):
        # raise balena.exceptions.InvalidParameter if application id is not a number.
        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.application.get_dashboard_url("1476418a")

        # should return the respective dashboard url when an application id is provided.
        url = self.balena.models.application.get_dashboard_url("1476418")
        self.assertEqual(url, "https://dashboard.balena-cloud.com/apps/1476418")

    def test_24_invite_get_all_empty(self):
        # shoud return an empty list
        invite_list = self.balena.models.application.invite.get_all()
        self.assertEqual(0, len(invite_list))

    def test_25_invite_create(self):
        app = type(self).app

        # should create and return an application invite
        invite = self.balena.models.application.invite.create(
            app["id"], {
                "invitee": self.helper.credentials["email"],
                "roleName": "developer",
                "message": "Python SDK test invite"
            }
        )
        type(self).invite = invite
        self.assertEqual(invite["message"], "Python SDK test invite")
        self.assertEqual(invite["is_invited_to__application"]["__id"], app["id"])

        # should throw an error when role is not found
        # raise balena.exceptions.BalenaApplicationMembershipRoleNotFound if  role is not found.
        with self.assertRaises(self.helper.balena_exceptions.BalenaApplicationMembershipRoleNotFound):
            self.balena.models.application.invite.create(
                app["id"], {
                    "invitee": self.helper.credentials["email"],
                    "roleName": "developer1",
                    "message": "Python SDK test invite"
                }
            )

    def test_26_invite_get_all(self):
        invite_list = self.balena.models.application.invite.get_all()
        self.assertEqual(1, len(invite_list))

    def test_27_invite_get_all_by_application(self):
        app = type(self).app

        invite_list = self.balena.models.application.invite.get_all_by_application(app["id"])
        self.assertEqual(1, len(invite_list))

    def test_28_invite_revoke(self):
        # should create and return an application invite
        self.balena.models.application.invite.revoke(type(self).invite["id"])
        invite_list = self.balena.models.application.invite.get_all()
        self.assertEqual(0, len(invite_list))

    def test_29_membership_get_all_empty(self):
        # shoud return an empty list
        membership_list = self.balena.models.application.membership.get_all()
        self.assertEqual(0, len(membership_list))

    def test_30_membership_get_all_by_application_empty(self):
        app = type(self).app

        # shoud return an empty list
        membership_list = self.balena.models.application.membership.get_all_by_application(app["id"])
        self.assertEqual(0, len(membership_list))

    def test_31_membership_create(self):
        app = type(self).app

        # should create and return an application membership
        membership = self.balena.models.application.membership.create(app["id"], "device_tester1")
        type(self).membership = membership
        self.assertEqual(membership["is_member_of__application"]["__id"], app["id"])

        # should throw an error when role is not found
        # raise balena.exceptions.BalenaApplicationMembershipRoleNotFound if  role is not found.
        with self.assertRaises(self.helper.balena_exceptions.BalenaApplicationMembershipRoleNotFound):
            self.balena.models.application.membership.create(app["id"], self.helper.credentials["email"], "developer1")

    def test_32_membership_get_all(self):
        membership_list = self.balena.models.application.membership.get_all()
        self.assertEqual(1, len(membership_list))

    def test_33_membership_get_all_by_application(self):
        app = type(self).app

        membership_list = self.balena.models.application.membership.get_all_by_application(app["id"])
        self.assertEqual(1, len(membership_list))

    def test_34_membership_remove(self):
        # should create and return an application membership
        self.balena.models.application.membership.remove(type(self).membership["id"])
        membership_list = self.balena.models.application.membership.get_all()
        self.assertEqual(0, len(membership_list))


if __name__ == "__main__":
    unittest.main()
