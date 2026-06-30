"""
tracking/signals.py
───────────────────
When a TrackingLog is saved, this signal:
  1. Broadcasts the update over WebSocket to all clients watching the document
  2. Queues a push notification task for the relevant users
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from tracking.models import TrackingLog


@receiver(post_save, sender=TrackingLog)
def broadcast_tracking_update(sender, instance, created, **kwargs):
    if not created:
        return

    log     = instance
    channel_layer = get_channel_layer()
    group_name    = f"doc_{log.document.tracking_number}"

    payload = {
        'id':          log.id,
        'action':      log.action,
        'actor':       log.actor.get_full_name() if log.actor else 'System',
        'actor_role':  log.actor.get_role_display() if log.actor else '',
        'from_office': log.from_office.name if log.from_office else None,
        'to_office':   log.to_office.name   if log.to_office   else None,
        'note':        log.note,
        'timestamp':   log.timestamp.isoformat(),
        'doc_status':  log.document.status,
        'tracking_number': log.document.tracking_number,
    }

    # 1. Real-time WebSocket broadcast
    async_to_sync(channel_layer.group_send)(
        group_name,
        {'type': 'tracking_update', 'payload': payload}
    )

    # 2. Push notification (background Celery task)
    # FIX #9: task renamed to push_document_event to avoid collision with service function
    from notifications.tasks import push_document_event
    push_document_event.delay(log.id)
