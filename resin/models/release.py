import sys

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions
from .image import Image
from .service import Service


class Release(object):
    """
    This class implements release model for Resin Python SDK.

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
            raise exceptions.ReleaseNotFound(key)

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

        images = []
        release = self.get(id)

        # Details of images built, including image id and service name
        for service in release['composition']['services']:
            images.append({
                'service_name': service,
                'id': self.image._Image__get_by_option(
                    'is_a_build_of__service',
                    self.service._Service__get_by_option('service_name', service)[0]['id']
                )['id']
            })
        release['images'] = images

        return release
