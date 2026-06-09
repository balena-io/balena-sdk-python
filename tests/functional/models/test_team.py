import unittest
from datetime import datetime

from tests.helper import TestHelper


class TestTeam(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.org_id = cls.helper.default_organization["id"]
        cls.org_handle = cls.helper.default_organization["handle"]
        cls.member_username = cls.helper.member_credentials["member_username"]
        time = datetime.now().strftime("%H_%M_%S")
        cls.test_team_name = f"python_sdk_team_test_{time}"
        cls.helper.wipe_application()

    @classmethod
    def tearDownClass(cls):
        teams = cls.balena.models.team.get_all_by_organization(cls.org_id)
        for team in teams:
            if cls.test_team_name in team["name"]:
                cls.balena.models.team.remove(team["id"])
        cls.helper.wipe_application()

    def test_01_get_all_by_organization_empty(self):
        teams = self.balena.models.team.get_all_by_organization(self.org_id)
        self.assertEqual(teams, [])

    def test_02_get_all_by_organization_not_found(self):
        with self.assertRaises(self.helper.balena_exceptions.OrganizationNotFound):
            self.balena.models.team.get_all_by_organization(999999)

    def test_03_create_with_org_id(self):
        team_name = self.test_team_name + "_id"
        TestTeam.team1 = self.balena.models.team.create(self.org_id, team_name)
        self.assertEqual(TestTeam.team1["name"], team_name)
        self.assertIn("id", TestTeam.team1)

    def test_04_create_with_org_handle(self):
        team_name = self.test_team_name + "_handle"
        TestTeam.team2 = self.balena.models.team.create(self.org_handle, team_name)
        self.assertEqual(TestTeam.team2["name"], team_name)

    def test_05_get_all_by_organization(self):
        teams = self.balena.models.team.get_all_by_organization(self.org_id)
        team_ids = [t["id"] for t in teams]
        self.assertIn(TestTeam.team1["id"], team_ids)
        self.assertIn(TestTeam.team2["id"], team_ids)

    def test_06_get_all_by_organization_by_handle(self):
        teams = self.balena.models.team.get_all_by_organization(self.org_handle)
        team_ids = [t["id"] for t in teams]
        self.assertIn(TestTeam.team1["id"], team_ids)
        self.assertIn(TestTeam.team2["id"], team_ids)

    def test_07_get(self):
        team = self.balena.models.team.get(TestTeam.team1["id"])
        self.assertEqual(team["id"], TestTeam.team1["id"])
        self.assertEqual(team["name"], TestTeam.team1["name"])

    def test_08_get_with_options(self):
        team = self.balena.models.team.get(
            TestTeam.team1["id"],
            {"$expand": {"belongs_to__organization": {"$select": "handle"}}},
        )
        self.assertEqual(team["belongs_to__organization"][0]["handle"], self.org_handle)

    def test_09_get_not_found(self):
        with self.assertRaises(self.helper.balena_exceptions.TeamNotFound) as cm:
            self.balena.models.team.get(999999)
        self.assertIn("Team not found: 999999", cm.exception.message)

    def test_10_rename(self):
        new_name = self.test_team_name + "_renamed"
        self.balena.models.team.rename(TestTeam.team1["id"], new_name)
        team = self.balena.models.team.get(TestTeam.team1["id"])
        self.assertEqual(team["name"], new_name)
        TestTeam.team1["name"] = new_name

    def test_11_rename_duplicate(self):
        with self.assertRaises(Exception) as cm:
            self.balena.models.team.rename(TestTeam.team1["id"], TestTeam.team2["name"])
        self.assertIn("A team with this name already exists in the organization", str(cm.exception))

    def test_12_rename_not_found(self):
        with self.assertRaises(self.helper.balena_exceptions.TeamNotFound) as cm:
            self.balena.models.team.rename(999999, "any_name")
        self.assertIn("Team not found: 999999", cm.exception.message)

    def test_13_remove(self):
        self.balena.models.team.remove(TestTeam.team1["id"])
        self.balena.models.team.remove(TestTeam.team2["id"])
        teams = self.balena.models.team.get_all_by_organization(self.org_id)
        team_ids = [t["id"] for t in teams]
        self.assertNotIn(TestTeam.team1["id"], team_ids)
        self.assertNotIn(TestTeam.team2["id"], team_ids)


if __name__ == "__main__":
    unittest.main()
