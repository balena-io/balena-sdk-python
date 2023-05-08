import unittest
from datetime import datetime

from tests.helper import TestHelper


class TestOrganization(unittest.TestCase):
    helper = None
    balena = None
    test_org_handle = "python_sdk_org_test_{time}".format(time=datetime.now().strftime("%H_%M_%S"))
    test_org_name = test_org_handle + " name"
    test_org_custom_handle = test_org_handle + "_python_sdk_test"
    org1 = None
    org2 = None
    org3 = None

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.test_org_admin_role = cls.helper.get_org_admin_role()
        # Wipe all apps before the tests run.
        cls.helper.wipe_organization()

    @classmethod
    def tearDownClass(cls):
        # Wipe all apps after the tests run.
        cls.helper.wipe_organization()

    def test_create(self):
        # should be able to create a new organization
        type(self).org1 = self.balena.models.organization.create(self.test_org_name)
        self.assertEqual(type(self).org1["name"], self.test_org_name)
        self.assertIsInstance(type(self).org1["handle"], str)

        # should be able to create a new organization with handle
        type(self).org2 = self.balena.models.organization.create(self.test_org_name, self.test_org_custom_handle)
        self.assertEqual(type(self).org2["name"], self.test_org_name)
        self.assertEqual(type(self).org2["handle"], self.test_org_custom_handle)

        # should be able to create a new organization with the same name
        type(self).org3 = self.balena.models.organization.create(self.test_org_name)
        self.assertEqual(type(self).org3["name"], self.test_org_name)
        self.assertNotEqual(type(self).org3["handle"], type(self).org1["handle"])

    def test_get_all(self):
        # given three extra non-user organization, should retrieve all organizations.
        orgs = self.balena.models.organization.get_all()
        print(orgs)
        orgs = sorted(orgs, key=lambda k: k["created_at"])
        self.assertEqual(len(orgs), 4)
        self.assertEqual(orgs[0]["handle"], self.helper.credentials["user_id"])
        self.assertEqual(orgs[1]["name"], self.test_org_name)
        self.assertEqual(orgs[2]["name"], self.test_org_name)
        self.assertEqual(orgs[2]["handle"], self.test_org_custom_handle)
        self.assertEqual(orgs[3]["name"], self.test_org_name)

    def test_get(self):
        # should be rejected if the organization id does not exist and raise balena.exceptions.OrganizationNotFound.
        with self.assertRaises(self.helper.balena_exceptions.OrganizationNotFound) as cm:
            self.balena.models.organization.get("999999999")
        self.assertIn("Organization not found: 999999999", cm.exception.message)

        org = self.balena.models.organization.get(type(self).org2["id"])
        self.assertEqual(org["handle"], self.test_org_custom_handle)
        self.assertEqual(org["name"], self.test_org_name)

    def test_get_by_handle(self):
        # should be rejected if the organization handle does not exist and raise balena.exceptions.OrganizationNotFound.
        with self.assertRaises(self.helper.balena_exceptions.OrganizationNotFound) as cm:
            self.balena.models.organization.get_by_handle("999999999")
        self.assertIn("Organization not found: 999999999", cm.exception.message)

        self.assertEqual(
            self.balena.models.organization.get_by_handle(self.test_org_custom_handle)["id"],
            type(self).org2["id"],
        )

    def test_remove(self):
        # should remove an organization by id.
        orgs_count = len(self.balena.models.organization.get_all())
        self.balena.models.organization.remove(type(self).org3["id"])
        self.assertEqual(len(self.balena.models.organization.get_all()), orgs_count - 1)

    def test_invite_create(self):
        # should create and return an organization invite
        invite = self.balena.models.organization.invite.create(
            type(self).org1["id"], self.helper.credentials["email"], "member", "Python SDK test invite"
        )
        self.assertEqual(invite["message"], "Python SDK test invite")
        self.assertEqual(invite["is_invited_to__organization"]["__id"], type(self).org1["id"])
        self.balena.models.organization.invite.revoke(invite["id"])

        # should throw an error when role is not found
        # raise balena.exceptions.BalenaOrganizationMembershipRoleNotFound if  role is not found.
        with self.assertRaises(self.helper.balena_exceptions.BalenaOrganizationMembershipRoleNotFound):
            invite = self.balena.models.organization.invite.create(
                type(self).org1["id"],
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
            type(self).org1["id"], self.helper.credentials["email"], "member", "Python SDK test invite"
        )
        invite_list = self.balena.models.organization.invite.get_all()
        self.assertEqual(1, len(invite_list))

    def test_invite_get_all_by_organization(self):
        invite_list = self.balena.models.organization.invite.get_all_by_organization(type(self).org1["id"])
        self.assertEqual(1, len(invite_list))

    def test_membership_get_all_by_organization(self):
        # shoud return only the user's own membership
        memberships = self.balena.models.organization.membership.get_all_by_organization(type(self).org1["id"])
        self.assertEqual(1, len(memberships))
        self.assertEqual(memberships[0]["user"]["__id"], self.balena.auth.get_user_id())
        self.assertEqual(memberships[0]["is_member_of__organization"]["__id"], type(self).org1["id"])
        self.assertEqual(
            memberships[0]["organization_membership_role"]["__id"],
            self.test_org_admin_role["id"],
        )


if __name__ == "__main__":
    unittest.main()
