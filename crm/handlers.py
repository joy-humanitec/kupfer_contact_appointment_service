from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import JsonResponse
from rest_framework.views import exception_handler
from rest_framework import status


def custom_exception_handler(exception, context):
    if isinstance(exception, ValidationError):
        return JsonResponse(data=exception.message_dict,
                            status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exception, IntegrityError):
        return JsonResponse(data={'cause': str(exception.__cause__)},
                            status=status.HTTP_400_BAD_REQUEST)
    # Call REST framework's default exception handler
    response = exception_handler(exception, context)
    return response
