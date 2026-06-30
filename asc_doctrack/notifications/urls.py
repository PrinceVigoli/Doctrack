from django.urls import path
from . import views

urlpatterns = [
    path('register/',   views.RegisterTokenView.as_view(),   name='notif-register'),
    path('deregister/', views.DeregisterTokenView.as_view(), name='notif-deregister'),
    path('mine/',       views.MyNotificationsView.as_view(), name='notif-mine'),
    path('mark-read/',  views.MarkAllReadView.as_view(),     name='notif-mark-read'),
]
