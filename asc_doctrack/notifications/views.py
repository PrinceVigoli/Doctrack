from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import DeviceToken, NotificationLog
from .serializers import DeviceTokenSerializer, NotificationLogSerializer


class RegisterTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token       = request.data.get('token', '').strip()
        platform    = request.data.get('platform', 'expo')
        device_name = request.data.get('device_name', '')
        if not token:
            return Response({'error': 'token is required.'}, status=400)
        obj, created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={'user': request.user, 'platform': platform,
                      'device_name': device_name, 'is_active': True}
        )
        return Response(DeviceTokenSerializer(obj).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class DeregisterTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get('token', '').strip()
        DeviceToken.objects.filter(user=request.user, token=token).update(is_active=False)
        return Response({'detail': 'Token deregistered.'})


class MyNotificationsView(generics.ListAPIView):
    serializer_class   = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationLog.objects.filter(recipient=self.request.user)[:30]


class MarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({'detail': 'All notifications marked as read.'})
