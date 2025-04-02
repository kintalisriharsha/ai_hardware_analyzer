"""
Signal handlers for the hardware API.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SystemMetric, HardwareIssue
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=SystemMetric)
def log_anomaly_detection(sender, instance, created, **kwargs):
    """Log when an anomaly is detected."""
    if created and instance.is_anomaly:
        logger.warning(f"Anomaly detected at {instance.timestamp} with score {instance.anomaly_score}")


@receiver(post_save, sender=HardwareIssue)
def log_hardware_issue(sender, instance, created, **kwargs):
    """Log when a hardware issue is created or resolved."""
    if created:
        logger.warning(f"Hardware issue detected: {instance.issue_type}")
    elif instance.is_resolved and instance.resolved_at:
        logger.info(f"Hardware issue resolved: {instance.issue_type}")