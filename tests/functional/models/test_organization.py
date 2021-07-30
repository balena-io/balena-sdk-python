import unittest
import json
from datetime import datetime
import sys

from tests.helper import TestHelper

PY2 = sys.version_info[0] == 2

if PY2:
    string_types = basestring
else:
    string_types = str


class TestOrganization(unittest.TestCase):

    helper = None
    balena = None
    test_org_name = 'python_sdk_org_test_{time}'.format(time=datetime.now().strftime("%H_%M_%S"))

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.test_org_admin_role = cls.helper.get_org_admin_role()

    def tearDown(self):
        # Wipe all apps after every test case.
        self.helper.wipe_organization()

    def test_create(self):
        # should be able to create a new organization
        org1 = self.balena.models.organization.create(self.test_org_name)
        self.assertEqual(org1['name'], self.test_org_name)
        self.assertIsInstance(org1['handle'], string_types)

        # should be able to create a new organization with handle
        org2 = self.balena.models.organization.create(self.test_org_name, 'python_sdk_test')
        self.assertEqual(org2['name'], self.test_org_name)
        self.assertEqual(org2['handle'], 'python_sdk_test')

        # should be able to create a new organization with the same name
        org3 = self.balena.models.organization.create(self.test_org_name)
        self.assertEqual(org3['name'], self.test_org_name)
        self.assertNotEqual(org3['handle'], org1['handle'])

    def test_get_all(self):
        # given no non-user organizations, should retrieve only the default org of the user.
        orgs = self.balena.models.organization.get_all()
        self.assertEqual(1, len(orgs))
        self.assertEqual(orgs[0]['handle'], self.helper.credentials['user_id'])

        # given two extra non-user organization, should retrieve all organizations.
        self.balena.models.organization.create(self.test_org_name)
        self.balena.models.organization.create(self.test_org_name)
        orgs = self.balena.models.organization.get_all()
        self.assertEqual(len(orgs), 3)

    def test_get(self):
        # should be rejected if the organization id does not exist and raise balena.exceptions.OrganizationNotFound.
        with self.assertRaises(self.helper.balena_exceptions.OrganizationNotFound) as cm:
            self.balena.models.organization.get('999999999')
        self.assertIn('Organization not found: 999999999', cm.exception.message)

        # should retrieve the initial organization of the user by organization id.
        org = self.balena.models.organization.create(self.test_org_name)
        self.assertEqual(self.balena.models.organization.get(org['id'])['name'], self.test_org_name)

    def test_get_by_handle(self):
        # should be rejected if the organization handle does not exist and raise balena.exceptions.OrganizationNotFound.
        with self.assertRaises(self.helper.balena_exceptions.OrganizationNotFound) as cm:
            self.balena.models.organization.get_by_handle('999999999')
        self.assertIn('Organization not found: 999999999', cm.exception.message)

        # should retrieve the initial organization of the user by organization handle.
        org = self.balena.models.organization.create(self.test_org_name, 'python_sdk_test_handle')
        self.assertEqual(self.balena.models.organization.get_by_handle('python_sdk_test_handle')['id'], org['id'])

    def test_remove(self):
        # should remove an organization by id.
        org = self.balena.models.organization.create(self.test_org_name)
        orgs_count = len(self.balena.models.organization.get_all())
        self.balena.models.organization.remove(org['id'])
        self.assertEqual(len(self.balena.models.organization.get_all()), orgs_count - 1)
    
    def test_invite_create(self):
        org = self.balena.models.organization.create(self.test_org_name)

        # should create and return an organization invite
        invite = self.balena.models.organization.invite.create(org['id'], 'james@resin.io', 'member', 'Python SDK test invite')
        self.assertEqual(invite['message'], 'Python SDK test invite')
        self.assertEqual(invite['is_invited_to__organization']['__id'], org['id'])
        self.balena.models.organization.invite.revoke(invite['id'])

        # should throw an error when role is not found
        # raise balena.exceptions.BalenaOrganizationMembershipRoleNotFound if  role is not found.
        with self.assertRaises(self.helper.balena_exceptions.BalenaOrganizationMembershipRoleNotFound):
            invite = self.balena.models.organization.invite.create(org['id'], 'james@resin.io', 'member1', 'Python SDK test invite')

    def test_invite_get_all(self):
        org = self.balena.models.organization.create(self.test_org_name)

        # shoud return an empty list
        invite_list = self.balena.models.organization.invite.get_all()
        self.assertEqual(0, len(invite_list))

        # shoud return an invite list with length equals 1.
        invite = self.balena.models.organization.invite.create(org['id'], 'james@resin.io', 'member', 'Python SDK test invite')
        invite_list = self.balena.models.organization.invite.get_all()
        self.assertEqual(1, len(invite_list))

    def test_invite_get_all_by_organization(self):
        org = self.balena.models.organization.create(self.test_org_name)

        # shoud return an empty list
        invite_list = self.balena.models.organization.invite.get_all_by_organization(org['id'])
        self.assertEqual(0, len(invite_list))

        # shoud return an invite list with length equals 1.
        invite = self.balena.models.organization.invite.create(org['id'], 'james@resin.io', 'member', 'Python SDK test invite')
        invite_list = self.balena.models.organization.invite.get_all_by_organization(org['id'])
        self.assertEqual(1, len(invite_list))

    def test_membership_get_all_by_organization(self):
        org = self.balena.models.organization.create(self.test_org_name)

        # shoud return only the user's own membership
        memberships = self.balena.models.organization.membership.get_all_by_organization(org['id'])
        self.assertEqual(1, len(memberships))
        self.assertEqual(memberships[0]['user']['__id'], self.balena.auth.get_user_id())
        self.assertEqual(memberships[0]['is_member_of__organization']['__id'], org['id'])
        self.assertEqual(memberships[0]['organization_membership_role']['__id'], self.test_org_admin_role['id'])


if __name__ == '__main__':
    unittest.main()
