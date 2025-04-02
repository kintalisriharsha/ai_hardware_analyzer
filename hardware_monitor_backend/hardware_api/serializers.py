from rest_framework import serializers
from .models import SystemMetric, HardwareIssue, ModelTrainingHistory

class SystemMetricSerializer(serializers.ModelSerializer):
    """Serializer for system metrics."""
    class Meta:
        model = SystemMetric
        fields = [
            'id', 'timestamp', 'cpu_percent', 'memory_percent', 
            'disk_usage_percent', 'network_bytes_sent', 'network_bytes_recv',
            'cpu_temp', 'fan_speed', 'fan_expected_speed', 'fan_anomaly',
            'battery_percent', 'is_anomaly', 'anomaly_score'
        ]


class HardwareIssueSerializer(serializers.ModelSerializer):
    """Serializer for hardware issues."""
    class Meta:
        model = HardwareIssue
        fields = '__all__'
        read_only_fields = ['id', 'timestamp', 'resolved_at']


class ModelTrainingHistorySerializer(serializers.ModelSerializer):
    """Serializer for model training history."""
    class Meta:
        model = ModelTrainingHistory
        fields = '__all__'
        read_only_fields = ['id', 'trained_at']


class SystemSummarySerializer(serializers.Serializer):
    """Serializer for system summary data."""
    current_state = serializers.DictField()
    recent_anomalies = serializers.ListField()
    unresolved_issues = serializers.ListField()
    trends = serializers.DictField()
    model_status = serializers.DictField()