"""
Role-based permissions for ASC DocTrack.

superadmin      → full CRUD on everything
records_officer → manage all documents (forward, status, classify)
program_chair   → forward docs, view all docs in their department
faculty         → submit docs, view own submissions only
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.is_superadmin)


class IsRecordsAdmin(BasePermission):
    """Records officer or superadmin."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.is_records_admin)


class IsRecordsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_records_admin


class CanForwardDocument(BasePermission):
    """Records officer, superadmin, or program chair can forward."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_records_admin or request.user.is_program_chair


class CanViewDocument(BasePermission):
    """
    Not currently wired into any view (DocumentViewSet enforces visibility
    via get_queryset() → Document.objects.visible_to() instead) — kept for
    any future view that wants an object-level check. Delegates to
    Document.is_visible_to so there's exactly one definition of "can this
    user see this document", not a second copy that can drift out of sync.
    """
    def has_object_permission(self, request, view, obj):
        return obj.is_visible_to(request.user)


class CanDownloadDocument(BasePermission):
    """Not currently wired into any view — see CanViewDocument above."""
    def has_object_permission(self, request, view, obj):
        return obj.is_downloadable_by(request.user)
