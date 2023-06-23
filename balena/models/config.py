from typing import List, TypedDict, Optional

from ..balena_auth import request
from ..utils import normalize_device_os_version
from ..settings import Settings


class GaConfig(TypedDict):
    site: str
    id: str


class ConfigType(TypedDict):
    deployment: Optional[str]
    deviceUrlsBase: str
    adminUrl: str
    gitServerUrl: str
    ga: Optional[GaConfig]
    mixpanelToken: Optional[str]
    intercomAppId: Optional[str]
    recurlyPublicKey: Optional[str]
    DEVICE_ONLINE_ICON: str
    DEVICE_OFFLINE_ICON: str
    signupCodeRequired: bool
    supportedSocialProviders: List[str]


class Config:
    """
    This class implements configuration model for balena python SDK.

    """

    def __init__(self, settings: Settings):
        self.__settings = settings

    def get_all(self) -> ConfigType:
        """
        Get all configuration.

        Returns:
            ConfigType: configuration information.

        Examples:
            >>> balena.models.config.get_all()
        """

        return normalize_device_os_version(request(method="GET", path="/config", settings=self.__settings))
