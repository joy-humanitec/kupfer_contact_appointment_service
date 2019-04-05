from rest_framework import filters


class StartsWithSearchFilter(filters.SearchFilter):

    search_param = 'starts_with'

    def get_search_fields(self, view, request):
        starts_with_search_fields = ('^first_name', '^last_name')
        return starts_with_search_fields
