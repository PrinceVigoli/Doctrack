from django.db import models
from accounts.models import User


class DeviceToken(models.Model):
    class Platform(models.TextChoices):
        EXPO    = 'expo',    'Expo (React Native)'
        ANDROID = 'android', 'Android (FCM)'
        IOS     = 'ios',     'iOS (APNs via FCM)'

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    token       = models.TextField(unique=True)
    platform    = models.CharField(max_length=10, choices=Platform.choices, default=Platform.EXPO)
    device_name = models.CharField(max_length=100, blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} | {self.platform} | {self.token[:20]}…"


class NotificationLog(models.Model):
    class Status(models.TextChoices):
        SENT    = 'sent',    'Sent'
        FAILED  = 'failed',  'Failed'
        PENDING = 'pending', 'Pending'

    recipient       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='notifications')
    title           = models.CharField(max_length=200)
    body            = models.TextField()
    data            = models.JSONField(default=dict, blank=True)
    status          = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_msg       = models.TextField(blank=True)
    sent_at         = models.DateTimeField(auto_now_add=True)
    document_id     = models.IntegerField(null=True, blank=True)
    tracking_number = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"[{self.status}] {self.title} → {self.recipient}"
