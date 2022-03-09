from functools import wraps
import json
try:  # Python 3 imports
    from urllib.parse import urljoin
except ImportError:  # Python 2 imports
    from urlparse import urljoin
from collections import defaultdict
from threading import Thread

from twisted.internet import reactor, ssl
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.internet.ssl import ClientContextFactory

from .base_request import BaseRequest
from . import exceptions
from .models.config import Config
from .models.device import Device
from .settings import Settings


class WebClientContextFactory(ClientContextFactory):
    """
    This is low level class and is not meant to be used by end users directly.
    """

    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)


class StreamingParser(Protocol):
    """
    This is low level class and is not meant to be used by end users directly.
    """

    def __init__(self, callback, error):
        self.callback = callback
        self.error = error
        self.pending = b''

    def dataReceived(self, data):
        obj = {}
        self.pending += data

        lines = self.pending.split(b'\n')
        self.pending = lines.pop()

        for line in lines:
            try:
                if line:
                    obj = json.loads(line)
            except Exception as e:
                self.transport.stopProducing()
                self.transport.loseConnection()

                if self.error:
                    self.error(e)
                break
            self.callback(obj)

    def connectionLost(self, reason):
        pass


def cbRequest(response, callback, error):
    protocol = StreamingParser(callback, error)
    response.deliverBody(protocol)
    return protocol


def cbDrop(protocol):
    protocol.transport.stopProducing()
    protocol.transport.loseConnection()


class Subscription:
    """
    This is low level class and is not meant to be used by end users directly.
    """

    def __init__(self):
        self.context_factory = WebClientContextFactory()
        self.settings = Settings()

    def add(self, uuid, callback, error=None, count=None):
        query = 'stream=1'
        if count:
            query = 'stream=1&count={}'.format(count)

        url = urljoin(
            self.settings.get('api_endpoint'),
            '/device/v2/{uuid}/logs?{query}'.format(uuid=uuid, query=query)
        )
        headers = {}
        headers[b'Authorization'] = ['Bearer {:s}'.format(self.settings.get('token')).encode()]

        agent = Agent(reactor, self.context_factory)
        d = agent.request(b'GET', url.encode(), Headers(headers), None)
        d.addCallback(cbRequest, callback, error)
        self.run()

        return d

    def run(self):
        if not reactor.running:
            Thread(target=reactor.run, args=(False,)).start()

    def stop(self, d):
        reactor.callFromThread(d.addCallback, cbDrop)


class Logs:
    """
    This class implements functions that allow processing logs from device.

    """

    subscriptions = defaultdict(list)

    def __init__(self):
        self.base_request = BaseRequest()
        self.config = Config()
        self.device = Device()
        self.settings = Settings()
        self.subscription_handler = Subscription()

    def __exit__(self, exc_type, exc_value, traceback):
        reactor.stop()

    def subscribe(self, uuid, callback, error=None, count=None):
        """
        Subscribe to device logs.

        Args:
            uuid (str): device uuid.
            callback (function): this callback is called on receiving a message.
            error (Optional[function]): this callback is called on an error event.
            count (Optional[int]): number of historical messages to include.

        Returns:
            dict: a log entry will contain the following keys: `isStdErr, timestamp, message, isSystem, createdAt`.

        """

        self.device.get(uuid)
        self.subscriptions[uuid].append(self.subscription_handler.add(uuid, callback, error, count))

    def history(self, uuid, count=None):
        """
        Get device logs history.

        Args:
            uuid (str): device uuid.
            count (Optional[int]): number of historical messages to include.

        """

        raw_query = ''

        if count:
            raw_query = 'count={}'.format(count)

        return self.base_request.request(
            '/device/v2/{uuid}/logs'.format(uuid=uuid), 'GET', raw_query=raw_query,
            endpoint=self.settings.get('api_endpoint')
        )

    def unsubscribe(self, uuid):
        """
        Unsubscribe from device logs for a specific device.

        Args:
            uuid (str): device uuid.

        """

        if uuid in self.subscriptions:
            for d in self.subscriptions[uuid]:
                self.subscription_handler.stop(d)
            del self.subscriptions[uuid]

    def unsubscribe_all(self):
        """
        Unsubscribe all subscribed devices.

        """

        for device in self.subscriptions:
            for d in self.subscriptions[device]:
                self.subscription_handler.stop(d)
        self.subscriptions = {}
