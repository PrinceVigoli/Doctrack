from django.urls import path
from . import views

urlpatterns = [
    path('summary/',  views.DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('activity/', views.RecentActivityView.as_view(),   name='dashboard-activity'),
]
