import sys

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions


class Image:
    """
    This class implements image model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def __get_by_option(self, key, value, include_logs=False):
        """
        Private function to get a specific image using any possible key.

        Args:
            key (str): query field.
            value (str): key's value.
            include_logs (Optional[bool]): Defaults to False since build log may be very large. True if user wants to include build log in image info.

        Returns:
            dict: image info.

        Raises:
            ImageNotFound: if image couldn't be found.

        """

        params = {
            'filter': key,
            'eq': value
        }

        image = self.base_request.request(
            'image', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )

        if image['d']:
            if include_logs:
                return image['d'][0]
            else:
                image['d'][0].pop('build_log', None)
                return image['d'][0]
        else:
            raise exceptions.ImageNotFound(key)

    def get(self, id):
        """
        Get a specific image.

        Args:
            id (str): image id.

        Returns:
            dict: image info.

        Raises:
            ImageNotFound: if image couldn't be found.

        """

        image = self.__get_by_option('id', id)

        # Only return selected fields, build_log is not included by default since they can be very large.
        selected_fields = [
            'id',
            'content_hash',
            'dockerfile',
            'project_type',
            'status',
            'error_message',
            'image_size',
            'created_at',
            'push_timestamp',
            'start_timestamp',
            'end_timestamp'
        ]

        return ({k: image[k] for k in selected_fields})

    def get_log(self, id):
        """
        Get the build log from an image.

        Args:
            id (str): image id.

        Returns:
            str: build log.

        Raises:
            ImageNotFound: if image couldn't be found.

        """

        return self.__get_by_option('id', id, include_logs=True)['build_log']
