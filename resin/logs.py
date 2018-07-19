from pubnub import Pubnub
from functools import wraps
import logging

from .base_request import BaseRequest
from .models.config import Config
from .models.device import Device


logging.basicConfig(format='%(levelname)s:%(message)s')


def _print_deprecation_warning():
    logging.warning(" using legacy logging services, this will stop working shortly.\nPlease update to ensure logs are correctly retrieved in future.")


# TODO: https://github.com/resin-io/resin-sdk/pull/277/files
class Logs(object):
    """
    This class implements functions that allow processing logs from device.

    This class is implemented using pubnub python sdk.

    For more details about pubnub, please visit: https://www.pubnub.com/docs/python/pubnub-python-sdk

    """

    def __init__(self):
        self.config = Config()
        self.device = Device()

    def _init_pubnub(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'pubnub'):
                pubnub_key = self.config.get_all()['pubnub']
                self.pubnub = Pubnub(
                    publish_key=pubnub_key['publish_key'],
                    subscribe_key=pubnub_key['subscribe_key']
                )
            return func(self, *args, **kwargs)
        return wrapper

    @_init_pubnub
    def subscribe(self, uuid, callback, error):
        """
        This function allows subscribing to device logs.
        There are fields (`m`, `t`, `s`, `c`) in the output which can be unclear. They stand for:
            m - The log message itself.
            t - The log timestamp.
            s - Is this a system message?
            c - The id of the service which produced this log (or null if the device does not support multiple containers).

        Args:
            uuid (str): device uuid.
            callback (function): this callback is called on receiving a message from the channel.
            error (function): this callback is called on an error event.
            For more details about callbacks in pubnub subscribe, visit here: https://www.pubnub.com/docs/python/api-reference#subscribe

        Examples:
            # Define callback and error.
            >>> def callback(message, channel):
            ...     print(message)
            >>> def error(message):
            ...     print('Error:'+ str(message))
            >>> Logs.subscribe(uuid=uuid, callback=callback, error=error)

        """

        _print_deprecation_warning()
        channel = self.get_channel(uuid)
        self.pubnub.subscribe(channels=channel, callback=callback, error=error)

    @_init_pubnub
    def history(self, uuid, callback, error):
        """
        This function allows fetching historical device logs.

        Args:
            uuid (str): device uuid.
            callback (function): this callback is called on receiving a message from the channel.
            error (function): this callback is called on an error event.
            For more details about callbacks in pubnub subscribe, visit here: https://www.pubnub.com/docs/python/api-reference#history

        Examples:
            # Define callback and error.
            >>> def callback(message):
            ...     print(message)
            >>> def error(message):
            ...     print('Error:'+ str(message))
            Logs.history(uuid=uuid, callback=callback, error=error)

        """

        _print_deprecation_warning()
        channel = self.get_channel(uuid)
        self.pubnub.history(channel=channel, callback=callback, error=error)

    def unsubscribe(self, uuid):
        """
        This function allows unsubscribing to device logs.

        Args:
            uuid (str): device uuid.

        """

        _print_deprecation_warning()
        if hasattr(self, 'pubnub'):
            channel = self.get_channel(uuid)
            self.pubnub.unsubscribe(channel=channel)

    def get_channel(self, uuid):
        """
        This function returns pubnub channel for a specific device.

        Args:
            uuid (str): device uuid.

        Returns:
            str: device channel.

        """

        _print_deprecation_warning()
        if not hasattr(self, 'logs_channel'):
            device_info = self.device.get(uuid)
            if 'logs_channel' in device_info:
                self.logs_channel = device_info['logs_channel']
            else:
                self.logs_channel = uuid

        return 'device-{logs_channel}-logs'.format(logs_channel=self.logs_channel)
