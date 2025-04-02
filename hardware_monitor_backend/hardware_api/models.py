from django.db import models
from django.utils import timezone

class SystemMetric(models.Model):
    """
    Model for storing system metrics collected at regular intervals.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    cpu_percent = models.FloatField(default=0)
    memory_percent = models.FloatField(default=0)
    disk_usage_percent = models.FloatField(default=0)
    network_bytes_sent = models.BigIntegerField(default=0)
    network_bytes_recv = models.BigIntegerField(default=0)
    cpu_temp = models.FloatField(default=0, null=True, blank=True)
    fan_speed = models.IntegerField(default=0, null=True, blank=True)
    fan_expected_speed = models.IntegerField(default=0, null=True, blank=True)
    fan_anomaly = models.BooleanField(default=False)
    battery_percent = models.FloatField(default=0, null=True, blank=True)
    is_anomaly = models.BooleanField(default=False)
    anomaly_score = models.FloatField(default=0)
    
    # Add these missing fields
    swap_percent = models.FloatField(default=0, null=True, blank=True)
    disk_read_count = models.BigIntegerField(default=0, null=True, blank=True)
    disk_write_count = models.BigIntegerField(default=0, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'System Metric'
        verbose_name_plural = 'System Metrics'
    
    def __str__(self):
        return f"Metrics at {self.timestamp}"


class HardwareIssue(models.Model):
    """Model to store detected hardware issues and recommendations."""
    metric = models.ForeignKey(SystemMetric, on_delete=models.CASCADE, related_name='issues')
    timestamp = models.DateTimeField(default=timezone.now)
    issue_type = models.CharField(max_length=100)
    description = models.TextField()
    recommendation = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    fan_expected_speed = models.IntegerField(null=True, blank=True)
    fan_anomaly = models.BooleanField(default=False)
    fan_rpm_min = models.IntegerField(null=True, blank=True)
    fan_rpm_max = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.issue_type} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def resolve(self):
        """Mark the issue as resolved."""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()


class ModelTrainingHistory(models.Model):
    """Model to track ML model training history."""
    trained_at = models.DateTimeField(default=timezone.now)
    model_file_path = models.CharField(max_length=255)
    scaler_file_path = models.CharField(max_length=255)
    training_samples = models.IntegerField()
    performance_score = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-trained_at']
        verbose_name_plural = "Model training histories"
    
    def __str__(self):
        return f"Model trained at {self.trained_at.strftime('%Y-%m-%d %H:%M:%S')}"