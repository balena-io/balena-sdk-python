import sys

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions


class ReleaseDelta():
    """
    This class implements release delta model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        
    def get_all(self):
        """
        Get all releases deltas, this method returns all releases generated deltas.

        Returns:
            list: releases deltas.

        """
        
        return self.base_request.request(
            'release_delta', 'GET',
            endpoint=self.settings.get('pine_endpoint'), login=True
        )['d']
        
    def get_by_release(self, release_id):
        """
        Get deltas for a specific release.

        Args:
            release_id (str): release id.

        Returns:
            list: releases delta.

        """
        
        raw_query = "$filter=(originates_from__releaseid%20eq%20'{release_id}%20or%20produces__release%20eq%20'{release_id}')".format(release_id=release_id)

        return self.base_request.request(
            'release_delta', 'GET', raw_query=raw_query,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )['d']

    def create(self, release_id1, release_id2):
        """
        Get or create delta size between two releases.

        Args:
            release_id1 (str): first release id.
            release_id2 (str): second release id.

        Returns:
            list: releases delta.

        """

        data = {
            'originates_from__release': release_id1,
            'produces__release': release_id2
        }

        return self.base_request.request(
            'release_delta', 'POST', data=data,
            endpoint=self.settings.get('pine_endpoint'), login=True
        )['d']