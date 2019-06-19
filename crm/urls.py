from rest_framework import routers

from contact import views as views_contacts
from appointment import views as views_apppointment

router = routers.SimpleRouter()

router.register(r'appointment', views_apppointment.AppointmentViewSet)
router.register(r'appointmentnotes', views_apppointment.AppointmentNoteViewSet)
router.register(r'appointmentnotifications', views_apppointment.AppointmentNotificationViewSet)
router.register(r'appointmentdrivingtimes', views_apppointment.AppointmentDrivingTimeViewSet)
router.register(r'contact', views_contacts.ContactViewSet)

urlpatterns = router.urls
