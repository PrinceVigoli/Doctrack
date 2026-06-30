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
    def has_object_permission(self, request, view, obj):
        if request.user.is_records_admin or request.user.is_superadmin:
            return True
        from documents.models import Document
        return obj.confidentiality != Document.Confidentiality.RESTRICTED


class CanDownloadDocument(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_records_admin or request.user.is_superadmin:
            return True
        from documents.models import Document
        return obj.confidentiality == Document.Confidentiality.PUBLIC
