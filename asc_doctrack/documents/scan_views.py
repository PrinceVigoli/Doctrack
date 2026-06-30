"""
documents/scan_views.py
─────────────────────────────────────────────────────────────
Scan endpoint — accepts a base64 image, runs a HuggingFace vision-language
model for OCR, returns extracted text + document classification + metadata.

POST /api/docs/scan/
{
  "image":      "<base64 string>",
  "media_type": "image/jpeg"   (optional, default jpeg)
}

Response:
{
  "extracted_text":    str,
  "suggested_title":   str,
  "doc_type":          str,
  "comm_type":         str,
  "priority":          str,
  "confidence":        float,
  "metadata":          { date, from, to, subject, reference_number, signatories },
  "summary":           str,
  "local_ai_label":    str,
  "is_readable":       bool,
  "low_quality_note":  str
}
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.throttling import UserRateThrottle
from classifier.scanner import scan_document


class ScanRateThrottle(UserRateThrottle):
    """Dedicated throttle for the scan endpoint — limits AI API cost per user."""
    scope = 'scan'


class ScanDocumentView(APIView):
    """
    All authenticated users can scan — even faculty.
    Scanning is just analysis; it doesn't create a document.
    The mobile app uses the result to pre-fill the submit form.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes   = [ScanRateThrottle]

    def post(self, request):
        image      = request.data.get('image', '').strip()
        media_type = request.data.get('media_type', 'image/jpeg')

        if not image:
            return Response(
                {'error': 'image (base64) is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reject images larger than ~10 MB encoded (base64 ≈ 4/3 × raw bytes)
        MAX_B64_LEN = 14_000_000   # ~10 MB raw
        if len(image) > MAX_B64_LEN:
            return Response(
                {'error': 'Image is too large. Maximum size is 10 MB.'},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        valid_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if media_type not in valid_types:
            return Response(
                {'error': f'media_type must be one of {valid_types}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = scan_document(image, media_type)

        if result.get('error'):
            return Response(result, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(result, status=status.HTTP_200_OK)
