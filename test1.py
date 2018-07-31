from pprint import pformat

from twisted.internet import threads, reactor, defer , ssl, protocol
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.internet.ssl import ClientContextFactory, ContextFactory
from twisted.internet.endpoints import TCP4ClientEndpoint, SSL4ClientEndpoint


from threading import Thread
import time


def callback(result):
    print(result)
def err(error):
    print(error)

class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)

class BeginningPrinter(Protocol):
    def __init__(self, callback, err):
        self.callback = callback
        self.err = err

    def dataReceived(self, bytes):
        self.callback(bytes)

    def connectionLost(self, reason):
        if self.err:
            d = Deferred()
            d.addErrback(self.err)
            d.errback(DefaultException(reason.getErrorMessage()))

def cbRequest(response, callback, err):
    print(pformat(list(response.headers.getAllRawHeaders())))
    a = BeginningPrinter(callback, err)
    response.deliverBody(a)
    return a

def cbDrop(proto):
    print('=======IN======!')
    proto.transport.loseConnection()

class Closer(Protocol):
        def makeConnection(self, producer):
            producer.stopProducing()

def close(response):
    response.deliverBody(Closer())

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzI5ODYsInVzZXJuYW1lIjoicHl0aG9uc2RrX3Rlc3RfcmVzaW4iLCJlbWFpbCI6InB5dGhvbnNkay50ZXN0LnJlc2luQGdtYWlsLmNvbSIsImNyZWF0ZWRfYXQiOiIyMDE4LTAxLTMxVDA3OjUxOjM1LjYxMFoiLCJmaXJzdF9uYW1lIjoidHJvbmcgbmdoaWEiLCJsYXN0X25hbWUiOiJuZ3V5ZW4iLCJjb21wYW55IjoiIiwiand0X3NlY3JldCI6IkEyWUI2UFY0RUxTMjc1WlkyWUxYWExNSVFSWENTRDVGIiwiaGFzX2Rpc2FibGVkX25ld3NsZXR0ZXIiOmZhbHNlLCJzb2NpYWxfc2VydmljZV9hY2NvdW50IjpbXSwiaGFzUGFzc3dvcmRTZXQiOnRydWUsIm5lZWRzUGFzc3dvcmRSZXNldCI6ZmFsc2UsInB1YmxpY19rZXkiOnRydWUsImZlYXR1cmVzIjpbXSwiaW50ZXJjb21Vc2VyTmFtZSI6InB5dGhvbnNka190ZXN0X3Jlc2luIiwiaW50ZXJjb21Vc2VySGFzaCI6ImRmNjZjNDk5MTczNGM4ZDQ3YTUxOWU2NDM4YmYzNDUyZWMwZGRhMDVhOGNhOWY0NTY4MDQyZjM2ZDNiYjc1MDQiLCJwZXJtaXNzaW9ucyI6W10sImF1dGhUaW1lIjoxNTMyMDI3MzM2NDc1LCJhY3RvciI6MjQ1NDA5NSwiaWF0IjoxNTMyNzI1MjI2LCJleHAiOjE1MzMzMzAwMjZ9.JGeMPrJ6csnB9YwiRfoKlHTHWNs-grVu5lbYTENETBU'
url = 'https://api.resin.io/device/v2/{0}/logs?stream=1&count=10'.format('3ddd4d42bf38e54b4d6b4cc8418fe606').encode()
url1 = b'http://localhost:8080'
url2 = b'https://api.resin.io/v4/device'
url3 = b'http://google.com'

headers = {}
headers[b'Authorization'] = [bytes("Bearer "+ token, 'utf-8')]

contextFactory = WebClientContextFactory()

agent = Agent(reactor, contextFactory)
d = agent.request(b'GET', url, Headers(headers), None)
d.addCallback(cbRequest, callback, err)
#d.addCallback(cbDrop)
#d2 = agent.request('GET', url, Headers(headers), None)
#d2.addCallback(cbRequest, callback, err)
#reactor.run()
Thread(target=reactor.run, args=(False,)).start()

#time.sleep(30)
#reactor.stop()
#print('stopped')
#reactor.run()
