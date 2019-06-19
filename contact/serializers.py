from rest_framework import serializers
from .models import Contact, Type


class TypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Type
        exclude = ('organization_uuid', )


class ContactSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    organization_uuid = serializers.ReadOnlyField()
    title_display = serializers.CharField(source='get_title_display', read_only=True)
    contact_type = TypeSerializer(read_only=True)

    class Meta:
        model = Contact
        exclude = ('core_user_uuid', )


class ContactNameSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField()

    class Meta:
        model = Contact
        fields = ('uuid', 'first_name', 'middle_name', 'last_name', 'title', 'id')
