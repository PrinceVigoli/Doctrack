"""
DocumentTrackingConsumer
─────────────────────────
WebSocket endpoint: ws://host/ws/docs/{tracking_number}/?token=JWT

When connected, the client is subscribed to a channel group named
  doc_{tracking_number}

Every time a TrackingLog is created (forwarded, approved, etc.) the
signal in tracking/signals.py broadcasts a message to this group,
which is pushed instantly to all connected clients.

Mobile usage (React Native):
  const ws = new WebSocket(
    `ws://192.168.1.7:8000/ws/docs/${trackingNumber}/?token=${accessToken}`
  );
  ws.onmessage = (e) => {
    const event = JSON.parse(e.data);
    // event.type, event.action, event.office, event.actor, event.timestamp
  };
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class DocumentTrackingConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.tracking_number = self.scope['url_route']['kwargs']['tracking_number']
        self.group_name      = f"doc_{self.tracking_number}"

        # Check the user has access to this document
        has_access = await self.check_access(user, self.tracking_number)
        if not has_access:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send current tracking history on connect
        history = await self.get_tracking_history(self.tracking_number)
        await self.send(text_data=json.dumps({
            'type':    'history',
            'payload': history,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Clients are read-only via WebSocket; all writes go through REST API
        pass

    # ── Event handlers (called by channel layer) ──────────────────────────────

    async def tracking_update(self, event):
        """Broadcast a new tracking log entry to all subscribers."""
        await self.send(text_data=json.dumps({
            'type':    'tracking_update',
            'payload': event['payload'],
        }))

    async def document_status(self, event):
        """Broadcast a status change."""
        await self.send(text_data=json.dumps({
            'type':    'status_change',
            'payload': event['payload'],
        }))

    # ── DB helpers ────────────────────────────────────────────────────────────

    @database_sync_to_async
    def check_access(self, user, tracking_number):
        from documents.models import Document
        try:
            doc = Document.objects.get(tracking_number=tracking_number)
            if user.is_records_admin or user.is_superadmin:
                return True
            if doc.confidentiality == Document.Confidentiality.RESTRICTED:
                return False
            return True
        except Document.DoesNotExist:
            return False

    @database_sync_to_async
    def get_tracking_history(self, tracking_number):
        from tracking.models import TrackingLog
        logs = TrackingLog.objects.filter(
            document__tracking_number=tracking_number
        ).select_related('actor', 'from_office', 'to_office')

        return [
            {
                'id':          log.id,
                'action':      log.action,
                'actor':       log.actor.get_full_name() if log.actor else 'System',
                'from_office': log.from_office.name if log.from_office else None,
                'to_office':   log.to_office.name   if log.to_office   else None,
                'note':        log.note,
                'timestamp':   log.timestamp.isoformat(),
            }
            for log in logs
        ]
