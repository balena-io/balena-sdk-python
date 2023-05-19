import datetime
import time
import unittest
from typing import Any

from tests.helper import TestHelper


class TestRelease(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena
        cls.helper.wipe_application()
        cls.empty_app = cls.balena.models.application.create(
            "ServiceTestApp", "raspberry-pi2", cls.helper.default_organization["id"]
        )
        cls.mc_app = cls.helper.create_multicontainer_app()
        cls.TEST_SOURCE_URL = "https://github.com/balena-io-examples/balena-node-hello-world/archive/v1.0.0.tar.gz"
        cls.TEST_SOURCE_CONTAINER_COUNT = 1
        cls.UNIQUE_PROPERTY_NAMES = ["id", "commit", "__belongs_to__hash__"]

    @classmethod
    def tearDownClass(cls):
        cls.helper.wipe_application()

    def test_01_should_reject_if_release_id_does_not_exist(self):
        with self.assertRaises(self.helper.balena_exceptions.ReleaseNotFound):
            self.balena.models.release.get(123)

        with self.assertRaises(self.helper.balena_exceptions.ReleaseNotFound):
            self.balena.models.release.get("7cf02a6")

        with self.assertRaises(self.helper.balena_exceptions.ReleaseNotFound):
            self.balena.models.release.get({"application": self.empty_app["id"], "raw_version": "10.0.0"})

        with self.assertRaises(self.helper.balena_exceptions.ReleaseNotFound):
            self.balena.models.release.get_with_image_details(123)

        with self.assertRaises(self.helper.balena_exceptions.ReleaseNotFound):
            self.balena.models.release.get_with_image_details("7cf02a6")

        with self.assertRaises(self.helper.balena_exceptions.ReleaseNotFound):
            self.balena.models.release.get_with_image_details(
                {"application": self.empty_app["id"], "raw_version": "10.0.0"}
            )

    def test_02_should_get_all_by_application(self):
        for prop in self.helper.application_retrieval_fields:
            releases = self.balena.models.release.get_all_by_application(self.empty_app[prop])
            self.assertEqual(releases, [])

        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.release.get_all_by_application("HelloWorldApp")

        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.release.get_all_by_application(999999)

    def test_03_create_from_url(self):
        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.release.create_from_url("HelloWorldApp", url=self.TEST_SOURCE_URL)

        with self.assertRaises(self.helper.balena_exceptions.ApplicationNotFound):
            self.balena.models.release.create_from_url(123, url=self.TEST_SOURCE_URL)

        with self.assertRaises(self.helper.balena_exceptions.BuilderRequestError) as cm:
            self.balena.models.release.create_from_url(
                self.empty_app["id"],
                url="https://github.com/balena-io-projects/simple-server-node/archive/v0.0.0.tar.gz",
            )
        self.assertIn("Failed to fetch tarball from passed URL", cm.exception.message)

        with self.assertRaises(self.helper.balena_exceptions.BuilderRequestError) as cm:
            self.balena.models.release.create_from_url(
                self.empty_app["id"], url="https://github.com/balena-io-projects/simple-server-node"
            )
        self.assertIn(
            "Invalid tar header. Maybe the tar is corrupted or it needs to be gunzipped?", cm.exception.message
        )

        release_ids = []
        for prop in self.helper.application_retrieval_fields:
            release_id = self.balena.models.release.create_from_url(self.empty_app[prop], url=self.TEST_SOURCE_URL)
            self.assertIsInstance(release_id, int)
            release_ids.append(release_id)

            release = self.balena.models.release.get(release_id)
            self.assertEqual(release["status"], "running")
            self.assertEqual(release["source"], "cloud")
            self.assertEqual(release["id"], release_id)
            self.assertEqual(release["belongs_to__application"]["__id"], self.empty_app["id"])
            self.assertIsInstance(release["commit"], str)

        self.__wait_for_images_to_be_created(self.empty_app["id"], len(release_ids))

    def test_04_finalize_releases(self):
        TestRelease.test_release_by_field = {}
        user_id = self.balena.auth.get_user_id()
        for i, field in enumerate(self.UNIQUE_PROPERTY_NAMES):
            TestRelease.test_release_by_field[field] = self.balena.pine.post(
                {
                    "resource": "release",
                    "body": {
                        "belongs_to__application": self.empty_app["id"],
                        "is_created_by__user": user_id,
                        "commit": f"abcdef{i}",
                        "semver": "1.1.1",
                        "status": "success",
                        "source": "cloud",
                        "is_final": False,
                        "composition": {},
                        "start_timestamp": datetime.datetime.now().isoformat(),
                    },
                }
            )
            TestRelease.test_release_by_field[field] = self.balena.models.release.get(
                TestRelease.test_release_by_field[field]["id"],
                {"$select": ["id", "commit", "raw_version", "belongs_to__application"]},
            )

        for field in self.UNIQUE_PROPERTY_NAMES:
            draft_release = TestRelease.test_release_by_field[field]
            finalize_param = self.__get_param(field, draft_release)
            self.balena.models.release.finalize(finalize_param)  # type: ignore
            release = self.balena.models.release.get(
                draft_release["id"], {"$select": ["id", "commit", "raw_version", "is_final"]}
            )

            self.assertEqual(release["id"], draft_release["id"])
            self.assertEqual(release["commit"], draft_release["commit"])
            self.assertIn(release["raw_version"].split("+")[0], draft_release["raw_version"])
            self.assertTrue(release["is_final"])

    def test_05_invalidate_releases(self):
        for field in self.UNIQUE_PROPERTY_NAMES:
            release = TestRelease.test_release_by_field[field]
            invalidate_param = self.__get_param(field, release)
            if isinstance(invalidate_param, dict):
                invalidate_param["raw_version"] = "1.1.1+rev2"

            self.balena.models.release.set_is_invalidated(invalidate_param, True)  # type: ignore
            invalidated_release = self.balena.models.release.get(
                invalidate_param, {"$select": ["is_invalidated"]}  # type: ignore
            )
            self.assertTrue(invalidated_release["is_invalidated"])

            self.balena.models.release.set_is_invalidated(invalidate_param, False)  # type: ignore
            validated_release = self.balena.models.release.get(
                invalidate_param, {"$select": ["is_invalidated"]}  # type: ignore
            )
            self.assertFalse(validated_release["is_invalidated"])

    def test_06_get_release_by_resources(self):
        match = {"id": self.mc_app["current_release"]["id"], "app_id": self.mc_app["app"]["id"]}

        release = self.balena.models.release.get(self.mc_app["current_release"]["id"])
        self.__expect_release_to_match_on_get(release, match)

        release = self.balena.models.release.get(self.mc_app["current_release"]["commit"])
        self.__expect_release_to_match_on_get(release, match)

        release = self.balena.models.release.get(self.mc_app["current_release"]["commit"][0:7])
        self.__expect_release_to_match_on_get(release, match)

        release = self.balena.models.release.get(
            {
                "application": self.mc_app["app"]["id"],
                "raw_version": self.mc_app["current_release"]["raw_version"],
            }
        )  # type: ignore
        self.__expect_release_to_match_on_get(release, match)

    def test_07_get_all_by_application(self):
        app_id = self.mc_app["app"]["id"]
        releases = self.balena.models.release.get_all_by_application(app_id)
        sorted_releases = sorted(releases, key=lambda r: r["start_timestamp"])
        sorted_releases = [{k: r[k] for k in ("status", "source", "commit")} for r in sorted_releases]

        self.assertEqual(
            sorted_releases,
            [
                {
                    "status": "success",
                    "source": "cloud",
                    "commit": "old-release-commit",
                },
                {
                    "status": "success",
                    "source": "cloud",
                    "commit": "new-release-commit",
                },
            ],
        )

    def test_08_get_with_image_details(self):
        release = self.balena.models.release.get_with_image_details(self.mc_app["current_release"]["id"])
        self.__expect_release_to_match_on_get_with_image_details(release)

        release = self.balena.models.release.get_with_image_details(self.mc_app["current_release"]["commit"])
        self.__expect_release_to_match_on_get_with_image_details(release)

        release = self.balena.models.release.get_with_image_details(self.mc_app["current_release"]["commit"][0:7])
        self.__expect_release_to_match_on_get_with_image_details(release)

        release = self.balena.models.release.get_with_image_details(self.mc_app["current_release"]["commit"][0:7])
        self.__expect_release_to_match_on_get_with_image_details(release)

        release = self.balena.models.release.get_with_image_details(
            {
                "application": self.mc_app["app"]["id"],
                "raw_version": self.mc_app["current_release"]["raw_version"],
            }
        )  # type: ignore
        self.__expect_release_to_match_on_get_with_image_details(release)

        release = self.balena.models.release.get_with_image_details(
            self.mc_app["current_release"]["id"], image_options={"$select": "build_log"}
        )
        self.__expect_release_to_match_on_get_with_image_details(release, ["new db log", "new web log"])

    def test_09_set_note(self):
        for field in self.UNIQUE_PROPERTY_NAMES:
            release = self.mc_app["current_release"]
            note_param = self.__get_param(field, release)
            note = f"this is a note set using field: {field}"
            self.balena.models.release.set_note(note_param, note)  # type: ignore
            updated_release = self.balena.models.release.get(release["id"], {"$select": ["id", "note"]})
            self.assertEqual(updated_release, {"id": release["id"], "note": note})

    def test_10_set_known_issue_list(self):
        for field in self.UNIQUE_PROPERTY_NAMES:
            release = self.mc_app["current_release"]
            known_issue_list_param = self.__get_param(field, release)
            known_issue_list = f"this is an issue set using field: {field}"
            self.balena.models.release.set_known_issue_list(known_issue_list_param, known_issue_list)  # type: ignore
            updated_release = self.balena.models.release.get(release["id"], {"$select": ["id", "known_issue_list"]})
            self.assertEqual(updated_release, {"id": release["id"], "known_issue_list": known_issue_list})

    def test_11_get_latest_by_application(self):
        app_id = self.mc_app["app"]["id"]
        user_id = self.balena.auth.get_user_id()

        releases = [
            {
                "belongs_to__application": app_id,
                "is_created_by__user": user_id,
                "commit": "errored-then-fixed-release-commit",
                "status": "error",
                "source": "cloud",
                "composition": {},
                "start_timestamp": 64321,
            },
            {
                "belongs_to__application": app_id,
                "is_created_by__user": user_id,
                "commit": "errored-then-fixed-release-commit",
                "status": "success",
                "source": "cloud",
                "composition": {},
                "start_timestamp": 74321,
            },
            {
                "belongs_to__application": app_id,
                "is_created_by__user": user_id,
                "commit": "failed-release-commit",
                "status": "failed",
                "source": "cloud",
                "composition": {},
                "start_timestamp": 84321,
            },
        ]
        for body in releases:
            self.balena.pine.post({"resource": "release", "body": body})

        app = self.mc_app["app"]
        for prop in self.helper.application_retrieval_fields:
            release = self.balena.models.release.get_latest_by_application(app[prop])
            self.assertIsNotNone(release)
            self.assertEqual(release["status"], "success")  # type: ignore
            self.assertEqual(release["source"], "cloud")  # type: ignore
            self.assertEqual(release["commit"], "errored-then-fixed-release-commit")  # type: ignore
            self.assertEqual(release["belongs_to__application"]["__id"], app["id"])  # type: ignore

    def test_12_releases_sharing_same_commit_root(self):
        user_id = self.balena.auth.get_user_id()
        app = self.mc_app["app"]

        self.balena.pine.post(
            {
                "resource": "release",
                "body": {
                    "belongs_to__application": app["id"],
                    "is_created_by__user": user_id,
                    "commit": "feb2361230dc40dba6dca9a18f2c19dc8f2c19dc",
                    "status": "success",
                    "source": "cloud",
                    "composition": {},
                    "start_timestamp": 64321,
                },
            }
        )
        self.balena.pine.post(
            {
                "resource": "release",
                "body": {
                    "belongs_to__application": app["id"],
                    "is_created_by__user": user_id,
                    "commit": "feb236123bf740d48900c19027d4a02127d4a021",
                    "status": "success",
                    "source": "cloud",
                    "composition": {},
                    "start_timestamp": 74321,
                },
            }
        )

        with self.assertRaises(self.helper.balena_exceptions.AmbiguousRelease):
            self.balena.models.release.get("feb23612")

        release = self.balena.models.release.get("feb2361230dc40dba6dca9a18f2c19dc8f2c19dc")

        self.assertEqual(release["commit"], "feb2361230dc40dba6dca9a18f2c19dc8f2c19dc")
        self.assertEqual(release["status"], "success")
        self.assertEqual(release["source"], "cloud")

        with self.assertRaises(self.helper.balena_exceptions.AmbiguousRelease):
            self.balena.models.release.get_with_image_details("feb23612")

        release_with_details = self.balena.models.release.get_with_image_details(
            "feb2361230dc40dba6dca9a18f2c19dc8f2c19dc"
        )

        self.assertEqual(release_with_details["commit"], "feb2361230dc40dba6dca9a18f2c19dc8f2c19dc")
        self.assertEqual(release_with_details["status"], "success")
        self.assertEqual(release_with_details["source"], "cloud")

    def __expect_release_to_match_on_get(self, release, match):
        self.assertEqual(release["status"], "success")
        self.assertEqual(release["source"], "cloud")
        self.assertEqual(release["commit"], "new-release-commit")
        self.assertEqual(release["id"], match["id"])
        self.assertEqual(release["belongs_to__application"]["__id"], match["app_id"])

    def __expect_release_to_match_on_get_with_image_details(self, release, build_logs=[None, None]):
        self.assertEqual(release["commit"], "new-release-commit")
        self.assertEqual(release["status"], "success")
        self.assertEqual(release["source"], "cloud")
        self.assertEqual(release["images"][0]["service_name"], "db")
        self.assertEqual(release["images"][1]["service_name"], "web")
        self.assertEqual(release["user"]["username"], self.helper.credentials["user_id"])
        self.assertEqual(release["images"][0].get("build_log"), build_logs[0])
        self.assertEqual(release["images"][1].get("build_log"), build_logs[1])

    def __get_param(self, field: str, draft_release: Any):
        if field == "__belongs_to__hash__":
            return {
                "application": draft_release["belongs_to__application"]["__id"],
                "raw_version": draft_release["raw_version"],
            }
        return draft_release[field]

    def __wait_for_images_to_be_created(self, app_id: int, release_count: int):
        start = time.time()
        while True:
            image_count = self.balena.pine.get(
                {
                    "resource": "image",
                    "options": {
                        "$count": {
                            "$filter": {
                                "is_a_build_of__service": {
                                    "$any": {
                                        "$alias": "s",
                                        "$expr": {
                                            "s": {
                                                "application": app_id,
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                }
            )

            if image_count == self.TEST_SOURCE_CONTAINER_COUNT * release_count:
                break

            if time.time() - start > 30:
                print("Giving up waiting before balena.models.release.createFromUrl() cleanup")
                break

            time.sleep(5)
