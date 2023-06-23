from .. import exceptions
from ..pine import PineClient
from ..types import AnyObject
from ..types.models import ImageType
from ..utils import merge
from ..settings import Settings


class Image:
    """
    This class implements image model for balena python SDK.
    """

    def __init__(self, pine: PineClient, settings: Settings):
        self.__pine = pine
        self.__settings = settings

    def get(self, id: int, options: AnyObject = {}) -> ImageType:
        """
        Get a specific image.

        Args:
            id (int): image id.
            options (AnyObject): extra pine options to use.

        Returns:
            ImageType: image info.
        """
        base_options = {
            "$select": [
                "id",
                "content_hash",
                "dockerfile",
                "project_type",
                "status",
                "error_message",
                "image_size",
                "created_at",
                "push_timestamp",
                "start_timestamp",
                "end_timestamp",
            ]
        }

        image = self.__pine.get({"resource": "image", "id": id, "options": merge(base_options, options, True)})

        if image is None:
            raise exceptions.ImageNotFound(id)

        return image

    def get_logs(self, id: int) -> str:
        """
        Get the build log from an image.

        Args:
            id (str): image id.

        Returns:
            str: build log.
        """
        return self.get(id, {"$select": "build_log"})["build_log"]
