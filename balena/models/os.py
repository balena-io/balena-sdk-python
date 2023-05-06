from typing import Literal, Optional, TypedDict, Union

from .. import exceptions
from ..balena_auth import request
from . import application as app_module


class ImgConfigOptions(TypedDict, total=False):
    network: Optional[Literal["ethernet", "wifi"]]
    appUpdatePollInterval: Optional[int]
    provisioningKeyName: Optional[str]
    provisioningKeyExpiryDate: Optional[str]
    wifiKey: Optional[str]
    wifiSsid: Optional[str]
    ip: Optional[str]
    gateway: Optional[str]
    netmask: Optional[str]
    deviceType: Optional[str]
    version: str
    developmentMode: Optional[bool]


class OS:
    """
    This class implements OS model for balena python SDK.
    """

    def __init__(self):
        pass

    def get_config(
        self, slug_or_uuid_or_id: Union[str, int], options: ImgConfigOptions
    ):
        """
        Download application config.json.

        Args:
            app_id (str): application id.
            options (ImgConfigOptions): OS configuration dict to use. The available options
            are listed below:
                network (Optional[Literal["ethernet", "wifi"]]): The network type that
                the device will use, one of 'ethernet' or 'wifi'.
                appUpdatePollInterval (Optional[int]): How often the OS checks for updates, in minutes.
                provisioningKeyName (Optional[str]): Name assigned to API key
                provisioningKeyExpiryDate (Optional[str]): Expiry Date assigned to API key
                wifiKey (Optional[str]): The key for the wifi network the device will connect to.
                wifiSsid (Optional[str]): The ssid for the wifi network the device will connect to.
                ip (Optional[str]): static ip address
                gateway (Optional[str]): static ip gateway.
                netmask (Optional[str]): static ip netmask.
                deviceType (Optional[str]): The device type.
                version (str): Required: the OS version of the image.
                developmentMode (Optional[bool]): If the device should be in development mode.

        Returns:
            dict: application config.json content.

        Raises:
            ApplicationNotFound: if application couldn't be found.

        """

        if options.get("version") is None:
            raise Exception(
                "An OS version is required when calling os.getConfig"
            )

        options["network"] = options.get("network", "ethernet")
        app_id = app_module.application.get_id(slug_or_uuid_or_id)

        try:
            return request(
                method="POST",
                path="/download-config",
                body={**options, "appId": app_id},
            )
        except exceptions.RequestError as e:
            if e.status_code == 404:
                raise exceptions.ApplicationNotFound(slug_or_uuid_or_id)
            raise e
