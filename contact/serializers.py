from rest_framework import serializers
from .models import Contact


class ContactSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    organization_uuid = serializers.ReadOnlyField()
    title_display = serializers.CharField(source='get_title_display', read_only=True)

    def validate(self, attrs):
        """Validate Uniqueness of customer_id in organization."""
        customer_id = attrs.get('customer_id', None)
        organization_uuid = self.context['request'].session.get('jwt_organization_uuid')
        if customer_id and Contact.objects.filter(organization_uuid=organization_uuid, customer_id=customer_id):
            raise serializers.ValidationError('customer_id is not unique in organization')
        return super().validate(attrs)

    class Meta:
        model = Contact
        exclude = ('core_user_uuid',)


class ContactNameSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField()

    class Meta:
        model = Contact
        fields = ('uuid', 'first_name', 'middle_name', 'last_name', 'title', 'id')
