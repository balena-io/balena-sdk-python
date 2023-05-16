import unittest
from datetime import datetime

from tests.helper import TestHelper


class TestOrganization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.test_org_admin_role = cls.helper.get_org_admin_role()
        time = datetime.now().strftime("%H_%M_%S")
        cls.test_org_handle = f"python_sdk_org_test_{time}"
        cls.test_org_name = cls.test_org_handle + " name"
        cls.test_org_custom_handle = cls.test_org_handle + "_python_sdk_test"

        # Wipe all apps before the tests run.
        cls.helper.wipe_organization()

    @classmethod
    def tearDownClass(cls):
        # Wipe all apps after the tests run.
        cls.helper.wipe_organization()

    def test_create(self):
        # should be able to create a new organization
        TestOrganization.org1 = self.balena.models.organization.create(self.test_org_name)
        self.assertEqual(TestOrganization.org1["name"], self.test_org_name)
        self.assertIsInstance(TestOrganization.org1["handle"], str)

        # should be able to create a new organization with handle
        TestOrganization.org2 = self.balena.models.organization.create(
            self.test_org_name, self.test_org_custom_handle
        )
        self.assertEqual(TestOrganization.org2["name"], self.test_org_name)
        self.assertEqual(TestOrganization.org2["handle"], self.test_org_custom_handle)

        # should be able to create a new organization with the same name
        TestOrganization.org3 = self.balena.models.organization.create(self.test_org_name)
        self.assertEqual(TestOrganization.org3["name"], self.test_org_name)
        self.assertNotEqual(TestOrganization.org3["handle"], TestOrganization.org1["handle"])

    def test_get_all(self):
        # given three extra non-user organization, should retrieve all organizations.
        orgs = self.balena.models.organization.get_all()
        orgs = sorted(orgs, key=lambda k: k["created_at"])
        self.assertEqual(len(orgs), 4)
        self.assertEqual(orgs[0]["handle"], self.helper.credentials["user_id"])
        self.assertEqual(orgs[1]["name"], self.test_org_name)
        self.assertEqual(orgs[2]["name"], self.test_org_name)
        self.assertEqual(orgs[2]["handle"], self.test_org_custom_handle)
        self.assertEqual(orgs[3]["name"], self.test_org_name)

    def test_get(self):
        # should be rejected if the organization id does not exist and raise balena.exceptions.OrganizationNotFound.
        with self.assertRaises(
            self.helper.balena_exceptions.OrganizationNotFound
        ) as cm:
            self.balena.models.organization.get("999999999")
        self.assertIn("Organization not found: 999999999", cm.exception.message)

        org = self.balena.models.organization.get(TestOrganization.org2["id"])
        self.assertEqual(org["handle"], self.test_org_custom_handle)
        self.assertEqual(org["name"], self.test_org_name)
        self.assertEqual(
            self.balena.models.organization.get(self.test_org_custom_handle)["id"],
            org["id"],
        )

    def test_remove(self):
        # should remove an organization by id.
        orgs_count = len(self.balena.models.organization.get_all())
        self.balena.models.organization.remove(TestOrganization.org3["id"])
        self.assertEqual(len(self.balena.models.organization.get_all()), orgs_count - 1)

    def test_invite_create(self):
        # should create and return an organization invite
        invite = self.balena.models.organization.invite.create(
            TestOrganization.org1["id"],
            self.helper.credentials["email"],
            "member",
            "Python SDK test invite",
        )
        self.assertEqual(invite["message"], "Python SDK test invite")
        self.assertEqual(
            invite["is_invited_to__organization"]["__id"], TestOrganization.org1["id"]
        )
        self.balena.models.organization.invite.revoke(invite["id"])

        # should throw an error when role is not found
        # raise balena.exceptions.BalenaOrganizationMembershipRoleNotFound if  role is not found.
        with self.assertRaises(
            self.helper.balena_exceptions.BalenaOrganizationMembershipRoleNotFound
        ):
            invite = self.balena.models.organization.invite.create(
                TestOrganization.org1["id"],
                self.helper.credentials["email"],
                "member1",
                "Python SDK test invite",
            )

    def test_invite_get_all(self):
        # shoud return an empty list
        invite_list = self.balena.models.organization.invite.get_all()
        self.assertEqual(0, len(invite_list))

        # shoud return an invite list with length equals 1.
        self.balena.models.organization.invite.create(
            TestOrganization.org1["id"],
            self.helper.credentials["email"],
            "member",
            "Python SDK test invite",
        )
        invite_list = self.balena.models.organization.invite.get_all()
        self.assertEqual(1, len(invite_list))

    def test_invite_get_all_by_organization(self):
        invite_list = self.balena.models.organization.invite.get_all_by_organization(
            TestOrganization.org1["id"]
        )
        self.assertEqual(1, len(invite_list))

    def test_membership_get_all_by_organization(self):
        # shoud return only the user's own membership
        memberships = (
            self.balena.models.organization.membership.get_all_by_organization(
                TestOrganization.org1["id"]
            )
        )
        self.assertEqual(1, len(memberships))
        self.assertEqual(memberships[0]["user"]["__id"], self.balena.auth.get_user_id())
        self.assertEqual(
            memberships[0]["is_member_of__organization"]["__id"], TestOrganization.org1["id"]
        )
        self.assertEqual(
            memberships[0]["organization_membership_role"]["__id"],
            self.test_org_admin_role["id"],
        )

    def test_membership_tags(self):
        org_id = TestOrganization.org1["id"]
        memberships = (
            self.balena.models.organization.membership.get_all_by_organization(org_id)
        )
        membership_id = memberships[0]["id"]

        membership_tag_model = self.balena.models.organization.membership.tag
        self.assertEqual(0, len(membership_tag_model.get_all_by_organization(org_id)))
        self.assertEqual(
            0,
            len(membership_tag_model.get_all_by_organization_membership(membership_id)),
        )

        membership_tag_model.set(membership_id, "test", "v1")
        self.__assert_tags_changed(org_id, membership_id, "test", "v1")

        membership_tag_model.set(membership_id, "test", "v2")
        self.__assert_tags_changed(org_id, membership_id, "test", "v2")
        self.__assert_tags_changed(org_id, membership_id, "test2", None)

        membership_tag_model.remove(membership_id, "test")
        self.__assert_tags_changed(org_id, membership_id, "test", None)

    def __assert_tags_changed(self, org_id, membership_id, key, value):
        membership_tag_model = self.balena.models.organization.membership.tag

        if value is not None:
            self.assertEqual(1, len(membership_tag_model.get_all_by_organization(org_id)))
            self.assertEqual(
                1,
                len(membership_tag_model.get_all_by_organization_membership(membership_id)),
            )

        self.assertEqual(membership_tag_model.get(membership_id, key), value)

        if value is not None:
            self.assertEqual(
                membership_tag_model.get_all_by_organization(org_id)[0].get("value"),
                value,
            )
            self.assertEqual(
                membership_tag_model.get_all_by_organization_membership(membership_id)[
                    0
                ].get("value"),
                value,
            )


if __name__ == "__main__":
    unittest.main()
