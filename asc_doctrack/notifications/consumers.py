"""
NotificationConsumer
─────────────────────
WebSocket endpoint: ws://host/ws/notifications/?token=JWT

Each authenticated user joins their own private group:
  user_{user_id}_notifications

When a document event happens (forward, approve, reject), the
notify_document_event Celery task sends a message to this group,
which is instantly pushed to the user's mobile app.

Mobile usage:
  const ws = new WebSocket(
    `ws://192.168.1.7:8000/ws/notifications/?token=${accessToken}`
  );
  ws.onmessage = (e) => {
    const notif = JSON.parse(e.data);
    showToast(notif.title, notif.body);
  };
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        # Private group per user
        self.group_name = f"user_{user.id}_notifications"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Read-only — clients don't send anything here
        pass

    async def send_notification(self, event):
        """Called by Celery task via channel layer."""
        await self.send(text_data=json.dumps({
            'type':             'notification',
            'title':            event['title'],
            'body':             event['body'],
            'tracking_number':  event.get('tracking_number'),
            'document_id':      event.get('document_id'),
            'action':           event.get('action'),
            'timestamp':        event.get('timestamp'),
        }))
