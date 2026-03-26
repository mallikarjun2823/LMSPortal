from rest_framework.permissions import BasePermission


class CoursePermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        user_role_num = getattr(getattr(user, 'role', None), 'role_num', None)
        if getattr(user, 'is_authenticated', False) and user_role_num == 1:
            return True
        return False