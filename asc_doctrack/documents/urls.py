from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views
from .scan_views import ScanDocumentView
from .qr_views import DocumentQRView

router = DefaultRouter()
router.register('types', views.DocumentTypeViewSet, basename='doctype')
router.register('',      views.DocumentViewSet,     basename='document')

urlpatterns = router.urls + [
    path('scan/',             ScanDocumentView.as_view(), name='document-scan'),
    path('<int:pk>/qr/',      DocumentQRView.as_view(),   name='document-qr'),   # FIX #16
]
