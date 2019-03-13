from django.contrib import admin
from .models import Contact


class ContactAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'core_user_uuid', 'title', 'first_name', 'last_name',
                    'company', 'phones',  'emails', )
    list_filter = ('title', )
    search_fields = ('first_name', 'last_name', 'emails', 'company', )


admin.site.register(Contact, ContactAdmin)
