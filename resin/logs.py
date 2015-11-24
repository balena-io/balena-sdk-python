from pubnub import Pubnub
from functools import wraps

from .base_request import BaseRequest
from .models.config import Config


class Logs(object):
    """
    This class implements functions that allow processing logs from device.

    This class is implemented using pubnub python sdk.

    For more details about pubnub, please visit: https://www.pubnub.com/docs/python/pubnub-python-sdk

    """

    def __init__(self):
        self.config = Config()

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
        Testing

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

        channel = self.get_channel(uuid)
        self.pubnub.history(channel=channel, callback=callback, error=error)

    def unsubscribe(self, uuid):
        """
        This function allows unsubscribing to device logs.

        Args:
            uuid (str): device uuid.

        """

        if hasattr(self, 'pubnub'):
            channel = self.get_channel(uuid)
            self.pubnub.unsubscribe(channel=channel)

    @staticmethod
    def get_channel(uuid):
        """
        This function returns pubnub channel for a specific device.

        Args:
            uuid (str): device uuid.

        Returns:
            str: device channel.

        """

        return 'device-{uuid}-logs'.format(uuid=uuid)
