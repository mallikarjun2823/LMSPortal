from rest_framework.permissions import BasePermission


class CoursePermission(BasePermission):
    """Permission check: only instructors can create/edit/delete courses."""
    def has_permission(self, request, view):
        user = request.user
        user_role_num = getattr(getattr(user, 'role', None), 'role_num', None)
        if getattr(user, 'is_authenticated', False) and user_role_num == 'INST':
            return True
        return False