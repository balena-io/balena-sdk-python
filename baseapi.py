import requests
import json
import resin
from urlparse import urljoin

from exceptions import (
    JSONDecodeError,
    NoTokenProvided,
    ResponseError,
    RequestError
)


class BaseAPI(object):

    """
    This is a python library for accessing the resin api
    http://github.com/craig-mulligan/resin-api-python
    Usage:
        import resin_io
        c = resin_io.Connection('{{JWT}}')
    """

    endpoint = 'https://api.resinstaging.io/ewa/'

    def __init__(self, token=None):
        self.token = token

    def __str__(self):
        return b'<{:s} at {:#x}>'.format(type(self).__name__, id(self))

    def __unicode__(self):
        return '<{:s} at {:#x}>'.format(type(self).__name__, id(self))

    def __set_content_type(self, headers, ctype):
        headers.update({'content-type': ctype})

    def __set_authorization(self, headers):
        if not self.token:
            raise NoTokenProvided()

        headers.update({'Authorization': 'Bearer {:s}'.format(self.token)})

    def __get(self, url, headers, data):
        return requests.get(url, headers=headers)

    def __post(self, url, headers, data):
        self.__set_content_type(headers, 'application/json')
        return requests.post(url,data=json.dumps(data), headers=headers)

    def __put(self, url, headers, data):
        self.__set_content_type(headers, 'application/json')
        return requests.put(url, headers=headers)

    def __delete(self, url, headers, data):
        self.__set_content_type(headers, 'application/x-www-form-urlencoded')
        return requests.delete(url, headers=headers)

    def __head(self, url, headers, data):
        return requests.head(url, headers=headers)

    def format_params(self, params):
    	#TODO: make more effecient
        if params:
            if params.has_key('expand'):
                query = "?$expand=" + \
                        params[
                            "expand"] + "($filter=" + params['filter'] + "%20eq%20'" + str(params["eq"]) + "')"
            elif params.has_key('filter'):
                query = "?$filter=" + params["filter"] + \
                    "%20eq%20'" + str(params["eq"]) + "'"
            else:
                query = ""
            print query
            return query

    def __request(self, url, method, params, headers=None, data=None):
        headers = headers or {}

        METHODS = {
            'get': self.__get,
            'post': self.__post,
            'put': self.__put,
            'delete': self.__delete,
            'head': self.__head
        }

        self.__set_authorization(headers)

        request_method = METHODS[method.lower()]
        url = urljoin(self.endpoint, url)
        params = self.format_params(params)
        url = urljoin(url, params)
        print url
        return request_method(url, headers=headers, data=data)

    def request(self, url, method, params=None, data=None):
        params = params or {}
        data = data or {}
        # About response obj: https://github.com/kennethreitz/requests/blob/master/requests/models.py#L525
        response = self.__request(url, method, params, data=data)
        
        if response.status_code == 201:
            return response.content
        # 204: no content - 200: OK
        if response.status_code == 204 or response.status_code == 200:
            return
        if not response.ok:
            if response.status_code >= 500:
                raise ResponseError('Server did not respond. {:d} {:s}'.format(response.status_code, response.reason))

            raise RequestError('{:d} {:s}. Message: {:s}'.format(response.status_code, response.reason, response._content))
        try:
            json = response.json()
        except ValueError:
            raise JSONDecodeError()   

        return json['d']
