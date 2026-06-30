from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views


# FIX #12: wrap the built-in simplejwt view with our LoginThrottle
class ThrottledTokenView(TokenObtainPairView):
    throttle_classes = [views.LoginThrottle]


urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/',    ThrottledTokenView.as_view(), name='token_obtain_pair'),
    path('refresh/',  TokenRefreshView.as_view(),    name='token_refresh'),
    path('logout/',   views.LogoutView.as_view(),    name='logout'),
    path('me/',       views.MeView.as_view(),        name='me'),
    path('offices/',       views.OfficeListView.as_view(),   name='offices'),
    path('offices/<int:pk>/', views.OfficeDetailView.as_view(), name='office-detail'),
    path('users/',         views.UserListView.as_view(),    name='users'),
]
