"""
documents/qr_views.py
─────────────────────────────────────────────────────────────
GET /api/docs/{id}/qr/

Returns a PNG QR code image that encodes the document's tracking
number.  The mobile scanner reads this and opens DocumentDetail.

FIX #16: QR codes were generated client-side but there was no
server endpoint to produce them.  The scanner had nothing to scan.
"""
import io
import qrcode
from rest_framework.views import APIView
from rest_framework import permissions
from django.http import HttpResponse, Http404
from .models import Document


class DocumentQRView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            raise Http404

        # SECURITY: same ownership/office-aware check used by DocumentViewSet
        # and the tracking WebSocket — see Document.objects.visible_to().
        # 404 (not 403) so scanning an out-of-scope QR code doesn't even
        # confirm the document exists.
        if not Document.objects.visible_to(request.user).filter(pk=doc.pk).exists():
            raise Http404

        # Encode tracking number + deep-link hint so the app can route correctly
        qr_data = f"asc-doctrack://documents/{doc.tracking_number}"

        qr = qrcode.QRCode(
            version       = 1,
            error_correction = qrcode.constants.ERROR_CORRECT_M,
            box_size      = 10,
            border        = 4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img    = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="image/png")
        response["Content-Disposition"] = (
            f'inline; filename="qr_{doc.tracking_number}.png"'
        )
        response["Cache-Control"] = "max-age=86400, public"
        return response
