from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import View

from users.choices import UserRole


class IsSystemUserOrOwner(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.role in [
            UserRole.system_admin,
            UserRole.system_user,
            UserRole.owner,
        ]
