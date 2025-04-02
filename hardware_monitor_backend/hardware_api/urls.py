from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'metrics', views.SystemMetricViewSet)
router.register(r'issues', views.HardwareIssueViewSet)
router.register(r'training', views.ModelTrainingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('health/', views.health_check, name='health_check'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('system-info/', views.system_info, name='system_info'),
    path('fans/', views.get_fan_info, name='fan-info'),
]
