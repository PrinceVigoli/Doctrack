import os
from rest_framework import serializers
from .models import Document, DocumentType, DocumentComment
from accounts.serializers import UserSerializer, OfficeSerializer
from tracking.models import TrackingLog


# ── File upload constraints ───────────────────────────────────────────────────

MAX_FILE_SIZE_MB  = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Allowlisted extensions → expected MIME type prefixes
ALLOWED_EXTENSIONS = {
    # Documents
    '.pdf':  'application/pdf',
    '.doc':  'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml',
    '.xls':  'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml',
    '.ppt':  'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml',
    '.txt':  'text/',
    '.csv':  'text/',
    # Images (for scanned documents)
    '.jpg':  'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png':  'image/png',
    '.webp': 'image/webp',
    '.gif':  'image/gif',
    # Archives (supporting docs)
    '.zip':  'application/zip',
}


def validate_uploaded_file(file):
    """
    Validates an uploaded file against:
      1. Size limit (20 MB)
      2. Extension allowlist
      3. Declared Content-Type consistency with extension

    Returns the file unchanged if valid; raises ValidationError otherwise.
    """
    # 1. Size check
    if file.size > MAX_FILE_SIZE_BYTES:
        raise serializers.ValidationError(
            f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB "
            f"(your file is {file.size / 1024 / 1024:.1f} MB)."
        )

    # 2. Extension check
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ', '.join(sorted(ALLOWED_EXTENSIONS))
        raise serializers.ValidationError(
            f"File type '{ext}' is not allowed. "
            f"Accepted types: {allowed}"
        )

    # 3. Content-Type consistency (defence-in-depth — catches renamed executables)
    expected_prefix = ALLOWED_EXTENSIONS[ext]
    content_type    = getattr(file, 'content_type', '') or ''
    if content_type and not content_type.startswith(expected_prefix):
        raise serializers.ValidationError(
            f"File content does not match its extension. "
            f"Expected a {ext.lstrip('.')} file but received content-type '{content_type}'."
        )

    return file


# ── Serializers ───────────────────────────────────────────────────────────────

class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DocumentType
        fields = ['id', 'name', 'code', 'description', 'is_active']


class DocumentCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    class Meta:
        model  = DocumentComment
        fields = ['id', 'author', 'body', 'is_private', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']


class TrackingLogSerializer(serializers.ModelSerializer):
    actor       = UserSerializer(read_only=True)
    from_office = OfficeSerializer(read_only=True)
    to_office   = OfficeSerializer(read_only=True)
    class Meta:
        model  = TrackingLog
        fields = ['id', 'action', 'actor', 'from_office', 'to_office', 'note', 'timestamp']


class DocumentListSerializer(serializers.ModelSerializer):
    doc_type                = DocumentTypeSerializer(read_only=True)
    submitted_by            = UserSerializer(read_only=True)
    current_office          = OfficeSerializer(read_only=True)
    can_download            = serializers.SerializerMethodField()
    comm_type_display       = serializers.CharField(source='get_comm_type_display', read_only=True)
    confidentiality_display = serializers.CharField(source='get_confidentiality_display', read_only=True)

    class Meta:
        model  = Document
        fields = [
            'id', 'tracking_number', 'title',
            'doc_type', 'status', 'priority',
            'ai_label', 'ai_confidence',
            'comm_type', 'comm_type_display',
            'confidentiality', 'confidentiality_display',
            'can_download',
            'submitted_by', 'current_office',
            'created_at', 'due_date',
        ]

    def get_can_download(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.is_downloadable_by(request.user)


class DocumentDetailSerializer(serializers.ModelSerializer):
    doc_type                = DocumentTypeSerializer(read_only=True)
    doc_type_id             = serializers.PrimaryKeyRelatedField(
        queryset=DocumentType.objects.all(), source='doc_type', write_only=True, required=False)
    submitted_by            = UserSerializer(read_only=True)
    assigned_to             = UserSerializer(read_only=True)
    origin_office           = OfficeSerializer(read_only=True)
    current_office          = OfficeSerializer(read_only=True)
    destination_office      = OfficeSerializer(read_only=True)
    comments                = DocumentCommentSerializer(many=True, read_only=True)
    logs                    = TrackingLogSerializer(many=True, read_only=True)
    can_download            = serializers.SerializerMethodField()
    comm_type_display       = serializers.CharField(source='get_comm_type_display', read_only=True)
    confidentiality_display = serializers.CharField(source='get_confidentiality_display', read_only=True)

    class Meta:
        model  = Document
        fields = [
            'id', 'tracking_number', 'title', 'description',
            'doc_type', 'doc_type_id',
            'ai_label', 'ai_confidence',
            'comm_type', 'comm_type_display',
            'confidentiality', 'confidentiality_display', 'confidentiality_note',
            'can_download',
            'status', 'priority',
            'submitted_by', 'assigned_to',
            'origin_office', 'current_office', 'destination_office',
            'file', 'file_size',
            'created_at', 'updated_at', 'due_date', 'completed_at',
            'comments', 'logs',
        ]
        read_only_fields = [
            'id', 'tracking_number', 'submitted_by',
            'ai_label', 'ai_confidence', 'file_size',
            'created_at', 'updated_at', 'completed_at',
        ]

    def get_can_download(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.is_downloadable_by(request.user)


class DocumentCreateSerializer(serializers.ModelSerializer):
    destination_office_id = serializers.PrimaryKeyRelatedField(
        source='destination_office',
        queryset=__import__('accounts').models.Office.objects.all(),
        required=False,
    )
    doc_type_id = serializers.PrimaryKeyRelatedField(
        source='doc_type', queryset=DocumentType.objects.all(), required=False,
    )

    class Meta:
        model  = Document
        fields = [
            'title', 'description', 'priority', 'due_date',
            'file', 'doc_type_id', 'destination_office_id',
            'comm_type', 'confidentiality',
        ]

    def validate_file(self, file):
        return validate_uploaded_file(file)
