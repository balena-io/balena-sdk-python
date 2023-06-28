import json
from collections import defaultdict
from threading import Thread
from urllib.parse import urljoin
from typing import Union, Optional, Literal, Callable, TypedDict, Any, List

from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from .settings import Settings
from .models.device import Device
from .balena_auth import request, get_token
from .pine import PineClient


class Log(TypedDict):
    message: str
    createdAt: int
    timestamp: int
    isStdErr: bool
    isSystem: bool
    serviceId: Optional[int]


class StreamingParser(Protocol):
    """
    This is low level class and is not meant to be used by end users directly.
    """

    def __init__(self, callback, error):
        self.callback = callback
        self.error = error
        self.pending = b""

    def dataReceived(self, data):
        obj = {}
        self.pending += data

        lines = self.pending.split(b"\n")
        self.pending = lines.pop()

        for line in lines:
            try:
                if line:
                    obj = json.loads(line)
            except Exception as e:
                self.transport.stopProducing()  # type: ignore
                self.transport.loseConnection()  # type: ignore

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

    def __init__(self, settings: Settings):
        self.__settings = settings

    def add(
        self,
        uuid: str,
        callback: Callable[[Log], None],
        error: Optional[Callable[[Any], None]] = None,
        count: Optional[Union[int, Literal["all"]]] = None,
    ):
        query = "stream=1"
        if count:
            query = f"stream=1&count={count}"

        url = urljoin(self.__settings.get("api_endpoint"), f"/device/v2/{uuid}/logs?{query}")
        headers = Headers({"Authorization": [f"Bearer {get_token(self.__settings)}"]})

        agent = Agent(reactor)
        req = agent.request(b"GET", url.encode(), headers, None)
        req.addCallback(cbRequest, callback, error)
        self.run()

        return req

    def run(self):
        if not reactor.running:  # type: ignore
            Thread(target=reactor.run, args=(False,)).start()  # type: ignore

    def stop(self, d):
        reactor.callFromThread(d.addCallback, cbDrop)  # type: ignore

    def stop_all(self):
        reactor.stop()  # type: ignore


class Logs:
    """
    This class implements functions that allow processing logs from device.

    """

    def __init__(self, pine: PineClient, settings: Settings):
        self.__subscriptions = defaultdict(list)
        self.__settings = settings
        self.__device = Device(pine, settings)
        self.__subscription_handler = Subscription(settings)

    def __exit__(self, exc_type, exc_value, traceback):
        reactor.stop()  # type: ignore

    def subscribe(
        self,
        uuid_or_id: Union[str, int],
        callback: Callable[[Log], None],
        error: Optional[Callable[[Any], None]] = None,
        count: Optional[Union[int, Literal["all"]]] = None,
    ) -> None:
        """
        Subscribe to device logs.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            callback (Callable[[Log], None]): this callback is called on receiving a message.
            error (Optional[Callable[[Any], None]]): this callback is called on an error event.
            count (Optional[Union[int, Literal["all"]]]): number of historical messages to include.
        """

        uuid = self.__device.get(uuid_or_id, {"$select": "uuid"})["uuid"]
        self.__subscriptions[uuid].append(self.__subscription_handler.add(uuid, callback, error, count))

    def history(self, uuid_or_id: Union[str, int], count: Optional[Union[int, Literal["all"]]] = None) -> List[Log]:
        """
        Get device logs history.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
            count (Optional[Union[int, Literal["all"]]]): number of historical messages to include.
        """
        uuid = self.__device.get(uuid_or_id, {"$select": "uuid"})["uuid"]
        qs = {}
        if count is not None:
            qs["count"] = count

        return request(method="GET", settings=self.__settings, path=f"/device/v2/{uuid}/logs", qs=qs)

    def unsubscribe(self, uuid_or_id: Union[str, int]) -> None:
        """
        Unsubscribe from device logs for a specific device.

        Args:
            uuid_or_id (Union[str, int]): device uuid (string) or id (int)
        """
        uuid = self.__device.get(uuid_or_id, {"$select": "uuid"})["uuid"]
        if uuid in self.__subscriptions:
            for d in self.__subscriptions[uuid]:
                self.__subscription_handler.stop(d)
            del self.__subscriptions[uuid]

    def unsubscribe_all(self) -> None:
        """
        Unsubscribe all subscribed devices.
        """
        for device in self.__subscriptions:
            for d in self.__subscriptions[device]:
                self.__subscription_handler.stop(d)
        self.__subscriptions = {}

    def stop(self) -> None:
        """
        Will grecefully unsubscribe from all devices and stop the consumer thread.
        """
        self.unsubscribe_all()
        self.__subscription_handler.stop_all()
