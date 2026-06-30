from django.contrib import admin
from .models import Document, DocumentType, DocumentComment

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display  = ['tracking_number', 'title', 'doc_type', 'status', 'priority',
                     'submitted_by', 'current_office', 'ai_label', 'created_at']
    list_filter   = ['status', 'priority', 'doc_type', 'current_office']
    search_fields = ['tracking_number', 'title']
    readonly_fields = ['tracking_number', 'ai_label', 'ai_confidence',
                       'file_size', 'created_at', 'updated_at']

@admin.register(DocumentComment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['document', 'author', 'is_private', 'created_at']
