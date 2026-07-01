from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.http import FileResponse
from django.utils import timezone
from .models import Document, DocumentType, DocumentComment
from .serializers import (
    DocumentListSerializer, DocumentDetailSerializer,
    DocumentCreateSerializer, DocumentTypeSerializer,
    DocumentCommentSerializer,
)
from .permissions import IsRecordsAdminOrReadOnly, IsRecordsAdmin
from tracking.models import TrackingLog
from classifier.routing    import suggest_routing
from classifier.priority   import detect_priority
from classifier.duplicates import check_duplicates


# Maps Document.Status values → valid TrackingLog.Action values
_STATUS_TO_ACTION = {
    Document.Status.IN_REVIEW: TrackingLog.Action.IN_REVIEW,
    Document.Status.APPROVED:  TrackingLog.Action.APPROVED,
    Document.Status.REJECTED:  TrackingLog.Action.REJECTED,
    Document.Status.RETURNED:  TrackingLog.Action.RETURNED,
    Document.Status.COMPLETED: TrackingLog.Action.COMPLETED,
    Document.Status.PENDING:   TrackingLog.Action.RECEIVED,
}


class DocumentTypeViewSet(ModelViewSet):
    queryset           = DocumentType.objects.filter(is_active=True)
    serializer_class   = DocumentTypeSerializer
    permission_classes = [IsRecordsAdminOrReadOnly]


class DocumentViewSet(ModelViewSet):
    permission_classes = [IsRecordsAdminOrReadOnly]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['title', 'tracking_number', 'description']
    ordering_fields    = ['created_at', 'updated_at', 'status', 'priority']
    ordering           = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        # SECURITY: visible_to() applies ownership/office scoping for non-admins
        # (see Document.objects.visible_to / documents/permissions.py docstring).
        # This is the single enforcement point — get_object() (used by retrieve
        # and every detail @action below) is keyed off this queryset, so fixing
        # it here is sufficient; no separate object-level RESTRICTED check is
        # needed any more.
        qs = Document.objects.visible_to(user).select_related(
            'doc_type', 'submitted_by', 'current_office',
            'origin_office', 'destination_office', 'assigned_to'
        ).prefetch_related('comments', 'logs')

        for param, field in [
            ('status',          'status'),
            ('priority',        'priority'),
            ('office',          'current_office__id'),
            ('doc_type',        'doc_type__id'),
            ('comm_type',       'comm_type'),
            ('confidentiality', 'confidentiality'),
        ]:
            val = self.request.query_params.get(param)
            if val:
                qs = qs.filter(**{field: val})
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentCreateSerializer
        if self.action in ['retrieve', 'update', 'partial_update']:
            return DocumentDetailSerializer
        return DocumentListSerializer

    def get_permissions(self):
        # Any authenticated user may submit a document
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        # Only records admins may edit, delete, change status, or set confidentiality
        if self.action in ['update', 'partial_update', 'destroy',
                           'update_status', 'set_confidentiality']:
            return [IsRecordsAdmin()]
        # Records officers and program chairs can forward
        if self.action == 'forward':
            from .permissions import CanForwardDocument
            return [CanForwardDocument()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        doc  = serializer.save(
            submitted_by   = user,
            origin_office  = user.office,
            current_office = user.office,
        )

        # Priority detection is fast (regex only) — run synchronously
        priority_result = detect_priority(doc)
        if priority_result['suggested_priority'] != 'normal':
            doc.priority = priority_result['suggested_priority']
            doc.save(update_fields=['priority'])

        # AI classification runs in the background (non-blocking)
        from notifications.tasks import classify_document_async
        classify_document_async.delay(doc.id)

        # Audit log — the post_save signal on TrackingLog fires push notifications
        TrackingLog.objects.create(
            document    = doc,
            action      = TrackingLog.Action.SUBMITTED,
            actor       = user,
            from_office = user.office,
            to_office   = doc.destination_office,
            note        = 'Document submitted.',
        )

    # ── Routing suggestions ───────────────────────────────────────────────────
    @action(detail=True, methods=['get'], url_path='routing-suggestions')
    def routing_suggestions(self, request, pk=None):
        doc         = self.get_object()
        suggestions = suggest_routing(doc)
        return Response({
            'document_id':      doc.id,
            'tracking_number':  doc.tracking_number,
            'ai_label':         doc.ai_label,
            'suggestions':      suggestions,
            'suggestion_count': len(suggestions),
        })

    # ── Duplicate check ───────────────────────────────────────────────────────
    @action(detail=False, methods=['post'], url_path='check-duplicate',
            permission_classes=[permissions.IsAuthenticated])
    def check_duplicate(self, request):
        class TempDoc:
            def __init__(self, data):
                self.pk               = None
                self.title            = data.get('title', '')
                self.description      = data.get('description', '')
                self.origin_office_id = data.get('origin_office_id')

        result = check_duplicates(TempDoc(request.data))
        return Response(result)

    # ── Priority suggestion ───────────────────────────────────────────────────
    @action(detail=True, methods=['get'], url_path='priority-suggestion')
    def priority_suggestion(self, request, pk=None):
        doc    = self.get_object()
        result = detect_priority(doc)
        return Response({
            'document_id':      doc.id,
            'current_priority': doc.priority,
            **result,
        })

    # ── Download (respects confidentiality) ───────────────────────────────────
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        doc = self.get_object()
        if not request.user.is_records_admin:
            if doc.confidentiality != Document.Confidentiality.PUBLIC:
                return Response(
                    {'error': 'This document is not available for download.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        try:
            response = FileResponse(doc.file.open('rb'),
                                    content_type='application/octet-stream')
            response['Content-Disposition'] = (
                f'attachment; filename="{doc.file.name.split("/")[-1]}"'
            )
            return response
        except Exception:
            return Response({'error': 'File not found.'}, status=404)

    # ── Forward ───────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='forward')
    def forward(self, request, pk=None):
        doc       = self.get_object()
        to_office = request.data.get('to_office_id')
        note      = request.data.get('note', '')
        if not to_office:
            return Response({'error': 'to_office_id required.'}, status=400)
        from accounts.models import Office
        try:
            office = Office.objects.get(pk=to_office)
        except Office.DoesNotExist:
            return Response({'error': 'Office not found.'}, status=404)

        from_office        = doc.current_office
        doc.current_office = office
        doc.status         = Document.Status.IN_REVIEW
        doc.save(update_fields=['current_office', 'status'])

        # Signal on TrackingLog handles push notifications via Celery
        TrackingLog.objects.create(
            document=doc, action=TrackingLog.Action.FORWARDED,
            actor=request.user, from_office=from_office, to_office=office, note=note,
        )
        return Response(DocumentDetailSerializer(doc, context={'request': request}).data)

    # ── Update status ─────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        doc        = self.get_object()
        new_status = request.data.get('status')
        note       = request.data.get('note', '')
        valid      = [c[0] for c in Document.Status.choices]
        if new_status not in valid:
            return Response({'error': f'status must be one of {valid}'}, status=400)

        doc.status = new_status
        if new_status == Document.Status.COMPLETED:
            doc.completed_at = timezone.now()
        doc.save(update_fields=['status', 'completed_at'])

        # Map to a valid TrackingLog action (avoids storing unmapped status strings)
        log_action = _STATUS_TO_ACTION.get(new_status, TrackingLog.Action.IN_REVIEW)

        # Signal on TrackingLog handles push notifications via Celery
        TrackingLog.objects.create(
            document=doc, action=log_action, actor=request.user, note=note,
        )
        return Response(DocumentDetailSerializer(doc, context={'request': request}).data)

    # ── Comment ───────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='comment')
    def comment(self, request, pk=None):
        doc = self.get_object()
        ser = DocumentCommentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(document=doc, author=request.user)

        # Signal on TrackingLog handles push notifications via Celery
        TrackingLog.objects.create(
            document=doc, action=TrackingLog.Action.COMMENTED,
            actor=request.user, note=ser.validated_data.get('body', '')[:200],
        )
        return Response(ser.data, status=status.HTTP_201_CREATED)

    # ── Set confidentiality ───────────────────────────────────────────────────
    @action(detail=True, methods=['patch'], url_path='set-confidentiality')
    def set_confidentiality(self, request, pk=None):
        doc   = self.get_object()
        level = request.data.get('confidentiality')
        note  = request.data.get('note', '')
        valid = [c[0] for c in Document.Confidentiality.choices]
        if level not in valid:
            return Response({'error': f'confidentiality must be one of {valid}'}, status=400)

        old_level                = doc.confidentiality
        doc.confidentiality      = level
        doc.confidentiality_note = note
        doc.save(update_fields=['confidentiality', 'confidentiality_note'])

        TrackingLog.objects.create(
            document = doc,
            action   = TrackingLog.Action.IN_REVIEW,
            actor    = request.user,
            note     = (
                f"[Confidentiality] Changed from '{old_level}' to '{level}'"
                + (f". Reason: {note}" if note else ".")
            ),
        )
        return Response(DocumentDetailSerializer(doc, context={'request': request}).data)
