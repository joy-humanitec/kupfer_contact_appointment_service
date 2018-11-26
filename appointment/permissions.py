from rest_framework.exceptions import PermissionDenied
from crm.permissions import AllowOptionsAuthentication


class OrganizationPermission(AllowOptionsAuthentication):
    def has_permission(self, request, view):
        return super(OrganizationPermission, self).has_permission(request,
                                                                  view)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if getattr(request, 'session', None):
            if request.session.get('jwt_user_uuid') == \
                    str(obj.owner):
                return True

            if request.session.get('jwt_organization_uuid') == \
                    str(obj.organization_uuid):
                return True
            else:
                raise PermissionDenied('User is not in the same organization '
                                       'as the object.')


class AppointmentNotificationPermission(OrganizationPermission):
    def has_permission(self, request, view):
        return super(AppointmentNotificationPermission,
                     self).has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return super(
            AppointmentNotificationPermission, self).has_object_permission(
            request, view, obj.appointment)
