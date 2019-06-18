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
            if request.session.get('jwt_core_user_uuid') == \
                    str(obj.owner):
                return True

            if request.session.get('jwt_organization_uuid') == \
                    str(obj.organization_uuid):
                return True
            else:
                raise PermissionDenied('User is not in the same organization '
                                       'as the object.')


class AppointmentNoteOrganizationPermission(OrganizationPermission):
    def has_object_permission(self, request, view, appointmentnote):
        if request.user.is_superuser:
            return True
        # the appointment-lookup is not optimal due to M2M, should be FK on Appointment
        if appointmentnote.appointment_set.count() and \
                request.session.get('jwt_organization_uuid') == str(
                appointmentnote.appointment_set.first().organization_uuid):
            return True
        else:
            raise PermissionDenied('User is not in the same organization '
                                   'as the object.')


class AppointmentRelatedModelPermission(OrganizationPermission):
    def has_permission(self, request, view):
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj.appointment)
