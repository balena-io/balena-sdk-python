from __future__ import annotations

from typing import List, TypedDict

from typing_extensions import NotRequired

from ..balena_auth import request
from ..utils import normalize_device_os_version


class GaConfig(TypedDict):
    site: str
    id: str


class ConfigType(TypedDict):
    deployment: NotRequired[str]
    deviceUrlsBase: str
    adminUrl: str
    gitServerUrl: str
    ga: NotRequired[GaConfig]
    mixpanelToken: NotRequired[str]
    intercomAppId: NotRequired[str]
    recurlyPublicKey: NotRequired[str]
    DEVICE_ONLINE_ICON: str
    DEVICE_OFFLINE_ICON: str
    signupCodeRequired: bool
    supportedSocialProviders: List[str]


class Config:
    """
    This class implements configuration model for balena python SDK.

    """

    def get_all(self) -> ConfigType:
        """
        Get all configuration.

        Returns:
            ConfigType: configuration information.

        Examples:
            >>> balena.models.config.get_all()
        """

        return normalize_device_os_version(request(method="GET", path="/config"))
