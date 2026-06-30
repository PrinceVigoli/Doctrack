from rest_framework import serializers
from .models import DeviceToken, NotificationLog


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DeviceToken
        fields = ['id', 'token', 'platform', 'device_name', 'is_active', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = NotificationLog
        fields = ['id', 'title', 'body', 'status', 'sent_at',
                  'tracking_number', 'document_id', 'error_msg']
        read_only_fields = fields
