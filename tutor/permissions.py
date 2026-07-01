from rest_framework.permissions import BasePermission


class IsStaffUser(BasePermission):
    """Staff-only access for admin API routes."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )
