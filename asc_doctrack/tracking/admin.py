from django.contrib import admin
from .models import TrackingLog

@admin.register(TrackingLog)
class TrackingLogAdmin(admin.ModelAdmin):
    list_display  = ['document', 'action', 'actor', 'from_office', 'to_office', 'timestamp']
    list_filter   = ['action']
    readonly_fields = ['timestamp']
