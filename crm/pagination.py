from rest_framework.pagination import CursorPagination, LimitOffsetPagination


class ContactLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 7000


class AppointmentCursorPagination(CursorPagination):
    page_size = 30
    max_page_size = 2000
    page_size_query_param = 'page_size'
