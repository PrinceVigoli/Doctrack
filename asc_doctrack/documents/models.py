from django.db import models
from django.db.models import Q
from accounts.models import User, Office


class DocumentQuerySet(models.QuerySet):
    def visible_to(self, user):
        """
        SECURITY: single source of truth for "can this user see this document
        at all" — used by DocumentViewSet (list/retrieve and every @action
        that calls get_object), DocumentQRView, and the tracking WebSocket
        consumer. Do not reimplement this check elsewhere; route new access
        points through here instead so the policy can't drift out of sync
        again (which is how the original bug happened).

        Mirrors the policy documented in documents/permissions.py:
          superadmin / records_officer → everything, including RESTRICTED
          program_chair                → their own submissions, plus
                                          anything currently in their office
          faculty (and everyone else)  → their own submissions only
        """
        if user.is_records_admin:
            return self.all()

        qs = self.exclude(confidentiality=self.model.Confidentiality.RESTRICTED)

        visible = Q(submitted_by=user)
        if user.is_program_chair and user.office_id:
            visible |= Q(current_office_id=user.office_id)

        return qs.filter(visible)


class DocumentType(models.Model):
    name      = models.CharField(max_length=100, unique=True)
    code      = models.CharField(max_length=20,  unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Document(models.Model):

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        IN_REVIEW = 'in_review', 'In Review'
        APPROVED  = 'approved',  'Approved'
        REJECTED  = 'rejected',  'Rejected'
        RETURNED  = 'returned',  'Returned'
        COMPLETED = 'completed', 'Completed'

    class Priority(models.TextChoices):
        LOW    = 'low',    'Low'
        NORMAL = 'normal', 'Normal'
        HIGH   = 'high',   'High'
        URGENT = 'urgent', 'Urgent'

    class CommType(models.TextChoices):
        INTERNAL = 'internal', 'Internal'   # between ASC offices
        EXTERNAL = 'external', 'External'   # to/from outside organizations
        NA       = 'n/a',      'Not Applicable'

    class Confidentiality(models.TextChoices):
        PUBLIC     = 'public',     'Public'      # all employees can view & download
        INTERNAL   = 'internal',   'Internal'    # ASC employees only, no download
        RESTRICTED = 'restricted', 'Restricted'  # Records Office eyes only

    # ── Identity ─────────────────────────────────────────────
    tracking_number = models.CharField(max_length=30, unique=True, editable=False)
    title           = models.CharField(max_length=255)
    description     = models.TextField(blank=True)

    # ── Classification ────────────────────────────────────────
    doc_type        = models.ForeignKey(DocumentType, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='documents')
    ai_label        = models.CharField(max_length=100, blank=True)
    ai_confidence   = models.FloatField(null=True, blank=True)

    # ── NEW: Communication type (internal / external) ─────────
    comm_type       = models.CharField(
        max_length=10, choices=CommType.choices, default=CommType.NA,
        verbose_name='Communication type',
        help_text='For letters and memos: is this between ASC offices (internal) or an outside org (external)?'
    )

    # ── NEW: Confidentiality level ────────────────────────────
    confidentiality = models.CharField(
        max_length=12, choices=Confidentiality.choices, default=Confidentiality.INTERNAL,
        help_text=(
            'Public = anyone can view and download. '
            'Internal = ASC employees can view but not download. '
            'Restricted = Records Office only (e.g. complaints, grievances, personnel matters).'
        )
    )
    confidentiality_note = models.TextField(
        blank=True,
        help_text='Optional note explaining why this is restricted (not shown to employees).'
    )

    # ── Routing ───────────────────────────────────────────────
    origin_office      = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True,
                                           related_name='outgoing_docs')
    current_office     = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True,
                                           related_name='current_docs')
    destination_office = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True,
                                           blank=True, related_name='incoming_docs')

    # ── Status & priority ────────────────────────────────────
    status   = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)

    # ── People ────────────────────────────────────────────────
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     related_name='submitted_docs')
    assigned_to  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='assigned_docs')

    # ── File ─────────────────────────────────────────────────
    file      = models.FileField(upload_to='documents/%Y/%m/')
    file_size = models.PositiveBigIntegerField(null=True, blank=True)

    # ── Timestamps ───────────────────────────────────────────
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    due_date     = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    objects = DocumentQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self._generate_tracking_number()
        if self.file and not self.file_size:
            try: self.file_size = self.file.size
            except: pass
        super().save(*args, **kwargs)

    def _generate_tracking_number(self):
        import uuid, datetime
        prefix = datetime.datetime.now().strftime('%Y%m')
        uid    = str(uuid.uuid4()).upper()[:6]
        return f"ASC-{prefix}-{uid}"

    @property
    def is_downloadable_by(self):
        """Return a callable that checks if a user can download this document."""
        def check(user):
            if user.is_records_admin:
                return True
            return self.confidentiality == self.Confidentiality.PUBLIC
        return check

    @property
    def is_visible_to(self):
        """Return a callable that checks if a user can see this document at all."""
        def check(user):
            if user.is_records_admin:
                return True
            return Document.objects.visible_to(user).filter(pk=self.pk).exists()
        return check

    def __str__(self):
        return f"[{self.tracking_number}] {self.title}"


class DocumentComment(models.Model):
    document   = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    author     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    body       = models.TextField()
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.document.tracking_number}"
