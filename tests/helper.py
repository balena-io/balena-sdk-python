import configparser
import os
import os.path as Path
from datetime import datetime

import jwt

from balena import Balena
from balena import exceptions as balena_exceptions
import time


class TestHelper:
    credentials = {}

    def __init__(self):
        self.balena = Balena()
        TestHelper.load_env()
        self.balena_exceptions = balena_exceptions

        self.balena.auth.login(
            **{
                "username": self.credentials["user_id"],
                "password": self.credentials["password"],
            }
        )

        # Stop the test if it's run by an admin user account.
        token_data = jwt.decode(
            self.balena.settings.get("token"),
            algorithms=["HS256"],
            options={"verify_signature": False},
        )
        if any("admin" in s for s in token_data["permissions"]):
            raise Exception(
                "The test is run with an admin user account. Cancelled, please try" " again with a normal account!"
            )

        whoami = self.balena.auth.whoami()
        self.default_organization = self.balena.models.organization.get(whoami["username"])  # type: ignore

        self.application_retrieval_fields = ["id", "slug", "uuid"]

    @classmethod
    def load_env(cls):
        env_file_name = ".env"
        required_env_keys = set(["email", "user_id", "password"])
        cls.credentials = {}

        if Path.isfile(env_file_name):
            # If .env file exists
            config_reader = configparser.ConfigParser()
            config_reader.read(env_file_name)
            config_data = {}
            options = config_reader.options("Credentials")
            for option in options:
                try:
                    config_data[option] = config_reader.get("Credentials", option)
                except Exception:
                    config_data[option] = None
            if not required_env_keys.issubset(set(config_data)):
                raise Exception("Mandatory env keys missing!")
            cls.credentials = config_data
        else:
            # If .env file not exists, read credentials from environment vars.
            try:
                cls.credentials["email"] = os.environ["TEST_ENV_EMAIL"]
                cls.credentials["user_id"] = os.environ["TEST_ENV_USER_ID"]
                cls.credentials["password"] = os.environ["TEST_ENV_PASSWORD"]

                # Optional endpoint override:
                cls.credentials["api_endpoint"] = os.environ.get("TEST_API_ENDPOINT")
            except Exception:
                raise Exception("Mandatory env keys missing!")

    def wipe_application(self):
        """
        Wipe all user's apps
        """
        self.balena.pine.delete({"resource": "application", "options": {"$filter": {"1": 1}}})

    def wipe_organization(self):
        """
        Wipe all user's orgs
        """
        for org in self.balena.models.organization.get_all():
            self.balena.models.organization.remove(org["id"])

    def reset_user(self):
        """
        Wipe all user's apps, ssh keys and api keys added.
        """
        if self.balena.auth.is_logged_in():
            self.wipe_application()

            self.balena.pine.delete({"resource": "user__has__public_key", "options": {"$filter": {"1": 1}}})

            for key in self.balena.models.api_key.get_all_named_user_api_keys():
                self.balena.models.api_key.revoke(key["id"])

    def datetime_to_epoch_ms(self, dt):
        return int((dt - datetime.utcfromtimestamp(0)).total_seconds() * 1000)

    def create_device(self, app_name="FooBar", device_type="raspberry-pi2"):
        """
        Create a device belongs to an application.
        """
        app = self.balena.models.application.create(app_name, device_type, self.default_organization["id"])
        return app, self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())

    def create_multicontainer_app(self, app_name="FooBar", device_type="raspberry-pi2"):
        """
        Create a multicontainer application with a device and two releases.
        """

        old_timestamp = int(datetime.strptime("2017-01-01", "%Y-%m-%d").timestamp())
        now_timestamp = int(time.time())

        app_with_releases = self.create_app_with_releases(app_name, device_type)

        app, old_release, new_release = (
            app_with_releases["app"],
            app_with_releases["old_release"],
            app_with_releases["current_release"],
        )

        # Register web & DB services
        web_service = self.balena.pine.post(
            {"resource": "service", "body": {"application": app["id"], "service_name": "web"}}
        )

        db_service = self.balena.pine.post(
            {"resource": "service", "body": {"application": app["id"], "service_name": "db"}}
        )

        dev = self.balena.models.device.register(app["id"], self.balena.models.device.generate_uuid())

        # Set device to the new release
        self.balena.pine.patch(
            {"resource": "device", "id": dev["id"], "body": {"is_running__release": new_release["id"]}}
        )
        dev = self.balena.models.device.get(dev["uuid"])

        # Register an old & new web image build from the old and new
        # releases, a db build in the new release only
        old_web_image = self.balena.pine.post(
            {
                "resource": "image",
                "body": {
                    "is_a_build_of__service": web_service["id"],
                    "project_type": "dockerfile",
                    "content_hash": "abc",
                    "build_log": "old web log",
                    "start_timestamp": old_timestamp,
                    "push_timestamp": old_timestamp,
                    "status": "success",
                },
            }
        )

        new_web_image = self.balena.pine.post(
            {
                "resource": "image",
                "body": {
                    "is_a_build_of__service": web_service["id"],
                    "project_type": "dockerfile",
                    "content_hash": "def",
                    "build_log": "new web log",
                    "start_timestamp": now_timestamp,
                    "push_timestamp": now_timestamp,
                    "status": "success",
                },
            }
        )

        old_db_image = self.balena.pine.post(
            {
                "resource": "image",
                "body": {
                    "is_a_build_of__service": db_service["id"],
                    "project_type": "dockerfile",
                    "content_hash": "jkl",
                    "build_log": "old db log",
                    "start_timestamp": old_timestamp,
                    "push_timestamp": old_timestamp,
                    "status": "success",
                },
            }
        )

        new_db_image = self.balena.pine.post(
            {
                "resource": "image",
                "body": {
                    "is_a_build_of__service": db_service["id"],
                    "project_type": "dockerfile",
                    "content_hash": "ghi",
                    "build_log": "new db log",
                    "start_timestamp": now_timestamp,
                    "push_timestamp": now_timestamp,
                    "status": "success",
                },
            }
        )

        # Tie the images to their corresponding releases
        self.balena.pine.post(
            {
                "resource": "image__is_part_of__release",
                "body": {"image": old_web_image["id"], "is_part_of__release": old_release["id"]},
            }
        )
        self.balena.pine.post(
            {
                "resource": "image__is_part_of__release",
                "body": {"image": old_db_image["id"], "is_part_of__release": old_release["id"]},
            }
        )
        self.balena.pine.post(
            {
                "resource": "image__is_part_of__release",
                "body": {"image": new_web_image["id"], "is_part_of__release": new_release["id"]},
            }
        )
        self.balena.pine.post(
            {
                "resource": "image__is_part_of__release",
                "body": {"image": new_db_image["id"], "is_part_of__release": new_release["id"]},
            }
        )

        # Create image installs for the images on the device
        self.balena.pine.post(
            {
                "resource": "image_install",
                "body": {
                    "installs__image": old_web_image["id"],
                    "is_provided_by__release": old_release["id"],
                    "device": dev["id"],
                    "download_progress": 100,
                    "status": "running",
                    "install_date": "2017-10-01",
                },
            }
        )

        self.balena.pine.post(
            {
                "resource": "image_install",
                "body": {
                    "installs__image": new_web_image["id"],
                    "is_provided_by__release": new_release["id"],
                    "device": dev["id"],
                    "download_progress": 50,
                    "status": "downloading",
                    "install_date": "2017-10-30",
                },
            }
        )

        self.balena.pine.post(
            {
                "resource": "image_install",
                "body": {
                    "installs__image": old_db_image["id"],
                    "is_provided_by__release": old_release["id"],
                    "device": dev["id"],
                    "download_progress": 100,
                    "status": "deleted",
                    "install_date": "2017-09-30",
                },
            }
        )

        self.balena.pine.post(
            {
                "resource": "image_install",
                "body": {
                    "installs__image": new_db_image["id"],
                    "is_provided_by__release": new_release["id"],
                    "device": dev["id"],
                    "download_progress": 100,
                    "status": "running",
                    "install_date": "2017-10-30",
                },
            }
        )

        # Create service installs for the services running on the device
        self.balena.pine.post(
            {"resource": "service_install", "body": {"installs__service": web_service["id"], "device": dev["id"]}}
        )
        self.balena.pine.post(
            {"resource": "service_install", "body": {"installs__service": db_service["id"], "device": dev["id"]}}
        )

        return {
            "app": app,
            "device": dev,
            "web_service": web_service,
            "db_service": db_service,
            "old_release": old_release,
            "current_release": new_release,
            "old_web_image": old_web_image,
            "current_web_image": new_web_image,
            "old_db_image": old_db_image,
            "current_db_image": new_db_image,
        }

    def create_app_with_releases(self, app_name="FooBar", device_type="raspberry-pi2"):
        """
        Create a multicontainer application with  two releases.
        """

        app = self.balena.models.application.create(
            app_name,
            device_type,
            self.default_organization["id"],
        )
        user_id = self.balena.auth.get_user_info()["id"]

        # Register an old & new release of this application
        old_release = self.balena.pine.post(
            {
                "resource": "release",
                "body": {
                    "belongs_to__application": app["id"],
                    "is_created_by__user": user_id,
                    "commit": "old-release-commit",
                    "status": "success",
                    "source": "cloud",
                    "composition": {},
                    "start_timestamp": 1234,
                },
            }
        )

        new_release = self.balena.pine.post(
            {
                "resource": "release",
                "body": {
                    "belongs_to__application": app["id"],
                    "is_created_by__user": user_id,
                    "commit": "new-release-commit",
                    "status": "success",
                    "source": "cloud",
                    "semver": "1.1.1",
                    "composition": {},
                    "start_timestamp": 54321,
                },
            }
        )

        new_release = self.balena.models.release.get(
            new_release["id"], {"$select": ["id", "commit", "raw_version", "belongs_to__application"]}
        )

        return {"app": app, "old_release": old_release, "current_release": new_release}

    def get_org_admin_role(self):
        """
        Get organization administrator role.

        """

        return self.balena.pine.get(
            {
                "resource": "organization_membership_role",
                "options": {"$top": 1, "$select": ["id"], "$filter": {"name": "administrator"}},
            }
        )[0]
