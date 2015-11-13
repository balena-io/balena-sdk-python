import requests
import json
import urllib
from string import Template
import os

from urlparse import urljoin

from .settings import Settings
from .token import Token

from . import exceptions


class BaseRequest(object):
    """
    This class provides an exclusive client to make HTTP requests to Resin.io servers.
    This is low level class and is not meant to be used by end users directly.

    """

    def __init__(self):
        self.settings = Settings()
        self.token = Token()
        self.util = Util()

    def __str__(self):
        return b'<{:s} at {:#x}>'.format(type(self).__name__, id(self))

    def __set_content_type(self, headers, ctype):
        headers.update({'Content-Type': ctype})

    def __set_authorization(self, headers):
        headers.update(
            {'Authorization': 'Bearer {:s}'.format(self.token.get())})

    def __get(self, url, headers, data=None, stream=None):
        return requests.get(url, headers=headers)

    def __post(self, url, headers, data, stream=None):
        self.__set_content_type(headers, 'application/json')
        if not stream:
            return requests.post(url, data=json.dumps(data), headers=headers)
        else:
            return requests.post(
                url, data=json.dumps(data), headers=headers, stream=stream)

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

    def _format_params(self, params, api_key):
        query_elements = []
        if api_key:
            query_elements.append('apikey={0}'.format(api_key))
        if params:
            if 'expand' in params:
                query_template = Template(
                    "$$expand=$expand($$filter=$filter%20eq%20'$eq')")
            elif 'filter' in params:
                query_template = Template("$$filter=$filter%20eq%20'$eq'")
            else:
                query_template = Template("")
            query_elements.append(query_template.safe_substitute(params))
        if query_elements:
            return '?{0}'.format('&'.join(query_elements))

    def __request(self, url, method, params, endpoint, headers=None,
                  data=None, stream=None, auth=True, api_key=None):
        """
        This function forms HTTP request and send to Resin.io.
        Resin.io host is prepended automatically, therefore only relative urls should be passed.

        Args:
            url (str): relative url.
            method (str): HTTP methods. Available methods are: GET, POST , PUT, PATCH, DELETE, HEAD.
            endpoint (str): target resin.io host. Available endpoints are saved in settings.
            params (Optional[dict]): parameters to generate query.
            data (Optional[dict]): request body.
            stream (Optional[bool]): this argument is set to True when needing to stream the response content.
            auth (Optional[bool]): default is True. This marks the request need to be authenticated or not.
            api_key (Optional[str]): default is None. Resin API Key.

        Returns:
            object: response object.
                if stream arg is set to True, the whole response object is returned.
                if JSON is returned from response, json parsed object is returned.
                otherwise response content is returned.

        Raises:
            RequestError: if any errors occur.

        """

        headers = headers or {}

        METHODS = {
            'get': self.__get,
            'post': self.__post,
            'put': self.__put,
            'delete': self.__delete,
            'head': self.__head,
            'patch': self.__patch
        }
        request_method = METHODS[method.lower()]
        url = urljoin(endpoint, url)
        if auth:
            if not api_key:
                self.__set_authorization(headers)
            params = self._format_params(params, api_key=api_key)
        else:
            params = self._format_params(params, api_key=None)

        url = urljoin(url, params)
        return request_method(url, headers=headers, data=data, stream=stream)

    def request(self, url, method, endpoint, params=None, data=None,
                stream=None, auth=True, login=False, api_key=None):
        if api_key is None:
            api_key = self.util.get_api_key()

        # Some requests require logging in using credentials or Auth Token to process
        if login:
            api_key = None
            auth = True

        if auth and not api_key:
            if not self.token.has():
                if login:
                    raise exceptions.NotLoggedIn()
                else:
                    raise exceptions.Unauthorized()

            if self.util.should_update_token(
                self.token.get_age(),
                self.settings.get('token_refresh_interval')
            ):
                self.token.set(self._request_new_token())
        params = params or {}
        data = data or {}
        # About response obj:
        # https://github.com/kennethreitz/requests/blob/master/requests/models.py#L525
        response = self.__request(url, method, params, endpoint, data=data,
                                  stream=stream, auth=auth, api_key=api_key)

        if stream:
            return response

        if response.status_code == 201:
            return response.content
        # 204: no content
        if response.status_code == 204:
            return

        # 200: OK
        if response.status_code == 200 and response.content == 'OK':
            return response.content
        if not response.ok:
            raise exceptions.RequestError(response._content)

        try:
            json = response.json()
        except ValueError:
            return response.content

        return json

    def _request_new_token(self):
        headers = {}
        self.__set_authorization(headers)
        url = urljoin(self.settings.get('api_endpoint'), 'whoami')
        response = requests.get(url, headers=headers)
        if not response.ok:
            raise exceptions.RequestError(response._content)
        return response.content


class Util(object):

    def should_update_token(self, age, token_fresh_interval):
        return int(age) >= int(token_fresh_interval)

    def get_api_key(self):
        # return None if key is not present
        return os.environ.get('RESIN_API_KEY')
