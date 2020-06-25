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


if __name__ == '__main__':
    unittest.main()
