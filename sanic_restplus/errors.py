# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from sanic import exceptions

__all__ = (
    'abort',
    'RestError',
    'ValidationError',
    'SpecsError',
)


def abort(code=500, message=None, **kwargs):
    '''
    Properly abort the current request.

    Raise a `HTTPException` for the given status `code`.
    Attach any keyword arguments to the exception for later processing.

    :param int code: The associated HTTP status code
    :param str message: An optional details message
    :param kwargs: Any additional data to pass to the error payload
    :raise HTTPException:
    '''
    raise exceptions.SanicException(message=message, status_code=code)

class RestError(Exception):
    '''Base class for all Flask-Restplus Errors'''
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class ValidationError(RestError):
    '''An helper class for validation errors.'''
    pass


class SpecsError(RestError):
    '''An helper class for incoherent specifications.'''
    pass
