import os
import psutil
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import SystemMetric, HardwareIssue, ModelTrainingHistory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='hardware_monitor_django.log'
)

class HardwareMonitorService:
    """Service for hardware monitoring and anomaly detection."""
    
    def __init__(self):
        """Initialize the hardware monitor service."""
        self.model = None
        self.scaler = None
        self.model_path = os.path.join(settings.ML_MODELS_DIR, "hardware_health_model.joblib")
        self.scaler_path = os.path.join(settings.ML_MODELS_DIR, "hardware_metrics_scaler.joblib")
        self.columns = [
            'cpu_percent', 'memory_percent', 'swap_percent', 
            'disk_usage_percent', 'disk_read_count', 'disk_write_count',
            'network_bytes_sent', 'network_bytes_recv', 'cpu_temp',
            'battery_percent', 'fan_speed'
        ]
        
        # Try to load the latest model from the database
        self._load_latest_model()
    
    def _load_latest_model(self):
        """Load the latest trained model if available."""
        try:
            latest_model = ModelTrainingHistory.objects.order_by('-trained_at').first()
            if latest_model:
                self.model = joblib.load(latest_model.model_file_path)
                self.scaler = joblib.load(latest_model.scaler_file_path)
                logging.info(f"Loaded model trained at {latest_model.trained_at}")
                return True
            
            # Fall back to default paths if no database record
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logging.info("Loaded model from default paths")
                return True
        except Exception as e:
            logging.error(f"Error loading model: {e}")
        
        return False
    
    def collect_system_metrics(self):
        """Collect system metrics using psutil."""
        metrics = {}
        try:
            # CPU metrics
            metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics['memory_percent'] = memory.percent
            
            # Swap metrics
            swap = psutil.swap_memory()
            metrics['swap_percent'] = swap.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics['disk_usage_percent'] = disk.percent
            
            disk_io = psutil.disk_io_counters()
            metrics['disk_read_count'] = disk_io.read_count if disk_io else 0
            metrics['disk_write_count'] = disk_io.write_count if disk_io else 0
            
            # Network metrics
            net_io = psutil.net_io_counters()
            metrics['network_bytes_sent'] = net_io.bytes_sent if net_io else 0
            metrics['network_bytes_recv'] = net_io.bytes_recv if net_io else 0
            
            # Temperature metrics (if available)
            metrics['cpu_temp'] = 0
            try:
                temps = psutil.sensors_temperatures()
                if temps and 'coretemp' in temps:
                    metrics['cpu_temp'] = temps['coretemp'][0].current
                elif temps and len(temps) > 0:
                    # Try to get temperature from any available sensor
                    first_sensor = list(temps.keys())[0]
                    if temps[first_sensor] and len(temps[first_sensor]) > 0:
                        metrics['cpu_temp'] = temps[first_sensor][0].current
            except Exception:
                # Handle all exceptions, including file not found errors
                pass
            
            # Battery metrics (if available)
            metrics['battery_percent'] = 0
            try:
                battery = psutil.sensors_battery()
                if battery:
                    metrics['battery_percent'] = battery.percent
            except Exception:
                # Handle all exceptions, including file not found errors
                pass
            
            # Fan speed (if available)
            metrics['fan_speed'] = 0
            try:
                fans = psutil.sensors_fans()
                if fans and len(fans) > 0:
                    first_fan_key = list(fans.keys())[0]
                    metrics['fan_speed'] = fans[first_fan_key][0].current
            except Exception:
                # Handle all exceptions, including file not found errors
                pass
            
        except Exception as e:
            logging.error(f"Error collecting system metrics: {e}")
        
        return metrics
    
    def collect_metrics(self):
        """
        Collect current system metrics and save to database.
        
        Returns:
            SystemMetric: The saved metrics object
        """
        try:
            # Existing code to collect metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Get swap usage
            swap = psutil.swap_memory()
            swap_percent = swap.percent
            
            # Get disk I/O counts
            disk_io = psutil.disk_io_counters()
            disk_read_count = disk_io.read_count if hasattr(disk_io, 'read_count') else 0
            disk_write_count = disk_io.write_count if hasattr(disk_io, 'write_count') else 0
            
            # Get CPU temperature if available
            cpu_temp = 0
            try:
                # Try to get temperature from psutil if available
                if hasattr(psutil, 'sensors_temperatures'):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        # Different systems name their CPU temperature sensor differently
                        for name, entries in temps.items():
                            if any(name.lower().startswith(prefix) for prefix in ['cpu', 'core', 'k10temp', 'coretemp']):
                                if entries:
                                    cpu_temp = entries[0].current
                                    break
            except Exception as e:
                print(f"Error getting CPU temperature: {e}")
            
            # Get fan speed if available
            fan_speed = 0
            try:
                if hasattr(psutil, 'sensors_fans'):
                    fans = psutil.sensors_fans()
                    if fans:
                        for name, entries in fans.items():
                            if entries:
                                fan_speed = entries[0].current
                                break
            except Exception as e:
                print(f"Error getting fan speed: {e}")
            
            # Calculate expected fan speed based on CPU temperature
            # This is a simplified model - real fan curves are more complex
            fan_expected_speed = 0
            fan_anomaly = False
            
            if cpu_temp > 0:
                # Simple fan curve calculation
                if cpu_temp < 40:
                    fan_expected_speed = 1000  # Low speed
                elif cpu_temp < 60:
                    # Linear increase between 40 and 60 degrees
                    fan_expected_speed = 1000 + ((cpu_temp - 40) * 50)  # 1000-2000 RPM
                elif cpu_temp < 75:
                    # Linear increase between 60 and 75 degrees
                    fan_expected_speed = 2000 + ((cpu_temp - 60) * 80)  # 2000-3200 RPM
                else:
                    fan_expected_speed = 3200 + ((cpu_temp - 75) * 120)  # 3200+ RPM
                
                # Detect fan anomaly
                if fan_speed > 0:  # Only if we have actual fan speed data
                    # If actual fan speed is significantly lower than expected
                    if fan_speed < (fan_expected_speed * 0.7) and cpu_temp > 50:
                        fan_anomaly = True
                    # Or if fan is running much faster than needed at low temps
                    elif fan_speed > (fan_expected_speed * 1.5) and cpu_temp < 40:
                        fan_anomaly = True
            
            # Get battery percent if available
            battery_percent = 0
            try:
                if hasattr(psutil, 'sensors_battery'):
                    battery = psutil.sensors_battery()
                    if battery:
                        battery_percent = battery.percent
            except Exception as e:
                print(f"Error getting battery percent: {e}")
            
            # Create and save metrics
            metrics = SystemMetric(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=disk.percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                cpu_temp=cpu_temp,
                fan_speed=fan_speed,
                fan_expected_speed=fan_expected_speed,
                fan_anomaly=fan_anomaly,
                battery_percent=battery_percent,
                swap_percent=swap_percent,
                disk_read_count=disk_read_count,
                disk_write_count=disk_write_count
            )
            
            # Check for anomalies
            metrics.is_anomaly, metrics.anomaly_score = self.detect_anomaly(metrics)
            
            # Save the metrics
            metrics.save()
            
            # Create hardware issue if anomaly detected
            if metrics.is_anomaly:
                self.create_hardware_issue(metrics)
            
            # Create hardware issue for fan anomaly
            if fan_anomaly:
                self.create_fan_issue(metrics)
            
            return metrics
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            import traceback
            traceback.print_exc()
            return None

    def save_metrics(self, metrics=None, run_anomaly_detection=True):
        """
        Save metrics to database and optionally run anomaly detection.
        
        Args:
            metrics (dict, optional): Metrics to save. If None, will collect metrics.
            run_anomaly_detection (bool): Whether to run anomaly detection on the metrics.
            
        Returns:
            SystemMetric: The saved metric object
        """
        if metrics is None:
            metrics = self.collect_system_metrics()
        
        # Create a SystemMetric object
        metric_obj = SystemMetric(
            cpu_percent=metrics.get('cpu_percent', 0),
            memory_percent=metrics.get('memory_percent', 0),
            swap_percent=metrics.get('swap_percent', 0),
            disk_usage_percent=metrics.get('disk_usage_percent', 0),
            disk_read_count=metrics.get('disk_read_count', 0),
            disk_write_count=metrics.get('disk_write_count', 0),
            network_bytes_sent=metrics.get('network_bytes_sent', 0),
            network_bytes_recv=metrics.get('network_bytes_recv', 0),
            cpu_temp=metrics.get('cpu_temp', None),
            battery_percent=metrics.get('battery_percent', None),
            fan_speed=metrics.get('fan_speed', None),
        )
        
        # Run anomaly detection if requested and model is available
        if run_anomaly_detection and self.model is not None and self.scaler is not None:
            anomaly_result = self.detect_anomalies(metrics)
            if anomaly_result:
                metric_obj.is_anomaly = anomaly_result['is_anomaly']
                metric_obj.anomaly_score = anomaly_result['anomaly_score']
                
                # Add fan anomaly detection
                # This ensures that a fan anomaly will also trigger the overall anomaly flag
                if metrics.get('fan_anomaly', False):
                    metric_obj.is_anomaly = True
                    metric_obj.fan_anomaly = True
                    
                # If it's an anomaly, analyze and create hardware issues
                if metric_obj.is_anomaly:
                    analysis = self.analyze_hardware_issues(metrics)
                    metric_obj.save()  # Save first to get the ID
                    
                    # Create HardwareIssue objects for each issue
                    for i, issue in enumerate(analysis['issues']):
                        HardwareIssue.objects.create(
                            metric=metric_obj,
                            issue_type=issue,
                            description=issue,
                            recommendation=analysis['recommendations'][i] if i < len(analysis['recommendations']) else ""
                        )
                    
                    return metric_obj
        # Save the metric
        metric_obj.save()
        return metric_obj
    
    def train_model(self, training_samples=300):
        """Train a new anomaly detection model.
        
        Args:
            training_samples: Number of samples to use for training.
            
        Returns:
            bool: True if training succeeded, False otherwise.
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Starting model training")
            
            # Get the most recent metrics for training
            metrics = SystemMetric.objects.order_by('-timestamp')[:training_samples]
            metrics_count = metrics.count()
            
            if metrics_count < 50:  # Minimum threshold for meaningful training
                logger.warning(f"Not enough training data: {metrics_count} samples")
                return False
            
            # Extract features for training
            import numpy as np
            features = []
            
            for metric in metrics:
                features.append([
                    metric.cpu_percent,
                    metric.memory_percent,
                    metric.disk_usage_percent,
                    metric.network_bytes_sent / 1024,  # Scale to KB to avoid numerical issues
                    metric.network_bytes_recv / 1024,  # Scale to KB to avoid numerical issues
                ])
            
            X = np.array(features)
            
            # Train isolation forest model for anomaly detection
            from sklearn.ensemble import IsolationForest
            
            # Adjust contamination based on dataset size
            contamination = 0.05  # Default 5% anomalies
            if metrics_count < 100:
                contamination = 0.1  # Increase for small datasets for better detection
            
            model = IsolationForest(
                n_estimators=100,
                contamination=contamination,
                random_state=42
            )
            
            model.fit(X)
            
            # Save model for later use
            import pickle
            import os
            
            # Create models directory if it doesn't exist
            os.makedirs('models', exist_ok=True)
            
            with open('models/anomaly_detection_model.pkl', 'wb') as f:
                pickle.dump(model, f)
            
            # Record training event
            ModelTrainingHistory.objects.create(
                samples=metrics_count,
                parameters={
                    'n_estimators': 100,
                    'contamination': contamination,
                    'features': ['cpu_percent', 'memory_percent', 'disk_usage_percent', 'network_sent_kb', 'network_recv_kb']
                },
                accuracy=0.95,  # Placeholder, replace with actual validation metrics if available
                notes=f"Trained with {metrics_count} samples"
            )
            
            return True
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def detect_anomalies(self, metrics):
        """
        Detect anomalies in the system metrics.
        
        Args:
            metrics (dict): System metrics
            
        Returns:
            dict: Anomaly detection results or None if detection fails
        """
        if self.model is None or self.scaler is None:
            logging.warning("Model not trained yet")
            return None
        
        try:
            # Convert metrics to DataFrame with expected columns
            metrics_df = pd.DataFrame([metrics])
            
            # Handle missing columns
            for col in self.columns:
                if col not in metrics_df.columns:
                    metrics_df[col] = 0
            
            # Ensure columns are in the correct order
            metrics_df = metrics_df[self.columns]
            
            # Scale the features
            scaled_metrics = self.scaler.transform(metrics_df)
            
            # Predict anomaly
            prediction = self.model.predict(scaled_metrics)
            score = self.model.decision_function(scaled_metrics)
            
            # Return result (-1 is anomaly, 1 is normal)
            return {
                'is_anomaly': prediction[0] == -1,
                'anomaly_score': score[0]
            }
        except Exception as e:
            logging.error(f"Error detecting anomalies: {e}")
            return None
    
    def analyze_hardware_issues(self, metrics):
        """
        Analyze specific hardware issues based on metrics and provide recommendations.
        
        Args:
            metrics (dict): System metrics
            
        Returns:
            dict: Issues and recommendations
        """
        issues = []
        recommendations = []
        
        # Define thresholds for different metrics
        high_cpu_threshold = 90
        high_memory_threshold = 85
        high_swap_threshold = 75
        high_disk_threshold = 90
        high_temp_threshold = 80  # in Celsius
        low_battery_threshold = 15
        
        # CPU usage check
        if metrics.get('cpu_percent', 0) > high_cpu_threshold:
            issues.append("High CPU usage detected")
            recommendations.append(
                "Check for runaway processes using Task Manager or htop. "
                "Consider upgrading CPU if consistently high during normal usage."
            )
        
        # Memory usage check
        if metrics.get('memory_percent', 0) > high_memory_threshold:
            issues.append("High memory usage detected")
            recommendations.append(
                "Close unnecessary applications. Consider adding more RAM "
                "if consistently high during normal usage."
            )
        
        # Swap usage check
        if metrics.get('swap_percent', 0) > high_swap_threshold:
            issues.append("High swap memory usage detected")
            recommendations.append(
                "Your system is relying heavily on swap memory, which is slower than RAM. "
                "Consider adding more physical RAM or optimizing memory usage."
            )
        
        # Disk usage check
        if metrics.get('disk_usage_percent', 0) > high_disk_threshold:
            issues.append("High disk usage detected")
            recommendations.append(
                "Free up disk space by removing unnecessary files or applications. "
                "Consider upgrading storage capacity."
            )
        
        # Temperature check
        if metrics.get('cpu_temp', 0) > high_temp_threshold:
            issues.append("High CPU temperature detected")
            recommendations.append(
                "Check that cooling fans are working properly. Clean dust from heat sinks. "
                "Ensure proper ventilation. Consider applying new thermal paste if problem persists."
            )
        
        # Battery check
        if 0 < metrics.get('battery_percent', 100) < low_battery_threshold:
            issues.append("Low battery level detected")
            recommendations.append(
                "Connect to power source. If battery drains quickly, consider battery replacement."
            )
        
        # Add fan analysis
        fan_analysis = self.analyze_fan_issues(metrics)
        issues.extend(fan_analysis['issues'])
        recommendations.extend(fan_analysis['recommendations'])
        
        return {
            'issues': issues,
            'recommendations': recommendations
        }

    def analyze_fan_issues(self, metrics):
        """
        Analyze fan-related issues based on metrics.
        
        Args:
            metrics (dict): System metrics
            
        Returns:
            dict: Fan-related issues and recommendations
        """
        issues = []
        recommendations = []
        
        # Define thresholds for fan metrics
        low_fan_speed_threshold = 1000  # RPM, adjust based on your system
        
        # Check if fan metrics are available
        if 'fan_speed' in metrics and metrics['fan_speed'] is not None:
            # Fan speed check - if fan speed is 0 but temperature is high
            if metrics['fan_speed'] == 0 and metrics.get('cpu_temp', 0) > 50:
                issues.append("Fan not spinning but CPU temperature is elevated")
                recommendations.append(
                    "Check if CPU fan is properly connected and functioning. "
                    "Ensure the fan is not obstructed by dust or debris. "
                    "Replace the fan if necessary."
                )
            # Low fan speed check
            elif 0 < metrics['fan_speed'] < low_fan_speed_threshold and metrics.get('cpu_temp', 0) > 60:
                issues.append("Low fan speed with high CPU temperature")
                recommendations.append(
                    "Clean dust from fans and heat sinks. Check fan settings in BIOS. "
                    "Consider replacing the fan if problem persists or installing additional cooling."
                )
            
            # Additional check for systems with fans but no fan speed reported
            if isinstance(metrics.get('fans', None), list) and len(metrics.get('fans', [])) > 0:
                inactive_fans = [fan for fan in metrics['fans'] if fan.get('status') == 'Inactive']
                if inactive_fans and metrics.get('cpu_temp', 0) > 60:
                    issues.append(f"{len(inactive_fans)} fan(s) inactive with elevated CPU temperature")
                    recommendations.append(
                        "Check inactive fans for obstructions or mechanical issues. "
                        "Ensure all fan connectors are properly seated on the motherboard. "
                        "Replace non-functioning fans."
                    )
        
        # Handle systems with no fan data but high temperatures
        elif metrics.get('cpu_temp', 0) > 75:
            issues.append("High CPU temperature with unknown fan status")
            recommendations.append(
                "Check all cooling fans are functioning properly. "
                "Clean dust from heat sinks and ensure proper ventilation. "
                "Consider installing monitoring software that can detect fan speeds."
            )
        
        return {
            'issues': issues,
            'recommendations': recommendations
        }
    
    def create_fan_issue(self, metrics):
        """
        Create a hardware issue for fan anomalies.
        
        Args:
            metrics (SystemMetric): The metrics object with fan anomaly
        
        Returns:
            HardwareIssue: The created issue
        """
        try:
            from .models import HardwareIssue
            from django.utils import timezone
            
            # Check if we already have an unresolved fan issue
            existing_issue = HardwareIssue.objects.filter(
                issue_type='cooling_system', 
                is_resolved=False
            ).first()
            
            if existing_issue:
                # Update the existing issue with new data
                existing_issue.timestamp = timezone.now()
                existing_issue.metric = metrics
                existing_issue.save()
                return existing_issue
            
            # Determine issue description and recommendation
            description = "Cooling fan anomaly detected"
            recommendation = "Check if CPU fan is working properly."
            
            if metrics.fan_speed == 0 and metrics.cpu_temp > 50:
                description = "Fan not spinning but CPU temperature is elevated"
                recommendation = "Check if CPU fan is properly connected and functioning. Replace if necessary."
            elif metrics.fan_speed < (metrics.fan_expected_speed * 0.7) and metrics.cpu_temp > 50:
                description = "Fan speed too low for current temperature"
                recommendation = (
                    "Clean dust from fans and heat sinks. Check fan settings in BIOS. "
                    "Consider replacing the fan if problem persists."
                )
            elif metrics.fan_speed > (metrics.fan_expected_speed * 1.5) and metrics.cpu_temp < 40:
                description = "Fan running unusually fast at low temperature"
                recommendation = (
                    "Check for fan controller issues. Consider updating BIOS or "
                    "fan control software. Ensure temperature sensors are working properly."
                )
            
            # Create the issue
            issue = HardwareIssue.objects.create(
                issue_type='cooling_system',
                description=description,
                is_resolved=False,
                metric=metrics,
                recommendation=recommendation
            )
            
            return issue
            
        except Exception as e:
            print(f"Error creating fan issue: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_system_summary(self):
        """
        Get a summary of the system's current state.
        
        Returns:
            dict: System summary
        """
        # Get current metrics
        current_metrics = self.collect_system_metrics()
        
        # Get recent anomalies
        recent_anomalies = SystemMetric.objects.filter(
            is_anomaly=True
        ).order_by('-timestamp')[:5]
        
        # Get unresolved issues
        unresolved_issues = HardwareIssue.objects.filter(
            is_resolved=False
        ).order_by('-timestamp')
        
        # Get metrics history for trends
        metrics_history = SystemMetric.objects.order_by('-timestamp')[:100]
        
        # Calculate trend data
        cpu_trend = [m.cpu_percent for m in metrics_history]
        memory_trend = [m.memory_percent for m in metrics_history]
        disk_trend = [m.disk_usage_percent for m in metrics_history]
        
        # Prepare summary
        summary = {
            'current_state': current_metrics,
            'recent_anomalies': [
                {
                    'timestamp': a.timestamp,
                    'anomaly_score': a.anomaly_score,
                    'issues': [
                        {'type': i.issue_type, 'recommendation': i.recommendation}
                        for i in a.issues.all()
                    ]
                }
                for a in recent_anomalies
            ],
            'unresolved_issues': [
                {
                    'id': i.id,
                    'timestamp': i.timestamp,
                    'issue_type': i.issue_type,
                    'recommendation': i.recommendation
                }
                for i in unresolved_issues
            ],
            'trends': {
                'cpu': cpu_trend,
                'memory': memory_trend,
                'disk': disk_trend
            },
            'model_status': {
                'trained': self.model is not None,
                'last_training': ModelTrainingHistory.objects.order_by('-trained_at').first().trained_at
                if ModelTrainingHistory.objects.exists() else None
            }
        }
        
        return summary

    def get_system_info(self):
        """
        Get detailed system hardware information.
        
        Returns:
            dict: Detailed system hardware information
        """
        try:
            # Import locally to avoid circular imports
            from .views import get_fan_info_for_system  # Use this function instead
            
            # Get basic system info...
            system_info = {
                # Your existing code to collect system info...
            }
            
            # Add fan information
            system_info['fans'] = get_fan_info_for_system()  # Call without request
            
            return system_info
        except Exception as e:
            print(f"Error getting system info: {e}")
            return {}

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def train(self, request):
        """Train a new model."""
        # Get number of samples from request data
        samples = request.data.get('samples', 300)
        try:
            samples = int(samples)
        except (TypeError, ValueError):
            samples = 300
        
        # Check if we have enough data
        available_samples = SystemMetric.objects.count()
        
        if available_samples < 50:  # Minimum threshold for training
            return Response({
                "success": False,
                "detail": f"Not enough training data. Only {available_samples} samples available, minimum required is 50.",
                "available_samples": available_samples,
                "required_samples": 50
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # If user requested more samples than we have, adjust
        if samples > available_samples:
            samples = available_samples
        
        try:
            # Train the model
            success = self.train_model(training_samples=samples)
            
            if success:
                # Get the newly created training history
                latest_training = ModelTrainingHistory.objects.order_by('-trained_at').first()
                serializer = self.get_serializer(latest_training)
                return Response({
                    "success": True,
                    "detail": f"Model trained successfully with {samples} samples.",
                    "data": serializer.data
                })
            else:
                return Response({
                    "success": False,
                    "detail": "Model training failed. See logs for details."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error training model: {str(e)}")
            logger.error(traceback.format_exc())
            
            return Response({
                "success": False,
                "detail": f"Error training model: {str(e)}",
                "error_type": type(e).__name__
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
