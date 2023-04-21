from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions
from .image import Image
from .service import Service
from ..utils import is_id


class Release:
    """
    This class implements release model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.image = Image()
        self.service = Service()

    def __get_by_option(self, **options):
        """
        Private function to get releases using any possible key.

        Args:
            **options: options keyword arguments.

        Returns:
            list: release info.

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        params = {"filters": options}

        release = self.base_request.request(
            "release", "GET", params=params, endpoint=self.settings.get("pine_endpoint")
        )

        if release["d"]:
            return release["d"]
        else:
            raise exceptions.ReleaseNotFound(options)

    def __get_by_raw_query(self, raw_query):
        """
        Private function to get releases using raw query.

        Args:
            raw_query (str): query field.

        Returns:
            list: release info.

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        release = self.base_request.request(
            "release",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
        )

        if release["d"]:
            return release["d"]
        else:
            raise exceptions.ReleaseNotFound(raw_query)

    def get(self, commit_or_id):
        """
        Get a specific release.

        Args:
            commit_or_id: release commit (str) or id (int).

        Returns:
            dict: release info.

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        if is_id(commit_or_id):
            return self.__get_by_option(id=commit_or_id)[0]
        else:
            raw_query = "$filter=startswith(commit, '{}')".format(commit_or_id)

            try:
                rt = self.__get_by_raw_query(raw_query)

                if len(rt) > 1:
                    raise exceptions.AmbiguousRelease(commit_or_id)

                return rt[0]
            except exceptions.ReleaseNotFound:
                raise exceptions.ReleaseNotFound(commit_or_id)

    def get_all_by_application(self, app_id):
        """
        Get all releases from an application.

        Args:
            app_id (str): applicaiton id.

        Returns:
            list: release info.

        """

        return self.__get_by_option(belongs_to__application=app_id)

    def get_latest_by_application(self, app_id):
        """
        Get the latest successful release for an application.

        Args:
            app_id (str): applicaiton id.

        Returns:
            dict: release info.

        """

        # fmt: off
        raw_query = (
            "$top=1"
            "&$filter="
                f"belongs_to__application%20eq%20'{app_id}'%20and%20"
                "status%20eq%20'success'"
            "&$orderby=created_at%20desc"
        )
        # fmt: on

        try:
            return self.__get_by_raw_query(raw_query)[0]
        except exceptions.ReleaseNotFound:
            raise exceptions.ReleaseNotFound(app_id)

    def remove(self, commit_or_id):
        """
        Remove a specific release. This function only works if you log in using credentials or Auth Token.

        Args:
            commit_or_id: release commit (str) or id (int).

        Raises:
            ReleaseNotFound: if release couldn't be found.
            AmbiguousRelease: if release commit is ambiguous.

        """

        if is_id(commit_or_id):
            params = {"filters": {"id": commit_or_id}}
        else:
            raw_query = "$filter=startswith(commit, '{}')".format(commit_or_id)

            try:
                rt = self.__get_by_raw_query(raw_query)

                if len(rt) > 1:
                    raise exceptions.AmbiguousRelease(commit_or_id)

                params = {"filters": {"id": rt[0]["id"]}}
            except exceptions.ReleaseNotFound:
                raise exceptions.ReleaseNotFound(commit_or_id)

        return self.base_request.request(
            "release",
            "DELETE",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def get_with_image_details(self, commit_or_id):
        """
        Get a specific release with the details of the images built.

        Args:
            commit_or_id: release commit (str) or id (int).

        Returns:
            dict: release info.

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        id = self.get(commit_or_id)["id"]

        # TODO: pine client for python
        # fmt: off
        raw_query = (
            "$expand="
                "release_image("
                    "$select=id"
                    "&$expand=image("
                        "$select=id"
                        "&$expand=is_a_build_of__service("
                            "$select=service_name"
                        ")"
                    ")"
                "),"
                "is_created_by__user($select=id,username)"
            )
        # fmt: on
        raw_release = self.base_request.request(
            "release({id})".format(id=id),
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
        )

        if raw_release["d"]:
            raw_release = raw_release["d"][0]
            release = {
                "user": raw_release["is_created_by__user"][0],
                "images": [
                    {
                        "id": i["id"],
                        "service_name": i["image"][0]["is_a_build_of__service"][0]["service_name"],
                    }
                    for i in raw_release["release_image"]
                ],
            }

            raw_release.pop("is_created_by__user", None)
            raw_release.pop("release_image", None)
            release.update(raw_release)
            return release
        else:
            raise exceptions.ReleaseNotFound(commit_or_id)

    def create_from_url(self, app_id, url, flatten_tarball=True):
        """
        Create a new release built from the source in the provided url.

        Args:
            app_id (int): application id.
            url (str): a url with a tarball of the project to build.
            flatten_tarball (Optional[bool]): Should be true when the tarball includes an extra root folder with all the content.

        Returns:
            int: release Id.

        Raises:
            BuilderRequestError: if builder returns any errors.

        """  # noqa: E501

        raw_query = f"$filter=id%20eq%20'{app_id}'" "&$select=app_name" "&$expand=organization($select=handle)"

        app = self.base_request.request(
            "application",
            "GET",
            raw_query=raw_query,
            endpoint=self.settings.get("pine_endpoint"),
        )["d"]

        if len(app) == 0:
            raise exceptions.ApplicationNotFound(app_id)
        if len(app) > 1:
            raise exceptions.AmbiguousApplication(app_id)

        data = {"url": url, "shouldFlatten": flatten_tarball}

        response = self.base_request.request(
            "/v3/buildFromUrl?headless=true&owner={owner}&app={app_name}".format(
                app_name=app[0]["app_name"], owner=app[0]["organization"][0]["handle"]
            ),
            "POST",
            data=data,
            endpoint=self.settings.get("builder_url"),
        )

        if response["started"]:
            return response["releaseId"]

        raise exceptions.BuilderRequestError(response["message"])

    def finalize(self, commit_or_id):
        """
        Finalizes a draft release.

        Args:
            commit_or_id (str): release commit (str) or id (int).

        Returns:
            OK

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        id = self.get(commit_or_id)["id"]

        params = {"filter": "id", "eq": id}

        data = {"is_final": True}

        return self.base_request.request(
            "release",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def set_is_invalidated(self, commit_or_id, is_invalidated):
        """
        Set the is_invalidated property of a release to True or False.

        Args:
            commit_or_id (str): release commit (str) or id (int).
            is_invalidated (bool): True for invalidated, False for validated.

        Returns:
            OK

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        id = self.get(commit_or_id)["id"]

        params = {"filter": "id", "eq": id}

        data = {"is_invalidated": is_invalidated}

        return self.base_request.request(
            "release",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def set_note(self, commit_or_id, note):
        """
        Set a note for a release.

        Args:
            commit_or_id (str): release commit (str) or id (int).
            note (str): the note.

        Returns:
            OK

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        id = self.get(commit_or_id)["id"]

        params = {"filter": "id", "eq": id}

        data = {"note": note}

        return self.base_request.request(
            "release",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def set_known_issue_list(self, commit_or_id, known_issue_list):
        """
        Set a known issue list for a release.

        Args:
            commit_or_id (str): release commit (str) or id (int).
            known_issue_list (str): the known issue list.

        Returns:
            OK

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        id = self.get(commit_or_id)["id"]

        params = {"filter": "id", "eq": id}

        data = {"known_issue_list": known_issue_list}

        return self.base_request.request(
            "release",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )

    def set_release_version(self, commit_or_id, semver):
        """
        Set a version for a release.

        Args:
            commit_or_id (str): release commit (str) or id (int).
            semver (str): the release version, only supports semver compliant values.

        Returns:
            OK

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        id = self.get(commit_or_id)["id"]

        params = {"filter": "id", "eq": id}

        data = {"semver": semver}

        return self.base_request.request(
            "release",
            "PATCH",
            params=params,
            data=data,
            endpoint=self.settings.get("pine_endpoint"),
        )
