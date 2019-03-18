from rest_framework import serializers
from .models import Contact


class ContactSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    organization_uuid = serializers.ReadOnlyField()
    title_display = serializers.CharField(source='get_title_display', read_only=True)

    class Meta:
        model = Contact
        exclude = ('core_user_uuid',)


class ContactNameSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField()

    class Meta:
        model = Contact
        fields = ('uuid', 'first_name', 'middle_name', 'last_name')


class ContactIndexSerializer(serializers.ModelSerializer):
    """
    Serializer for saving to ElasticSearchIndex.
    """
    organization_uuid = serializers.ReadOnlyField()

    class Meta:
        model = Contact
        fields = '__all__'
