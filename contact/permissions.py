from rest_framework.exceptions import PermissionDenied
from crm.permissions import AllowOptionsAuthentication


class ContactPermission(AllowOptionsAuthentication):
    def has_permission(self, request, view):
        return super(ContactPermission, self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        organization_uuid = obj.organization_uuid
        if getattr(request, 'session', None) and \
                request.session.get('jwt_organization_uuid') == \
                organization_uuid:
            return True
        else:
            raise PermissionDenied('User is not in the same organization as '
                                   'the object.')
