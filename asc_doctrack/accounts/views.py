from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Office
from .serializers import UserSerializer, RegisterSerializer, OfficeSerializer
from documents.permissions import IsRecordsAdmin


# FIX #12: custom throttle scope for login endpoint (10/min)
class LoginThrottle(AnonRateThrottle):
    scope = 'login'


class RegisterView(generics.CreateAPIView):
    serializer_class   = RegisterSerializer
    permission_classes = [IsRecordsAdmin]  # only Records Office can create users


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        try:
            token = RefreshToken(request.data['refresh'])
            token.blacklist()
        except Exception:
            pass
        return Response({'detail': 'Logged out.'})


class OfficeListView(generics.ListCreateAPIView):
    queryset         = Office.objects.all()
    serializer_class = OfficeSerializer
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsRecordsAdmin()]
        return [permissions.IsAuthenticated()]


class OfficeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset         = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [IsRecordsAdmin]


class UserListView(generics.ListAPIView):
    serializer_class   = UserSerializer
    permission_classes = [IsRecordsAdmin]
    def get_queryset(self):
        qs     = User.objects.select_related('office').all()
        office = self.request.query_params.get('office')
        if office:
            qs = qs.filter(office__id=office)
        return qs
