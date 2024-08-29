import unittest
from datetime import datetime

from tests.helper import TestHelper


class TestApplication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.org_handle = cls.helper.default_organization["handle"]
        cls.org_id = cls.helper.default_organization["id"]
        cls.app_slug = f"{cls.org_handle}/FooBar"
        cls.helper.wipe_application()

    @classmethod
    def tearDownClass(cls):
        cls.helper.wipe_application()
        cls.helper.wipe_organization()

    def test_01_get_all_empty(self):
        self.assertEqual(self.balena.models.application.get_all(), [])

    def test_02_has_any_empty(self):
        self.assertFalse(self.balena.models.application.has_any())

    def test_03_create(self):
        with self.assertRaises(self.helper.balena_exceptions.InvalidDeviceType):
            self.balena.models.application.create("FooBar", "Foo", self.helper.default_organization["id"])

        with self.assertRaises(Exception) as cm:
            self.balena.models.application.create("Fo", "raspberry-pi2", self.helper.default_organization["id"])
        self.assertIn(
            "It is necessary that each application has an app name that has a Length"
            " (Type) that is greater than or equal to 4 and is less than or equal"
            " to 100",
            cm.exception.message,  # type: ignore
        )

        TestApplication.app = self.balena.models.application.create(
            "FooBar", "raspberry-pi2", self.helper.default_organization["id"]
        )
        self.assertEqual(TestApplication.app["app_name"], "FooBar")

        app1 = self.balena.models.application.create(
            "FooBar1", "raspberrypi3", self.helper.default_organization["id"], "block"
        )
        self.assertEqual(app1["app_name"], "FooBar1")
        self.assertEqual(app1["is_of__class"], "block")

    def test_04_get_all(self):
        all_apps = self.balena.models.application.get_all()
        self.assertEqual(len(all_apps), 2)
        self.assertNotEqual(all_apps[0]["app_name"], all_apps[1]["app_name"])

    def test_05_get(self):
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.get("AppNotExist")

        self.assertEqual(self.balena.models.application.get(self.app_slug)["app_name"], "FooBar")

    def test_06_get_all_by_organization(self):
        with self.assertRaises(self.helper.balena_exceptions.OrganizationNotFound):
            self.balena.models.application.get_all_by_organization("OrgNotExist")

        self.assertEqual(
            self.balena.models.application.get_all_by_organization(self.org_handle)[0]["app_name"], "FooBar"
        )

        self.assertEqual(
            self.balena.models.application.get_all_by_organization(self.org_id)[0]["app_name"], "FooBar"
        )

    def test_06_get_by_owner(self):
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.get_by_owner("AppNotExist", self.helper.credentials["user_id"])

        self.assertEqual(
            self.balena.models.application.get_by_owner("FooBar", self.helper.default_organization["handle"])[
                "app_name"
            ],
            "FooBar",
        )

        with self.assertRaises(Exception) as cm:
            self.balena.models.application.get_by_owner("FooBar", "random_username")
        self.assertIn("Application not found: random_username/foobar", cm.exception.message)  # type: ignore

    def test_07_has(self):
        self.assertFalse(self.balena.models.application.has("AppNotExist"))
        self.assertTrue(self.balena.models.application.has(self.app_slug))

    def test_08_has_any(self):
        self.assertTrue(self.balena.models.application.has_any())

    def test_09_get_by_id(self):
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.get(1)

        app = TestApplication.app
        self.assertEqual(self.balena.models.application.get(app["id"])["id"], app["id"])

    def test_10_remove(self):
        self.assertEqual(len(self.balena.models.application.get_all()), 2)
        self.balena.models.application.remove(f"{self.org_handle}/FooBar1")
        self.assertEqual(len(self.balena.models.application.get_all()), 1)

    def test_11_generate_provisioning_key(self):
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.application.generate_provisioning_key("app/notexists")

        app = TestApplication.app
        key = self.balena.models.application.generate_provisioning_key(app["id"])
        self.assertEqual(len(key), 32)

        key = self.balena.models.application.generate_provisioning_key(
            app["id"], "FooBar Key", "FooBar Key Description"
        )
        self.assertEqual(len(key), 32)

    def test_14_enable_device_urls(self):
        app = TestApplication.app
        device = self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())
        TestApplication.device = device
        self.balena.models.application.enable_device_urls(app["id"])
        self.assertTrue(self.balena.models.device.has_device_url(device["uuid"]))

    def test_15_disable_device_urls(self):
        app = TestApplication.app
        device = TestApplication.device
        self.balena.models.application.enable_device_urls(app["id"])
        self.balena.models.application.disable_device_urls(app["id"])
        self.assertFalse(self.balena.models.device.has_device_url(device["uuid"]))

    def test_16_grant_support_access(self):
        app = TestApplication.app
        expiry_timestamp = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) - 10000)
        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.application.grant_support_access(app["id"], expiry_timestamp)

        expiry_time = int(self.helper.datetime_to_epoch_ms(datetime.utcnow()) + 3600 * 1000)
        self.balena.models.application.grant_support_access(app["id"], expiry_time)

        support_date = datetime.strptime(
            self.balena.models.application.get(self.app_slug)["is_accessible_by_support_until__date"],
            "%Y-%m-%dT%H:%M:%S.%fZ",
        )
        self.assertEqual(self.helper.datetime_to_epoch_ms(support_date), expiry_time)

    def test_17_revoke_support_access(self):
        app = TestApplication.app
        expiry_time = int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000 + 3600 * 1000)
        self.balena.models.application.grant_support_access(app["id"], expiry_time)
        self.balena.models.application.revoke_support_access(app["id"])

        app = self.balena.models.application.get(self.app_slug)
        self.assertIsNone(app["is_accessible_by_support_until__date"])

    def test_18_will_track_new_releases(self):
        app_info = self.helper.create_app_with_releases(app_name="FooBarWithReleases")
        TestApplication.app_info = app_info
        self.assertTrue(self.balena.models.application.will_track_new_releases(app_info["app"]["id"]))

    def test_19_get_target_release_hash(self):
        app_info = TestApplication.app_info
        self.assertEqual(
            self.balena.models.application.get_target_release_hash(app_info["app"]["id"]),
            app_info["current_release"]["commit"],
        )

    def test_21_pin_to_release(self):
        app_info = TestApplication.app_info
        self.balena.models.application.pin_to_release(app_info["app"]["id"], app_info["old_release"]["commit"])
        self.assertEqual(
            self.balena.models.application.get_target_release_hash(app_info["app"]["id"]),
            app_info["old_release"]["commit"],
        )
        self.assertFalse(self.balena.models.application.will_track_new_releases(app_info["app"]["id"]))
        self.assertFalse(self.balena.models.application.is_tracking_latest_release(app_info["app"]["id"]))

    def test_22_track_latest_release(self):
        app_info = TestApplication.app_info
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
        with self.assertRaises(self.helper.balena_exceptions.InvalidParameter):
            self.balena.models.application.get_dashboard_url("1476418a")  # type: ignore

        url = self.balena.models.application.get_dashboard_url("1476418")  # type: ignore
        self.assertEqual(url, "https://dashboard.balena-cloud.com/apps/1476418")

    def test_24_invite_get_all_empty(self):
        invite_list = self.balena.models.application.invite.get_all()
        self.assertEqual(0, len(invite_list))

    def test_25_invite_create(self):
        app = TestApplication.app
        invite = self.balena.models.application.invite.create(
            app["id"],
            {"invitee": self.helper.credentials["email"], "roleName": "developer", "message": "Python SDK test invite"},
        )
        TestApplication.invite = invite
        self.assertEqual(invite["message"], "Python SDK test invite")
        self.assertEqual(invite["is_invited_to__application"]["__id"], app["id"])

        with self.assertRaises(self.helper.balena_exceptions.BalenaApplicationMembershipRoleNotFound):
            self.balena.models.application.invite.create(
                app["id"],
                {
                    "invitee": self.helper.credentials["email"],
                    "roleName": "developer1",  # type: ignore
                    "message": "Python SDK test invite",
                },
            )

    def test_26_invite_get_all(self):
        invite_list = self.balena.models.application.invite.get_all()
        self.assertEqual(1, len(invite_list))

    def test_27_invite_get_all_by_application(self):
        app = TestApplication.app

        invite_list = self.balena.models.application.invite.get_all_by_application(app["id"])
        self.assertEqual(1, len(invite_list))

    def test_28_invite_revoke(self):
        self.balena.models.application.invite.revoke(TestApplication.invite["id"])
        invite_list = self.balena.models.application.invite.get_all()
        self.assertEqual(0, len(invite_list))

    def test_29_membership_get_all_empty(self):
        membership_list = self.balena.models.application.membership.get_all()
        self.assertEqual(0, len(membership_list))

    def test_30_membership_get_all_by_application_empty(self):
        app = TestApplication.app
        membership_list = self.balena.models.application.membership.get_all_by_application(app["id"])
        self.assertEqual(0, len(membership_list))

    def test_31_membership_create(self):
        app = TestApplication.app
        membership = self.balena.models.application.membership.create(app["id"], "device_tester1")
        TestApplication.membership = membership
        self.assertEqual(membership["is_member_of__application"]["__id"], app["id"])

        with self.assertRaises(self.helper.balena_exceptions.BalenaApplicationMembershipRoleNotFound):
            self.balena.models.application.membership.create(
                app["id"], self.helper.credentials["email"], "developer1"  # type: ignore
            )

    def test_32_membership_get_all(self):
        membership_list = self.balena.models.application.membership.get_all()
        self.assertEqual(1, len(membership_list))

    def test_33_membership_get_all_by_application(self):
        app = TestApplication.app
        membership_list = self.balena.models.application.membership.get_all_by_application(app["id"])
        self.assertEqual(1, len(membership_list))

    def test_34_membership_remove(self):
        self.balena.models.application.membership.remove(TestApplication.membership["id"])
        membership_list = self.balena.models.application.membership.get_all()
        self.assertEqual(0, len(membership_list))


if __name__ == "__main__":
    unittest.main()
