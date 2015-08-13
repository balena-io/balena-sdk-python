import requests
import json
import resin
import urllib
from string import Template

from urlparse import urljoin

from .settings import Settings
from .token  import Token
from .resources import Message

from exceptions import (
    JSONDecodeError,
    NoTokenProvided,
    ResponseError,
    RequestError
)


class BaseRequest(object):

    def __init__(self):
        self.settings = Settings()
        self.token = Token()
        self.util = Util()

    def __str__(self):
        return b'<{:s} at {:#x}>'.format(type(self).__name__, id(self))

    def __set_content_type(self, headers, ctype):
        headers.update({'content-type': ctype})

    def __set_authorization(self, headers):
        headers.update({'Authorization': 'Bearer {:s}'.format(self.token.get())})

    def __get(self, url, headers, data=None, stream=None):
        return requests.get(url, headers=headers)

    def __post(self, url, headers, data, stream=None):
        self.__set_content_type(headers, 'application/json')
        if not stream:
            return requests.post(url,data=json.dumps(data), headers=headers)
        else:
            return requests.post(url,data=json.dumps(data), headers=headers, stream=stream)

    def __put(self, url, headers, data=None, stream=None):
        self.__set_content_type(headers, 'application/json')
        return requests.put(url, data=json.dumps(data), headers=headers)

    def __patch(self, url, headers, data=None, stream=None):
        self.__set_content_type(headers, 'application/json')
        return requests.patch(url, data=json.dumps(data), headers=headers)

    def __delete(self, url, headers, data=None, stream=None):
        self.__set_content_type(headers, 'application/x-www-form-urlencoded')
        return requests.delete(url, headers=headers)

    def __head(self, url, headers, data=None, stream=None):
        return requests.head(url, headers=headers)

    def format_params(self, params):
        if params:
            if params.has_key('expand'):
                query_template = Template("?$$expand=$expand($$filter=$filter%20eq%20'$eq')")
            elif params.has_key('filter'):
                query_template = Template("?$$filter=$filter%20eq%20'$eq'")
            else:
                query_template = Template("") 
            return query_template.safe_substitute(params)

    def __request(self, url, method, params, endpoint, headers=None, data=None, stream=None, auth=True):
        headers = headers or {}

        METHODS = {
            'get': self.__get,
            'post': self.__post,
            'put': self.__put,
            'delete': self.__delete,
            'head': self.__head,
            'patch': self.__patch
        }

        if auth:
            self.__set_authorization(headers)

        request_method = METHODS[method.lower()]
        url = urljoin(endpoint, url)
        params = self.format_params(params)
        url = urljoin(url, params)
        return request_method(url, headers=headers, data=data, stream=stream)

    def request(self, url, method, endpoint, params=None, data=None, stream=None, auth=True):
        if auth:
            if not self.token.has():
                # TODO: need exception if no token provided
                pass

            if self.util.should_update_token(self.token.get_age(),self.settings.get('token_refresh_interval')):
                self.token.set(self.request_new_token())

        params = params or {}
        data = data or {}
        # About response obj: https://github.com/kennethreitz/requests/blob/master/requests/models.py#L525
        response = self.__request(url, method, params, endpoint, data=data, stream=stream, auth=auth)
        # FOR TESTING ONLY
        #print response.status_code
        #print response.reason
        #print response.content
        #print response.url
        #
        if response.status_code == 201:
            return response.content
        # 204: no content
        if response.status_code == 204:
            return
        # 200: OK
        if response.status_code == 200 and response.content == 'OK':
            return
        if not response.ok:
            if response.status_code >= 500:
                raise ResponseError('Server did not respond. {:d} {:s}'.format(response.status_code, response.reason))

            raise RequestError('{:d} {:s}. Message: {:s}'.format(response.status_code, response.reason, response._content))
        try:
            json = response.json()
        except ValueError:
            return response.content  

        return json

    def request_new_token(self):
        headers = {}
        self.__set_authorization(headers)
        url = urljoin(self.settings.get('api_endpoint'), 'whoami')
        response = requests.get(url, headers=headers)
        return response.content


class Util(object):

    def should_update_token(self, age, token_fresh_interval):
        return bool(age >= token_fresh_interval)
