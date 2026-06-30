"""
WebSocket URL patterns.
  ws://host/ws/docs/{tracking_number}/   — real-time document tracking
  ws://host/ws/notifications/            — per-user push event stream
"""
from django.urls import re_path
from tracking.consumers import DocumentTrackingConsumer
from notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r'^ws/docs/(?P<tracking_number>[^/]+)/$', DocumentTrackingConsumer.as_asgi()),
    re_path(r'^ws/notifications/$',                   NotificationConsumer.as_asgi()),
]
