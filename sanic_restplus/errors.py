# -*- coding: utf-8 -*-
#
from sanic import exceptions

from ._http import HTTPStatus

__all__ = ("abort", "RestError", "ValidationError", "SpecsError")


def abort(code=HTTPStatus.INTERNAL_SERVER_ERROR, message=None, **kwargs):
    """
    Properly abort the current request.

    Raise a `HTTPException` for the given status `code`.
    Attach any keyword arguments to the exception for later processing.

    :param int code: The associated HTTP status code
    :param str message: An optional details message
    :param kwargs: Any additional data to pass to the error payload
    :raise HTTPException:
    """

    try:
        exceptions.abort(status_code=code, message=message)
    except Exception as ex:
        data = {"message": message, **kwargs} if message else {**kwargs}
        if data:
            ex.data = data
        raise ex


class RestError(Exception):
    """Base class for all Flask-Restplus Errors"""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class ValidationError(RestError):
    """An helper class for validation errors."""

    pass


class SpecsError(RestError):
    """An helper class for incoherent specifications."""

    pass
