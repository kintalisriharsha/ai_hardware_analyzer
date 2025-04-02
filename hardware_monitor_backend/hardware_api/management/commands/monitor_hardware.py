import time
import logging
from django.core.management.base import BaseCommand
from hardware_api.hardware_monitor import HardwareMonitorService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs the hardware monitoring service in the background'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Interval in seconds between metric collections'
        )
        
        parser.add_argument(
            '--train',
            action='store_true',
            help='Train a new model before starting monitoring'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        train = options['train']
        
        self.stdout.write(self.style.SUCCESS('Starting hardware monitoring service'))
        
        # Initialize the hardware monitor
        monitor = HardwareMonitorService()
        
        # Train a new model if requested
        if train:
            self.stdout.write('Training a new model...')
            success = monitor.train_model()
            if success:
                self.stdout.write(self.style.SUCCESS('Model training completed'))
            else:
                self.stdout.write(self.style.ERROR('Model training failed'))
        
        # Continuous monitoring loop
        try:
            self.stdout.write(f'Collecting metrics every {interval} seconds. Press Ctrl+C to stop.')
            while True:
                metrics = monitor.collect_system_metrics()
                monitor.save_metrics(metrics)
                self.stdout.write(f'Metrics collected at {time.strftime("%Y-%m-%d %H:%M:%S")}')
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Monitoring stopped'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during monitoring: {e}'))

        finally:
            # Cleanup actions if needed
            monitor.cleanup()
            self.stdout.write(self.style.SUCCESS('Cleanup completed'))
            self.stdout.write(self.style.SUCCESS('Hardware monitoring service stopped'))