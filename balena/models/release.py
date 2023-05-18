from typing import TypedDict, Union, Any, List, Optional

from .. import exceptions
from ..builder import build_from_url
from ..pine import pine
from ..types import AnyObject
from ..types.models import ReleaseType, ReleaseWithImageDetailsType
from ..utils import is_id, merge
from . import application as app_module


class ReleaseRawVersionApplicationPair(TypedDict, total=True):
    application: Union[str, int]
    raw_version: str


class Release:
    """
    This class implements release model for balena python SDK.

    """

    def __set(
        self,
        commit_or_id_or_raw_version: Union[str, int, ReleaseRawVersionApplicationPair],
        body: AnyObject,
    ) -> None:
        id = self.get(commit_or_id_or_raw_version, {"$select": "id"})["id"]
        pine.patch({"resource": "release", "id": id, "body": body})

    def get(
        self,
        commit_or_id_or_raw_version: Union[str, int, ReleaseRawVersionApplicationPair],
        options: AnyObject = {},
    ) -> ReleaseType:
        """
        Get a specific release.

        Args:
            commit_or_id_or_raw_version(Union[str, int, ReleaseRawVersionApplicationPair]): release commit (string)
            or id (number) or an object with the unique `application` (number or string) & `rawVersion` (string)
            pair of the release options
            options(AnyObject): extra pine options to use

        Returns:
            ReleaseType: release info.
        """

        if commit_or_id_or_raw_version is None:
            raise exceptions.ReleaseNotFound(commit_or_id_or_raw_version)

        if is_id(commit_or_id_or_raw_version):
            release = pine.get(
                {"resource": "release", "id": commit_or_id_or_raw_version, "options": options}  # type: ignore
            )

            if release is None:
                raise exceptions.ReleaseNotFound(commit_or_id_or_raw_version)
            return release
        else:
            if isinstance(commit_or_id_or_raw_version, dict):
                raw_version = commit_or_id_or_raw_version["raw_version"]
                app = commit_or_id_or_raw_version["application"]
                app_id = app_module.application.get(app, {"$select": "id"})["id"]
                dollar_filter = {
                    "raw_version": raw_version,
                    "belongs_to__application": app_id,
                }
            else:
                dollar_filter = {"commit": {"$startswith": commit_or_id_or_raw_version}}
            releases = pine.get(
                {
                    "resource": "release",
                    "options": merge({"$filter": dollar_filter}, options),
                }
            )

            if len(releases) == 0:
                raise exceptions.ReleaseNotFound(str(commit_or_id_or_raw_version))
            if len(releases) > 1:
                raise exceptions.AmbiguousRelease(str(commit_or_id_or_raw_version))
            return releases[0]

    def get_with_image_details(
        self,
        commit_or_id_or_raw_version: Union[str, int, ReleaseRawVersionApplicationPair],
        image_options: AnyObject = {},
        release_options: AnyObject = {},
    ) -> ReleaseWithImageDetailsType:
        """
        Get a specific release with the details of the images built.

        Args:
            commit_or_id_or_raw_version(Union[str, int, ReleaseRawVersionApplicationPair]): release commit (string)
            image_options (AnyObject): extra pine options to use on image expand
            release_options (AnyObject): extra pine options to use on release expand

        Returns:
            dict: release info.

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """
        base_image_options = {
            "$select": "id",
            "$expand": {"is_a_build_of__service": {"$select": "service_name"}},
        }

        base_release_options = {
            "$expand": {
                "release_image": {"$expand": {"image": merge(base_image_options, image_options)}},
                "is_created_by__user": {"$select": ["id", "username"]},
            }
        }

        release: Any = self.get(
            commit_or_id_or_raw_version,
            merge(base_release_options, release_options),
        )

        images = [ri["image"][0] for ri in release["release_image"]]

        del release["release_image"]
        release["images"] = sorted(
            [
                {
                    **image_data,
                    "service_name": image_data["is_a_build_of__service"][0]["service_name"],
                }
                for image_data in images
                if "is_a_build_of__service" in image_data
            ],
            key=lambda x: x["service_name"],
        )
        release["user"] = release["is_created_by__user"][0]

        return release

    def get_all_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[ReleaseType]:
        """
        Get all releases from an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).
            options (AnyObject): extra pine options to use

        Returns:
            List[ReleaseType]: release info.
        """
        app_id = app_module.application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]

        return pine.get(
            {
                "resource": "release",
                "options": merge(
                    {
                        "$filter": {"belongs_to__application": app_id},
                        "$orderby": "created_at desc",
                    },
                    options,
                ),
            }
        )

    def get_latest_by_application(
        self, slug_or_uuid_or_id: Union[str, int], options: AnyObject = {}
    ) -> Optional[ReleaseType]:
        """
        Get the latest successful release for an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).
            options (AnyObject): extra pine options to use

        Returns:
            Optional[ReleaseType]: release info.

        """
        releases = self.get_all_by_application(
            slug_or_uuid_or_id,
            merge({"$top": 1, "$filter": {"status": "success"}}, options),
        )

        if len(releases) == 0:
            return None
        return releases[0]

    def create_from_url(
        self,
        slug_or_uuid_or_id: Union[str, int],
        url: str,
        flatten_tarball: bool = True,
    ) -> int:
        """
        Create a new release built from the source in the provided url.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number).
            url (str): a url with a tarball of the project to build.
            flatten_tarball (bool): Should be true when the tarball includes an extra root folder
            with all the content.

        Returns:
            int: release Id.
        """

        app_options = {
            "$select": "app_name",
            "$expand": {"organization": {"$select": "handle"}},
        }
        app = app_module.application.get(slug_or_uuid_or_id, app_options)
        return build_from_url(
            app["organization"][0]["handle"],
            app["app_name"],
            url,
            flatten_tarball,
        )

    def finalize(
        self,
        commit_or_id_or_raw_version: Union[str, int, ReleaseRawVersionApplicationPair],
    ) -> None:
        """
        Finalizes a draft release.

        Args:
            commit_or_id_or_raw_version(Union[str, int, ReleaseRawVersionApplicationPair]): release commit (string)
        """

        self.__set(commit_or_id_or_raw_version, {"is_final": True})

    def set_is_invalidated(
        self,
        commit_or_id_or_raw_version: Union[str, int, ReleaseRawVersionApplicationPair],
        is_invalidated: bool,
    ) -> None:
        """
        Set the is_invalidated property of a release to True or False.

        Args:
            commit_or_id_or_raw_version(Union[str, int, ReleaseRawVersionApplicationPair]): release commit (string)
            is_invalidated (bool): True for invalidated, False for validated.
        """
        self.__set(commit_or_id_or_raw_version, {"is_invalidated": is_invalidated})

    def set_note(
        self,
        commit_or_id_or_raw_version: Union[str, int, ReleaseRawVersionApplicationPair],
        note: Optional[str] = None,
    ) -> None:
        """
        Set a note for a release.

        Args:
            commit_or_id_or_raw_version(Union[str, int, ReleaseRawVersionApplicationPair]): release commit (string)
            note (Optional[str]): the note.
        """
        self.__set(commit_or_id_or_raw_version, {"note": note})

    def set_known_issue_list(
        self,
        commit_or_id_or_raw_version: Union[str, int, ReleaseRawVersionApplicationPair],
        known_issue_list: Optional[str],
    ) -> None:
        """
        Set a known issue list for a release.

        Args:
            commit_or_id_or_raw_version(Union[str, int, ReleaseRawVersionApplicationPair]): release commit (string)
            known_issue_list (Optional[str]): the known issue list.
        """
        self.__set(commit_or_id_or_raw_version, {"known_issue_list": known_issue_list})
