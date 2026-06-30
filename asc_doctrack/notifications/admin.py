from django.contrib import admin
from .models import DeviceToken, NotificationLog

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'device_name', 'is_active', 'updated_at']
    list_filter  = ['platform', 'is_active']

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'title', 'status', 'tracking_number', 'sent_at']
    list_filter  = ['status']
    readonly_fields = ['sent_at']
