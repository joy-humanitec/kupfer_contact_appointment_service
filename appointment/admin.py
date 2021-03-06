from django.contrib import admin
from .models import Appointment, AppointmentNotification, AppointmentNote


class AppointmentAdmin(admin.ModelAdmin):
    pass


class AppointmentNotificationAdmin(admin.ModelAdmin):
    pass


admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(AppointmentNotification, AppointmentNotificationAdmin)
admin.site.register(AppointmentNote)
