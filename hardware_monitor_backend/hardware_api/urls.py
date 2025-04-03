from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import fan_data

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
    path('fans/', views.fan_data, name='fan-data'), 
    path('api/fan-data/', fan_data, name='fan_data'),
    path('api/fans/', fan_data, name='fans'),
]
