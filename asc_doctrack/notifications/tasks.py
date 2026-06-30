"""
notifications/tasks.py
───────────────────────
Celery background tasks:
  1. push_document_event     — push notification when doc status changes
  2. classify_document_async — AI classification in background (TF-IDF + LR)
"""
import logging
from celery import shared_task
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


# ── 1. Document event notification ───────────────────────────────────────────

ACTION_MESSAGES = {
    'submitted':  ('📄 New Document Submitted',       '{actor} submitted "{title}"'),
    'forwarded':  ('📨 Document Forwarded',            '"{title}" forwarded to {to_office}'),
    'received':   ('✅ Document Received',             '"{title}" received by {to_office}'),
    'in_review':  ('🔍 Document Under Review',         '"{title}" is now under review'),
    'approved':   ('✅ Document Approved',             '"{title}" has been approved'),
    'rejected':   ('❌ Document Rejected',             '"{title}" has been rejected'),
    'returned':   ('↩️ Document Returned',             '"{title}" was returned with notes'),
    'completed':  ('🎉 Document Completed',            '"{title}" is complete'),
    'commented':  ('💬 New Comment',                   '{actor} commented on "{title}"'),
}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def push_document_event(self, tracking_log_id: int):
    """
    Fires after a TrackingLog is created (via tracking.signals).
    Broadcasts a WebSocket event to the document room and to each recipient's
    personal notification channel, then sends push notifications.
    """
    from tracking.models import TrackingLog
    from notifications.service import notify_user

    try:
        log = TrackingLog.objects.select_related(
            'document', 'actor', 'from_office', 'to_office',
            'document__submitted_by', 'document__current_office',
        ).get(id=tracking_log_id)
    except TrackingLog.DoesNotExist:
        return

    doc    = log.document
    action = log.action
    actor  = log.actor

    title_tpl, body_tpl = ACTION_MESSAGES.get(
        action, ('Document Update', 'Your document "{title}" was updated'),
    )
    title = title_tpl
    body  = body_tpl.format(
        title     = doc.title[:60],
        actor     = actor.get_full_name() if actor else 'System',
        to_office = log.to_office.name if log.to_office else '',
    )

    recipients    = _get_recipients(log)
    channel_layer = get_channel_layer()
    ws_payload    = {
        'type':            'send_notification',
        'title':           title,
        'body':            body,
        'tracking_number': doc.tracking_number,
        'document_id':     doc.id,
        'action':          action,
        'timestamp':       timezone.now().isoformat(),
    }

    push_data = {
        'trackingNumber': doc.tracking_number,
        'documentId':     str(doc.id),
        'action':         action,
        'screen':         'DocumentDetail',
    }

    for user in recipients:
        # Real-time WebSocket broadcast to user's personal channel
        try:
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}_notifications", ws_payload,
            )
        except Exception as exc:
            logger.warning(f"WS notify failed for user {user.id}: {exc}")

        # Push notification (Expo / FCM)
        try:
            notify_user(
                user     = user,
                title    = title,
                body     = body,
                data     = push_data,
                document = doc,
            )
        except Exception as exc:
            logger.warning(f"Push notify failed for user {user.id}: {exc}")


def _get_recipients(log):
    """Determine who should receive a notification for this tracking event."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    recipients = set()
    doc = log.document

    if doc.submitted_by:
        recipients.add(doc.submitted_by)

    if log.to_office:
        recipients.update(User.objects.filter(office=log.to_office, is_active=True))

    recipients.update(
        User.objects.filter(role__in=['records_officer', 'superadmin'], is_active=True)
    )

    if log.actor:
        recipients.discard(log.actor)

    return list(recipients)


# ── 2. Background AI Classification ──────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def classify_document_async(self, document_id: int):
    """
    Classifies a document in the background using the local TF-IDF classifier.
    Called automatically after a document is saved (from documents/views.py).

    Updates document.ai_label and document.ai_confidence only.
    Does NOT create a TrackingLog entry — classification is a system operation,
    not a human workflow step, and should not appear in the audit trail.
    """
    from documents.models import Document
    from classifier.service import classify_document

    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return

    logger.info(f"Classifying document {doc.tracking_number}...")

    try:
        label, confidence = classify_document(doc)

        doc.ai_label      = label
        doc.ai_confidence = confidence
        doc.save(update_fields=['ai_label', 'ai_confidence'])

        logger.info(f"Classification complete: {doc.tracking_number} → {label} ({confidence:.0%})")

    except Exception as exc:
        logger.error(f"Classification failed for document {document_id}: {exc}")
        raise self.retry(exc=exc)
