from django.apps import AppConfig


class HardwareApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hardware_api'
    
    def ready(self):
        """
        Initialize the app.
        This is called when the app is ready.
        Use this to perform initialization tasks.
        """
        # Import signals
        import hardware_api.signals
        