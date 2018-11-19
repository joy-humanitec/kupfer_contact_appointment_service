from django.conf.urls import url
from rest_framework import routers
from rest_framework.documentation import include_docs_urls

from contact import views as views_contacts
from appointment import views as views_apppointment

router = routers.SimpleRouter()

router.register(r'appointment', views_apppointment.AppointmentViewSet)
router.register(r'appointmentnotifications',
                views_apppointment.AppointmentNotificationViewSet)
router.register(r'contact', views_contacts.ContactViewSet)

urlpatterns = [
    url(r'^docs/', include_docs_urls(title='CRM Service')),
]

urlpatterns += router.urls
