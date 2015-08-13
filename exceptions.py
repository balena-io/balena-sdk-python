# coding: utf-8

class APIException(Exception):
    pass


class JSONDecodeError(Exception):
	def __init__(self):
		self.code = 'JSONDecodeError'
		self.exit_code = 1
		self.message = ''


class NoTokenProvided(Exception):
    pass


class ResponseError(Exception):
    pass


class RequestError(Exception):
    pass
