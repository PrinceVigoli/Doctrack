from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from documents.models import Document
from tracking.models import TrackingLog
from accounts.models import Office


class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        qs   = Document.objects.all()
        if not user.is_records_admin and user.office:
            qs = qs.filter(current_office=user.office)

        # Counts by status
        by_status = {
            item['status']: item['count']
            for item in qs.values('status').annotate(count=Count('id'))
        }

        # Counts by document type
        by_type = list(
            qs.exclude(doc_type=None)
              .values(label=F('doc_type__name'))
              .annotate(count=Count('id'))
              .order_by('-count')[:10]
        )

        # Counts by AI label
        by_ai_label = list(
            qs.exclude(ai_label='')
              .values('ai_label')
              .annotate(count=Count('id'))
              .order_by('-count')[:10]
        )

        # Average processing time (submitted → completed)
        avg_time = qs.filter(
            status=Document.Status.COMPLETED,
            completed_at__isnull=False
        ).annotate(
            duration=ExpressionWrapper(
                F('completed_at') - F('created_at'),
                output_field=DurationField()
            )
        ).aggregate(avg=Avg('duration'))['avg']

        # Trend: docs submitted per day over the last 14 days
        # TruncDate works correctly with both SQLite and PostgreSQL
        since = timezone.now() - timedelta(days=14)
        trend = list(
            qs.filter(created_at__gte=since)
              .annotate(day=TruncDate('created_at'))
              .values('day')
              .annotate(count=Count('id'))
              .order_by('day')
        )

        # Office workload
        office_load = list(
            qs.exclude(current_office=None)
              .values(office=F('current_office__name'))
              .annotate(count=Count('id'))
              .order_by('-count')
        )

        return Response({
            'total':              qs.count(),
            'by_status':          by_status,
            'by_type':            by_type,
            'by_ai_label':        by_ai_label,
            'avg_processing_hrs': round(avg_time.total_seconds() / 3600, 1) if avg_time else None,
            'daily_trend':        trend,
            'office_workload':    office_load,
        })


class RecentActivityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            page      = max(1, int(request.query_params.get('page', 1)))
            page_size = min(100, max(1, int(request.query_params.get('page_size', 30))))
        except (ValueError, TypeError):
            page, page_size = 1, 30

        user = request.user

        # Scope activity to the user's office unless they are a records admin
        logs_qs = TrackingLog.objects.select_related(
            'document', 'actor', 'from_office', 'to_office'
        )
        if not user.is_records_admin and user.office:
            logs_qs = logs_qs.filter(
                document__current_office=user.office
            ).exclude(
                document__confidentiality=Document.Confidentiality.RESTRICTED
            )
        elif not user.is_records_admin:
            # User has no office and is not a records admin — show their own submissions only
            logs_qs = logs_qs.filter(document__submitted_by=user)

        logs_qs = logs_qs.order_by('-timestamp')

        offset = (page - 1) * page_size
        total  = logs_qs.count()
        logs   = logs_qs[offset: offset + page_size]

        data = [
            {
                'id':              log.id,
                'tracking_number': log.document.tracking_number,
                'doc_title':       log.document.title,
                'action':          log.action,
                'actor':           log.actor.get_full_name() if log.actor else '—',
                'from_office':     log.from_office.name if log.from_office else '—',
                'to_office':       log.to_office.name   if log.to_office   else '—',
                'note':            log.note,
                'timestamp':       log.timestamp,
            }
            for log in logs
        ]
        return Response({
            'count':   total,
            'page':    page,
            'pages':   (total + page_size - 1) // page_size,
            'results': data,
        })
