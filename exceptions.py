# coding: utf-8

class APIException(Exception):
    pass


class JSONDecodeError(APIException):
	pass


class NoTokenProvided(APIException):
    pass


class ResponseError(APIException):
    pass


class RequestError(APIException):
    pass