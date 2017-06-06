from ..base_request import BaseRequest
from ..settings import Settings
from ..token import Token
from .. import exceptions


class Build(object):
    """
    This class implements model for build for Resin Python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.token = Token()

    def get(self, id):
        """
        Get a specific build.

        Args:
            id (str): build id.

        Returns:
            dict: build info.

        Raises:
            BuildNotFound: if build couldn't be found.

        """

        params = {
            'filter': 'id',
            'eq': id
        }
        build = self.base_request.request(
            'build', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )
        if build:
            return build
        else:
            raise exceptions.BuildNotFound(id)

    def get_all_by_application(self, app_id, include_logs=False):
        """
        Get a specific build.

        Args:
            app_id (str): application id.
            include_logs (bool): True if user wants to include build logs in build info, False otherwise.

        Returns:
            list: list of build info.

        Raises:
            BuildNotFound: if build couldn't be found.

        """

        params = {
            'filter': 'application',
            'eq': app_id
        }
        full_builds = self.base_request.request(
            'build', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )
        builds = []
        build_info = [
            'id', 'created_at', 'status',
            'push_timestamp', 'end_timestamp',
            'start_timestamp', 'project_type',
            'commit_hash', 'message'
        ]
        if include_logs:
            build_info.append('log')
        for i in full_builds['d']:
            builds.append({k: i[k] for k in build_info})
        return builds
