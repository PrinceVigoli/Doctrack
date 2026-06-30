from django.db import models
from django.core.exceptions import PermissionDenied
from documents.models import Document
from accounts.models import User, Office


class TrackingLog(models.Model):
    """
    Immutable audit trail — one entry per status change or office transfer.

    Deletion is intentionally blocked. Records are the authoritative history
    of a document's lifecycle and must not be removed. Use the Django admin
    to view logs; do not expose a delete endpoint.
    """

    class Action(models.TextChoices):
        SUBMITTED   = 'submitted',   'Submitted'
        FORWARDED   = 'forwarded',   'Forwarded'
        RECEIVED    = 'received',    'Received'
        IN_REVIEW   = 'in_review',   'In Review'
        APPROVED    = 'approved',    'Approved'
        REJECTED    = 'rejected',    'Rejected'
        RETURNED    = 'returned',    'Returned'
        COMPLETED   = 'completed',   'Completed'
        COMMENTED   = 'commented',   'Commented'

    document     = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='logs')
    action       = models.CharField(max_length=20, choices=Action.choices)
    actor        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    from_office  = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='outgoing_logs')
    to_office    = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='incoming_logs')
    note         = models.TextField(blank=True)
    timestamp    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering           = ['timestamp']
        default_permissions = ('view', 'add')   # no 'change' or 'delete' in admin

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Tracking logs are immutable and cannot be deleted.")

    def __str__(self):
        return f"{self.document.tracking_number} → {self.action} @ {self.timestamp:%Y-%m-%d %H:%M}"
