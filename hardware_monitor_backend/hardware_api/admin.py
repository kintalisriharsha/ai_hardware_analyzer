# hardware_api/admin.py
"""
Admin configuration for the hardware monitoring app.
"""

from django.contrib import admin
from .models import SystemMetric, HardwareIssue, ModelTrainingHistory

@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'cpu_percent', 'memory_percent', 'disk_usage_percent', 'is_anomaly')
    list_filter = ('is_anomaly', 'timestamp')
    search_fields = ('timestamp',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'is_anomaly', 'anomaly_score')
    fieldsets = (
        ('General Information', {
            'fields': ('timestamp', 'is_anomaly', 'anomaly_score')
        }),
        ('CPU and Memory', {
            'fields': ('cpu_percent', 'memory_percent', 'swap_percent')
        }),
        ('Storage', {
            'fields': ('disk_usage_percent', 'disk_read_count', 'disk_write_count')
        }),
        ('Network', {
            'fields': ('network_bytes_sent', 'network_bytes_recv')
        }),
        ('Hardware Sensors', {
            'fields': ('cpu_temp', 'battery_percent', 'fan_speed'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HardwareIssue)
class HardwareIssueAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'issue_type', 'is_resolved', 'resolved_at')
    list_filter = ('is_resolved', 'issue_type', 'timestamp')
    search_fields = ('issue_type', 'description', 'recommendation')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'metric')
    actions = ['mark_as_resolved']
    
    fieldsets = (
        ('Issue Information', {
            'fields': ('timestamp', 'issue_type', 'metric')
        }),
        ('Details', {
            'fields': ('description', 'recommendation')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_at')
        }),
    )
    
    def mark_as_resolved(self, request, queryset):
        """Admin action to mark selected issues as resolved."""
        from django.utils import timezone
        updated = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f"{updated} issues marked as resolved.")
    mark_as_resolved.short_description = "Mark selected issues as resolved"
    
    def get_queryset(self, request):
        """Optimize queryset for admin."""
        return super().get_queryset(request).select_related('metric')


@admin.register(ModelTrainingHistory)
class ModelTrainingHistoryAdmin(admin.ModelAdmin):
    list_display = ('trained_at', 'training_samples', 'performance_score')
    list_filter = ('trained_at',)
    search_fields = ('notes',)
    ordering = ('-trained_at',)
    date_hierarchy = 'trained_at'
    readonly_fields = ('trained_at', 'model_file_path', 'scaler_file_path', 'training_samples')
    
    fieldsets = (
        ('Training Information', {
            'fields': ('trained_at', 'training_samples', 'performance_score')
        }),
        ('Model Files', {
            'fields': ('model_file_path', 'scaler_file_path'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )