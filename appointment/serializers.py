import logging

from rest_framework import serializers

from contact.models import Contact
from contact.serializers import ContactNameSerializer
from .models import Appointment, AppointmentNotification

logger = logging.getLogger(__name__)


class ContactNameField(serializers.ReadOnlyField):
    def get_attribute(self, obj):
        if obj.contact_uuid:
            try:
                contact = Contact.objects.get(uuid=obj.contact_uuid)
            except Contact.DoesNotExist:
                logger.warning('Missing database record. Appointment has a '
                               'reference to a non existing Contact. UUID: {}'.
                               format(obj.contact_uuid))
            else:
                contact_serizalizer = ContactNameSerializer(contact)
                return contact_serizalizer.data


class AppointmentSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    def validate_type(self, value):
        if not value:
            raise serializers.ValidationError(
                'type must be an array of one or more string elements')
        return value

    def validate_organization_uuid(self, value):
        if value:
            request = self.context['request']
            user_org_uuid = request.session.get('jwt_organization_uuid')
            if user_org_uuid != str(value):
                raise serializers.ValidationError(
                    'The Organization cannot be different than user\'s '
                    'organization')
        return value

    class Meta:
        model = Appointment
        exclude = ('owner',)


class AppointmentDenormalizedSerializer(serializers.HyperlinkedModelSerializer):  # noqa
    id = serializers.ReadOnlyField()
    contact = ContactNameField()

    class Meta:
        model = Appointment
        extra_fields = ['invitees']
        exclude = ('owner',)


class AppointmentNotificationSerializer(serializers.HyperlinkedModelSerializer):  # noqa
    id = serializers.ReadOnlyField()
    sent_at = serializers.ReadOnlyField()

    class Meta:
        model = AppointmentNotification
        fields = '__all__'
