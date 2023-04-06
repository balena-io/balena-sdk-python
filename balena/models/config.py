from ..base_request import BaseRequest
from ..settings import Settings


class Config:
    """
    This class implements configuration model for balena python SDK.

    Attributes:
        _config (dict): caching configuration.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self._config = {}
        self._device_types = None

    def _get_config(self, key):
        if self._config:
            return self._config[key]
        # Load all config again
        self.get_all()
        return self._config[key]

    def get_all(self):
        """
        Get all configuration.

        Returns:
            dict: configuration information.

        Examples:
            >>> balena.models.config.get_all()
            { all configuration details }

        """

        if not self._config:
            self._config = self.base_request.request("config", "GET", endpoint=self.settings.get("api_endpoint"))
        return self._config
