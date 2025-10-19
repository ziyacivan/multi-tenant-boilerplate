from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and hasattr(exc, "get_full_details"):
        response.data = exc.get_full_details()

    return response


class BaseAPIException(exceptions.APIException):
    def __init__(self, detail=None, code=None, **kwargs) -> None:
        self.extra_parameters = kwargs.copy()

        if detail is None and kwargs:
            detail = str(self.default_detail).format(**kwargs)

            if code is not None:
                self.default_code = code

        super().__init__(detail, self.default_code)

    def get_full_details(self):
        details = {
            "detail": self.detail,
            "code": self.default_code,
        }

        if self.extra_parameters:
            details["parameters"] = self.extra_parameters

        return details
