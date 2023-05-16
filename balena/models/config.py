from __future__ import annotations

from ..balena_auth import request

from typing import TypedDict, List
from typing_extensions import NotRequired


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

        return request(method="GET", path="/config")
