import sys

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions
from .image import Image
from .service import Service


class Release(object):
    """
    This class implements release model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.image = Image()
        self.service = Service()

    def __get_by_option(self, key, value):
        """
        Private function to get releases using any possible key.

        Args:
            key (str): query field.
            value (str): key's value.

        Returns:
            list: release info.

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        params = {
            'filter': key,
            'eq': value
        }

        release = self.base_request.request(
            'release', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )

        if release['d']:
            return release['d']
        else:
            raise exceptions.ReleaseNotFound(value)

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
            'release', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )

        if release['d']:
            return release['d']
        else:
            raise exceptions.ReleaseNotFound(raw_query)

    def get(self, id):
        """
        Get a specific release.

        Args:
            id (str): release id.

        Returns:
            dict: release info.

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        return self.__get_by_option('id', id)[0]

    def get_all_by_application(self, app_id):
        """
        Get all releases from an application.

        Args:
            app_id (str): applicaiton id.

        Returns:
            list: release info.

        """

        return self.__get_by_option('belongs_to__application', app_id)

    def get_latest_by_application(self, app_id):
        """
        Get the latest successful release for an application.

        Args:
            app_id (str): applicaiton id.

        Returns:
            dict: release info.

        """

        raw_query = "$top=1&$filter=belongs_to__application%20eq%20'{}'%20and%20status%20eq%20'success'".format(app_id)
        try:
            return self.__get_by_raw_query(raw_query)[0]
        except exceptions.ReleaseNotFound:
            raise exceptions.ReleaseNotFound(app_id)

    def get_with_image_details(self, id):
        """
        Get a specific release with the details of the images built.

        Args:
            id (str): release id.

        Returns:
            dict: release info.

        Raises:
            ReleaseNotFound: if release couldn't be found.

        """

        # TODO: pine client for python
        raw_query = '$expand=contains__image($select=id&$expand=image($select=id&$expand=is_a_build_of__service($select=service_name))),is_created_by__user($select=id,username)'

        raw_release = self.base_request.request(
            'release({id})'.format(id=id), 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint')
        )

        if raw_release['d']:

            raw_release = raw_release['d'][0]
            release = {
                'user': raw_release['is_created_by__user'][0],
                'images': [{'id': i['id'], 'service_name': i['image'][0]['is_a_build_of__service'][0]['service_name']} for i in raw_release['contains__image']]
            }

            raw_release.pop('is_created_by__user', None)
            raw_release.pop('contains__image', None)
            release.update(raw_release)
            return release
        else:
            raise exceptions.ReleaseNotFound(id)
