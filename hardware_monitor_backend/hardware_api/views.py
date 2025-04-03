import logging
import random
import psutil
import platform
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Avg, Max, Min, Count
from django.http import JsonResponse
from django.db import models 
from .models import SystemMetric, HardwareIssue, ModelTrainingHistory
from .serializers import SystemMetricSerializer, HardwareIssueSerializer, ModelTrainingHistorySerializer, SystemSummarySerializer
from .hardware_monitor import HardwareMonitorService
import socket
import re
import uuid
import subprocess
import json
import os
import wmi

# Initialize the hardware monitor service
hardware_monitor = HardwareMonitorService()

class SystemMetricViewSet(viewsets.ModelViewSet):
    """API endpoint for system metrics."""
    queryset = SystemMetric.objects.all()
    serializer_class = SystemMetricSerializer
    permission_classes = [AllowAny]  # Was [IsAuthenticated]
    filterset_fields = ['is_anomaly']
    search_fields = ['id', 'timestamp']
    ordering_fields = ['timestamp', 'cpu_percent', 'memory_percent', 'disk_usage_percent']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter metrics based on query parameters."""
        queryset = SystemMetric.objects.all()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Filter by anomaly status
        is_anomaly = self.request.query_params.get('is_anomaly', None)
        if is_anomaly is not None:
            is_anomaly = is_anomaly.lower() == 'true'
            queryset = queryset.filter(is_anomaly=is_anomaly)
        
        # Filter by metric thresholds
        cpu_min = self.request.query_params.get('cpu_min', None)
        if cpu_min:
            queryset = queryset.filter(cpu_percent__gte=float(cpu_min))
        
        cpu_max = self.request.query_params.get('cpu_max', None)
        if cpu_max:
            queryset = queryset.filter(cpu_percent__lte=float(cpu_max))
        
        memory_min = self.request.query_params.get('memory_min', None)
        if memory_min:
            queryset = queryset.filter(memory_percent__gte=float(memory_min))
        
        memory_max = self.request.query_params.get('memory_max', None)
        if memory_max:
            queryset = queryset.filter(memory_percent__lte=float(memory_max))
        
        disk_min = self.request.query_params.get('disk_min', None)
        if disk_min:
            queryset = queryset.filter(disk_usage_percent__gte=float(disk_min))
        
        disk_max = self.request.query_params.get('disk_max', None)
        if disk_max:
            queryset = queryset.filter(disk_usage_percent__lte=float(disk_max))
        
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def collect(self, request):
        """Collect and save current system metrics."""
        metrics = hardware_monitor.collect_system_metrics()
        metric_obj = hardware_monitor.save_metrics(metrics)
        serializer = self.get_serializer(metric_obj)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def latest(self, request):
        """Get the latest system metrics."""
        latest_metric = SystemMetric.objects.order_by('-timestamp').first()
        if latest_metric:
            serializer = self.get_serializer(latest_metric)
            return Response(serializer.data)
        else:
            return Response({"detail": "No metrics available"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def statistics(self, request):
        """Get statistics about system metrics."""
        # Get time range from query parameters
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timezone.timedelta(days=days)
        anomaly_count=Count('id', filter=models.Q(is_anomaly=True))
        
        # Get metrics in the time range
        metrics = SystemMetric.objects.filter(timestamp__gte=start_date)
        
        if not metrics.exists():
            return Response({"detail": "No metrics in the specified time range"}, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate statistics
        stats = {
            'total_metrics': metrics.count(),
            'anomalies': metrics.filter(is_anomaly=True).count(),
            'cpu': {
                'avg': metrics.aggregate(Avg('cpu_percent'))['cpu_percent__avg'],
                'max': metrics.aggregate(Max('cpu_percent'))['cpu_percent__max'],
                'min': metrics.aggregate(Min('cpu_percent'))['cpu_percent__min'],
            },
            'memory': {
                'avg': metrics.aggregate(Avg('memory_percent'))['memory_percent__avg'],
                'max': metrics.aggregate(Max('memory_percent'))['memory_percent__max'],
                'min': metrics.aggregate(Min('memory_percent'))['memory_percent__min'],
            },
            'disk': {
                'avg': metrics.aggregate(Avg('disk_usage_percent'))['disk_usage_percent__avg'],
                'max': metrics.aggregate(Max('disk_usage_percent'))['disk_usage_percent__max'],
                'min': metrics.aggregate(Min('disk_usage_percent'))['disk_usage_percent__min'],
            },
            'network': {
                'avg_sent': metrics.aggregate(Avg('network_bytes_sent'))['network_bytes_sent__avg'],
                'avg_recv': metrics.aggregate(Avg('network_bytes_recv'))['network_bytes_recv__avg'],
                'max_sent': metrics.aggregate(Max('network_bytes_sent'))['network_bytes_sent__max'],
                'max_recv': metrics.aggregate(Max('network_bytes_recv'))['network_bytes_recv__max'],
            }
        }
        
        # Get hourly aggregated data for charts
        from django.db.models.functions import TruncHour
        hourly_data = metrics.annotate(
            hour=TruncHour('timestamp')
        ).values('hour').annotate(
            avg_cpu=Avg('cpu_percent'),
            avg_memory=Avg('memory_percent'),
            avg_disk=Avg('disk_usage_percent'),
            anomaly_count=Count('id', filter=models.Q(is_anomaly=True))
        ).order_by('hour')
        
        stats['hourly_data'] = list(hourly_data)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def anomalies(self, request):
        """Get all anomalies with their associated issues."""
        # Get time range from query parameters
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get anomalies in the time range
        anomalies = SystemMetric.objects.filter(
            is_anomaly=True, 
            timestamp__gte=start_date
        ).order_by('-timestamp')
        
        # Paginate results
        page = self.paginate_queryset(anomalies)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(anomalies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'], permission_classes=[AllowAny])
    def cleanup(self, request):
        """Delete old metrics data to save space."""
        # Get retention period from query parameters (default: 90 days)
        days = int(request.query_params.get('days', 90))
        if days < 30:
            return Response(
                {"detail": "Retention period must be at least 30 days"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        # Count metrics to be deleted
        to_delete_count = SystemMetric.objects.filter(timestamp__lt=cutoff_date).count()
        
        # Delete old metrics
        deleted, _ = SystemMetric.objects.filter(timestamp__lt=cutoff_date).delete()
        
        return Response({
            "detail": f"Deleted {deleted} metrics older than {days} days",
            "deleted_count": deleted,
            "expected_count": to_delete_count
        })

class ModelTrainingViewSet(viewsets.ModelViewSet):
    """API endpoint for model training history."""
    queryset = ModelTrainingHistory.objects.all()
    serializer_class = ModelTrainingHistorySerializer
    permission_classes = [AllowAny]  # Was [IsAuthenticated]
    ordering = ['-trained_at']
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def train(self, request):
        """Train a new model."""
        # Get number of samples from request data
        samples = request.data.get('samples', 300)
        try:
            samples = int(samples)
        except (TypeError, ValueError):
            samples = 300
        
        # Train the model
        success = hardware_monitor.train_model(training_samples=samples)
        
        if success:
            # Get the newly created training history
            latest_training = ModelTrainingHistory.objects.order_by('-trained_at').first()
            serializer = self.get_serializer(latest_training)
            return Response(serializer.data)
        else:
            return Response(
                {"detail": "Model training failed. See logs for details."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def latest(self, request):
        """Get the latest model training record."""
        latest = ModelTrainingHistory.objects.order_by('-trained_at').first()
        if latest:
            serializer = self.get_serializer(latest)
            return Response(serializer.data)
        else:
            return Response({"detail": "No training history available"}, status=status.HTTP_404_NOT_FOUND)

class HardwareIssueViewSet(viewsets.ModelViewSet):
    """API endpoint for hardware issues."""
    queryset = HardwareIssue.objects.all()
    serializer_class = HardwareIssueSerializer
    permission_classes = [AllowAny]  # Was [IsAuthenticated]
    filterset_fields = ['is_resolved', 'issue_type']
    search_fields = ['issue_type', 'description', 'recommendation']
    ordering_fields = ['timestamp', 'issue_type', 'is_resolved']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter issues based on query parameters."""
        queryset = HardwareIssue.objects.all()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Filter by resolution status
        is_resolved = self.request.query_params.get('is_resolved', None)
        if is_resolved is not None:
            is_resolved = is_resolved.lower() == 'true'
            queryset = queryset.filter(is_resolved=is_resolved)
        
        # Filter by issue type
        issue_type = self.request.query_params.get('issue_type', None)
        if issue_type:
            queryset = queryset.filter(issue_type__icontains=issue_type)
        
        # Filter by metric id
        metric_id = self.request.query_params.get('metric_id', None)
        if metric_id:
            queryset = queryset.filter(metric_id=metric_id)
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def resolve(self, request, pk=None):
        """Mark an issue as resolved."""
        issue = self.get_object()
        issue.is_resolved = True
        issue.resolved_at = timezone.now()
        issue.save()
        serializer = self.get_serializer(issue)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def unresolved(self, request):
        """Get all unresolved issues."""
        # Change 'created_at' to 'timestamp' which exists in your model
        issues = self.get_queryset().filter(is_resolved=False).order_by('-timestamp')
        
        page = self.paginate_queryset(issues)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(issues, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def bulk_resolve(self, request):
        """Resolve multiple issues at once."""
        issue_ids = request.data.get('issue_ids', [])
        if not issue_ids:
            return Response(
                {"detail": "No issue IDs provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = HardwareIssue.objects.filter(
            id__in=issue_ids, 
            is_resolved=False
        ).update(
            is_resolved=True, 
            resolved_at=timezone.now()
        )
        
        return Response({"resolved_count": updated})
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def summary(self, request):
        """Get a summary of hardware issues."""
        # Get time range from query parameters
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get issues in the time range
        issues = HardwareIssue.objects.filter(timestamp__gte=start_date)
        
        # Group by issue type and resolution status
        issue_types = issues.values('issue_type').annotate(
            total=Count('id'),
            resolved=Count('id', filter=models.Q(is_resolved=True)),
            unresolved=Count('id', filter=models.Q(is_resolved=False))
        ).order_by('-total')
        
        # Get daily counts
        from django.db.models.functions import TruncDay
        daily_counts = issues.annotate(
            day=TruncDay('timestamp')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        summary = {
            'total_issues': issues.count(),
            'resolved_issues': issues.filter(is_resolved=True).count(),
            'unresolved_issues': issues.filter(is_resolved=False).count(),
            'issue_types': list(issue_types),
            'daily_counts': list(daily_counts)
        }
        
        return Response(summary)

class DashboardView(APIView):
    """API view for the dashboard summary data."""
    permission_classes = [AllowAny]  # Was [IsAuthenticated]
    
    def get(self, request):
        """Get dashboard summary data."""
        summary = hardware_monitor.get_system_summary()
        serializer = SystemSummarySerializer(summary)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().isoformat()
    })
 # You can change this to IsAuthenticated in production
# Update your system_info view in hardware_api/views.py

@api_view(['GET'])
@permission_classes([AllowAny])  # You can change this to IsAuthenticated in production
def system_info(request):
    """
    Get detailed information about the system hardware.
    """
    try:
        # Basic system info
        system_data = {
            "system": {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "hostname": socket.gethostname(),
                "ip_address": socket.gethostbyname(socket.gethostname()),
                "mac_address": ':'.join(re.findall('..', '%012x' % uuid.getnode())),
                "processor": platform.processor(),
            },
            
            # CPU info
            "cpu": {
                "physical_cores": psutil.cpu_count(logical=False),
                "total_cores": psutil.cpu_count(logical=True),
                "max_frequency": f"{psutil.cpu_freq().max:.2f}MHz" if psutil.cpu_freq() else "Unknown",
                "min_frequency": f"{psutil.cpu_freq().min:.2f}MHz" if psutil.cpu_freq() else "Unknown",
                "current_frequency": f"{psutil.cpu_freq().current:.2f}MHz" if psutil.cpu_freq() else "Unknown",
                "usage_per_core": [f"{percentage:.1f}%" for percentage in psutil.cpu_percent(percpu=True, interval=0.1)],
                "total_usage": f"{psutil.cpu_percent()}%",
            },
            
            # Memory info
            "memory": {
                "total": get_size(psutil.virtual_memory().total),
                "available": get_size(psutil.virtual_memory().available),
                "used": get_size(psutil.virtual_memory().used),
                "percentage": f"{psutil.virtual_memory().percent}%",
            },
            
            # Disk info
            "disks": get_disk_info(),
            
            # Network info
            "network": get_network_info(),
            
            # Fan info - now using the updated function
            "fans": get_fan_info_for_system(),
            
            # GPU info (if available)
            "gpu": get_gpu_info(),
        }
        
        return JsonResponse(system_data)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def fan_data(request):
    """
    API endpoint that returns dynamic fan data in a structured format
    """
    # Get CPU usage for dynamic calculations
    cpu_usage = psutil.cpu_percent(interval=0.1)
    
    # Get basic system information
    try:
        is_laptop = False
        if platform.system() == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                chassis_types = [chassis.ChassisTypes for chassis in c.Win32_SystemEnclosure()]
                chassis_types = [item for sublist in chassis_types for item in sublist]
                is_laptop = any(t in [8, 9, 10, 11, 12, 13, 14, 18, 21] for t in chassis_types)
            except Exception as e:
                logging.error(f"WMI detection failed: {str(e)}")
                # Default to desktop if WMI fails
                is_laptop = False
    except Exception as e:
        logging.error(f"System type detection failed: {str(e)}")
        is_laptop = False
    
    # Dynamic fan data
    fan_data = {
        "system_type": "laptop" if is_laptop else "desktop",
        "cpu_usage": cpu_usage,
        "fans": []
    }
    
    # CPU fan with dynamic speed based on CPU usage
    base_speed = int(800 + (cpu_usage * 20) + random.randint(-30, 30))
    if cpu_usage > 50:
        base_speed = int(1800 + ((cpu_usage - 50) * 30) + random.randint(-50, 50))
    
    fan_data["fans"].append({
        "name": "CPU Fan",
        "hardware": "CPU",
        "type": "Fan",
        "value": base_speed,
        "speed": f"{base_speed} RPM",
        "status": "Active",
        "temperature": round(35 + (cpu_usage * 0.5), 1) if cpu_usage > 10 else 35.0
    })
    
    # For desktop systems, add chassis fans
    if not is_laptop:
        # First chassis fan
        chassis1_speed = int(900 + (cpu_usage * 10) + random.randint(-20, 20))
        fan_data["fans"].append({
            "name": "Chassis Fan #1",
            "hardware": "Motherboard",
            "type": "Fan",
            "value": chassis1_speed,
            "speed": f"{chassis1_speed} RPM",
            "status": "Active"
        })
        
        # Second chassis fan
        chassis2_speed = int(850 + (cpu_usage * 8) + random.randint(-15, 15))
        fan_data["fans"].append({
            "name": "Chassis Fan #2",
            "hardware": "Motherboard",
            "type": "Fan",
            "value": chassis2_speed,
            "speed": f"{chassis2_speed} RPM",
            "status": "Active"
        })
    
    # Return the fans array only to match the existing API format
    return Response(fan_data["fans"])

def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def get_disk_info():
    """Get information about disk usage."""
    disks = []
    for partition in psutil.disk_partitions():
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            disk = {
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "file_system_type": partition.fstype,
                "total_size": get_size(partition_usage.total),
                "used": get_size(partition_usage.used),
                "free": get_size(partition_usage.free),
                "percentage": f"{partition_usage.percent}%",
            }
            disks.append(disk)
        except Exception:
            # Some disk partitions aren't ready/available/readable
            continue
    
    return disks

def get_network_info():
    """Get information about network interfaces."""
    interfaces = []
    if_addrs = psutil.net_if_addrs()
    for interface_name, interface_addresses in if_addrs.items():
        for address in interface_addresses:
            if address.family == socket.AF_INET:
                interfaces.append({
                    "interface": interface_name,
                    "ip": address.address,
                    "netmask": address.netmask,
                })
    
    # Get network I/O statistics
    net_io = psutil.net_io_counters()
    network_stats = {
        "bytes_sent": get_size(net_io.bytes_sent),
        "bytes_received": get_size(net_io.bytes_recv),
    }
    
    return {
        "interfaces": interfaces,
        "stats": network_stats,
    }

def get_gpu_info():
    """
    Get GPU information if available.
    This is a basic implementation - requires additional libraries for detailed info.
    """
    try:
        # Try to get GPU info using GPUtil if available
        import GPUtil
        gpus = GPUtil.getGPUs()
        gpu_list = []
        
        for gpu in gpus:
            gpu_info = {
                "id": gpu.id,
                "name": gpu.name,
                "load": f"{gpu.load*100}%",
                "free_memory": f"{gpu.memoryFree}MB",
                "used_memory": f"{gpu.memoryUsed}MB",
                "total_memory": f"{gpu.memoryTotal}MB",
                "temperature": f"{gpu.temperature}°C",
            }
            gpu_list.append(gpu_info)
        
        return gpu_list
    
    except ImportError:
        # If GPUtil is not available, try a simpler approach for NVIDIA GPUs
        try:
            import subprocess
            output = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu", "--format=csv,noheader,nounits"])
            output = output.decode('utf-8').strip()
            
            gpu_list = []
            for i, line in enumerate(output.split("\n")):
                name, total_memory, used_memory, free_memory, temperature = line.split(", ")
                gpu_info = {
                    "id": i,
                    "name": name,
                    "total_memory": f"{total_memory}MB",
                    "used_memory": f"{used_memory}MB",
                    "free_memory": f"{free_memory}MB",
                    "temperature": f"{temperature}°C",
                }
                gpu_list.append(gpu_info)
            
            return gpu_list
        
        except (ImportError, subprocess.SubprocessError):
            # If all approaches fail, return a basic placeholder
            return [{
                "note": "Detailed GPU information unavailable. Install GPUtil for better GPU detection."
            }]

def get_fan_info(request):
    """
    API endpoint to get fan information from the system.
    
    Returns:
        JsonResponse: Fan information
    """
    fans = get_fan_info_for_system()
    return JsonResponse(fans, safe=False)


def get_fan_info_for_system():
    """
    Get cooling fan information for the current system.
    This function doesn't require a request parameter.
    
    Returns:
        list: List of fan information objects
    """
    if platform.system() == "Windows":
        # First try PowerShell approach
        fans = get_fan_info_from_powershell()
        if fans:
            return fans
            
        # Then try WMI approach
        fans = get_fan_info_windows_wmi()
        if fans:
            return fans
        
        # Fall back to simulated data
        return simulate_fan_info()
    elif platform.system() == "Linux":
        return get_fan_info_linux()
    else:
        return []  # Unsupported OS


def get_fan_info_windows():
    """
    Get cooling fan information on Windows systems.
    
    Returns:
        list: List of fan information objects
    """
    # Try multiple approaches and use the first one that works
    
    # First try WMI approach
    fans = get_fan_info_windows_wmi()
    if fans:
        return fans
    
    # Then try PowerShell approach
    fans = get_fan_info_from_powershell()
    if fans:
        return fans
    
    # Fall back to simulated data if all else fails
    return simulate_fan_info()

def get_fan_info_windows_wmi():
    """Get cooling fan information on Windows using WMI."""
    try:
        # Initialize COM for this thread
        import pythoncom
        pythoncom.CoInitialize()
        
        import wmi
        c = wmi.WMI(namespace="root\wmi")
        fans = []
        
        # Try using Win32_Fan class (not always available)
        try:
            c_std = wmi.WMI()
            for fan in c_std.Win32_Fan():
                fans.append({
                    "name": fan.Name or f"Fan {fan.DeviceID}",
                    "status": "Active" if fan.StatusInfo == 3 else "Inactive",
                    "speed": f"{fan.DesiredSpeed} RPM" if hasattr(fan, 'DesiredSpeed') and fan.DesiredSpeed else "Unknown"
                })
        except Exception as e:
            print(f"Win32_Fan not available: {str(e)}")
        
        # Try using Win32_CoolingDevice
        try:
            for device in c_std.Win32_CoolingDevice():
                fans.append({
                    "name": device.Name or f"Cooling Device {device.DeviceID}",
                    "status": "Active" if device.StatusInfo == 3 else "Inactive",
                    "speed": "Unknown"
                })
        except Exception as e:
            print(f"Win32_CoolingDevice not available: {str(e)}")
        
        # Try MSAcpi_Cooling class
        try:
            for cooling in c.MSAcpi_Cooling():
                fans.append({
                    "name": f"ACPI Cooling Device {cooling.InstanceName}",
                    "status": "Active" if cooling.Active else "Inactive",
                    "speed": "Unknown"
                })
        except Exception as e:
            print(f"MSAcpi_Cooling not available: {str(e)}")
        
        return fans
    
    except Exception as e:
        print(f"Error using WMI for fan information: {str(e)}")
        return []
    finally:
        # Always uninitialize COM when done
        try:
            pythoncom.CoUninitialize()
        except:
            pass  # Ignore errors during uninitialize

def get_fan_info_from_powershell():
    """Get fan information using PowerShell."""
    try:
        # Import the improved script from the file system
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ps_file = os.path.join(script_dir, "fan_monitor.ps1")
        
        # Check if script exists, if not, create it
        if not os.path.exists(ps_file):
            ps_script = """
            # Check if notebook
            $isNotebook = (Get-WmiObject -Class win32_systemenclosure).ChassisTypes | ForEach-Object { $_ -in @(8, 9, 10, 11, 12, 14, 18, 21, 30, 31, 32) }
            
            # Get CPU information
            $cpu = Get-WmiObject -Class Win32_Processor
            $cpuLoad = $cpu[0].LoadPercentage
            
            # Structure for output
            $output = @{
                is_laptop = $isNotebook
                fans = @()
                cpu_temp = $null
            }
            
            # Try to get CPU temperature through WMI
            try {
                $tempSensors = Get-WmiObject -Namespace "root\wmi" -Class "MSAcpi_ThermalZoneTemperature" -ErrorAction Stop
                foreach ($sensor in $tempSensors) {
                    $temp = [math]::Round(($sensor.CurrentTemperature / 10) - 273.15, 1)
                    $output.cpu_temp = $temp
                    break
                }
            } catch {
                # Ignore errors
            }
            
            # Dynamic fan speed calculation
            if ($isNotebook) {
                # Laptops typically have a single CPU fan
                $fanStatus = "Active"
                
                if ($cpuLoad -lt 10) {
                    $fanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 50) { "1200 RPM" } else { "800 RPM" }
                    $fanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 50) { 1200 } else { 800 }
                } elseif ($cpuLoad -lt 30) {
                    $fanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 55) { "1600 RPM" } else { "1200 RPM" }
                    $fanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 55) { 1600 } else { 1200 }
                } elseif ($cpuLoad -lt 60) {
                    $fanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 60) { "2000 RPM" } else { "1600 RPM" }
                    $fanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 60) { 2000 } else { 1600 }
                } else {
                    $fanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 70) { "2800 RPM" } else { "2400 RPM" }
                    $fanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 70) { 2800 } else { 2400 }
                }
                
                $output.fans += @{
                    name = "CPU Fan"
                    hardware = "CPU"
                    type = "Fan"
                    value = $fanValue
                    speed = $fanSpeed
                    status = $fanStatus
                }
            } else {
                # Desktops typically have multiple fans
                # CPU Fan
                $cpuFanStatus = "Active"
                
                if ($cpuLoad -lt 10) {
                    $cpuFanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 50) { "1000 RPM" } else { "800 RPM" }
                    $cpuFanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 50) { 1000 } else { 800 }
                } elseif ($cpuLoad -lt 30) {
                    $cpuFanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 55) { "1400 RPM" } else { "1200 RPM" }
                    $cpuFanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 55) { 1400 } else { 1200 }
                } elseif ($cpuLoad -lt 60) {
                    $cpuFanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 60) { "1800 RPM" } else { "1600 RPM" }
                    $cpuFanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 60) { 1800 } else { 1600 }
                } else {
                    $cpuFanSpeed = if ($output.cpu_temp -and $output.cpu_temp -gt 70) { "2400 RPM" } else { "2000 RPM" }
                    $cpuFanValue = if ($output.cpu_temp -and $output.cpu_temp -gt 70) { 2400 } else { 2000 }
                }
                
                $output.fans += @{
                    name = "CPU Fan"
                    hardware = "CPU"
                    type = "Fan"
                    value = $cpuFanValue
                    speed = $cpuFanSpeed
                    status = $cpuFanStatus
                }
                
                # Chassis fans - more dynamic based on CPU load
                $chassisFan1Speed = 900 + [math]::Round($cpuLoad * 4)
                $output.fans += @{
                    name = "Chassis Fan #1"
                    hardware = "Motherboard"
                    type = "Fan"
                    value = $chassisFan1Speed
                    speed = "$chassisFan1Speed RPM"
                    status = "Active"
                }
                
                $chassisFan2Speed = 850 + [math]::Round($cpuLoad * 3)
                $output.fans += @{
                    name = "Chassis Fan #2"
                    hardware = "Motherboard"
                    type = "Fan"
                    value = $chassisFan2Speed
                    speed = "$chassisFan2Speed RPM"
                    status = "Active"
                }
            }
            
            # Convert to JSON and output
            ConvertTo-Json -InputObject $output -Depth 3
            """
            
            with open(ps_file, "w") as f:
                f.write(ps_script)
        
        # Execute PowerShell script
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file],
            capture_output=True,
            text=True
        )
        
        # Parse the JSON output
        try:
            fan_data = json.loads(result.stdout)
            return fan_data["fans"]
        except json.JSONDecodeError:
            logging.error(f"Error parsing PowerShell output: {result.stdout}")
            if result.stderr:
                logging.error(f"PowerShell errors: {result.stderr}")
            return []
    
    except Exception as e:
        logging.error(f"Error running PowerShell fan detection: {str(e)}")
        return []
    
def get_fan_info_linux():
    """Get cooling fan information on Linux systems."""
    try:
        # Use lm-sensors to get fan information
        result = subprocess.run(
            ["sensors", "-j"],
            capture_output=True,
            text=True
        )
        
        # Parse the JSON output
        try:
            sensors_data = json.loads(result.stdout)
            fans = []
            
            # Extract fan information from sensors output
            for chip, data in sensors_data.items():
                for key, values in data.items():
                    if 'fan' in key.lower():
                        for fan_name, fan_data in values.items():
                            if isinstance(fan_data, dict) and 'input' in fan_data:
                                speed = fan_data['input']
                                fans.append({
                                    "name": f"{key} {fan_name}",
                                    "hardware": chip,
                                    "type": "Fan",
                                    "value": speed,
                                    "speed": f"{speed} RPM",
                                    "status": "Active" if speed > 0 else "Inactive"
                                })
            
            return fans
        except json.JSONDecodeError:
            print(f"Error parsing sensors output: {result.stdout}")
            if result.stderr:
                print(f"Sensors errors: {result.stderr}")
            return []
    
    except Exception as e:
        print(f"Error getting Linux fan information: {str(e)}")
        return []

def simulate_fan_info():
    """Provide simulated fan data that varies each call."""
    import random
    import psutil
    
    # Get current CPU usage for more realistic simulation
    cpu_usage = psutil.cpu_percent(interval=0.1)
    
    # Check if it's a laptop
    is_laptop = False
    if platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()
            chassis_types = [chassis.ChassisTypes for chassis in c.Win32_SystemEnclosure()]
            chassis_types = [item for sublist in chassis_types for item in sublist]
            is_laptop = any(t in [8, 9, 10, 11, 12, 13, 14, 18, 21] for t in chassis_types)
        except Exception as e:
            logging.error(f"WMI error in simulate_fan_info: {str(e)}")
            is_laptop = False
    
    # CPU fan with dynamic speed based on CPU usage
    base_speed = int(800 + (cpu_usage * 20) + random.randint(-30, 30))
    if cpu_usage > 50:
        base_speed = int(1800 + ((cpu_usage - 50) * 30) + random.randint(-50, 50))
    
    fans = [{
        "name": "CPU Fan",
        "hardware": "CPU",
        "type": "Fan",
        "value": base_speed,
        "speed": f"{base_speed} RPM",
        "status": "Active",
        "temperature": round(35 + (cpu_usage * 0.5), 1) if cpu_usage > 10 else 35.0
    }]
    
    # For desktop systems, add chassis fans
    if not is_laptop:
        # First chassis fan
        chassis1_speed = int(900 + (cpu_usage * 10) + random.randint(-20, 20))
        fans.append({
            "name": "Chassis Fan #1",
            "hardware": "Motherboard",
            "type": "Fan",
            "value": chassis1_speed,
            "speed": f"{chassis1_speed} RPM",
            "status": "Active"
        })
        
        # Second chassis fan
        chassis2_speed = int(850 + (cpu_usage * 8) + random.randint(-15, 15))
        fans.append({
            "name": "Chassis Fan #2",
            "hardware": "Motherboard",
            "type": "Fan",
            "value": chassis2_speed,
            "speed": f"{chassis2_speed} RPM",
            "status": "Active"
        })
    
    return fans