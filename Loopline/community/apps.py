from django.apps import AppConfig

# This class was already here
class CommunityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'community'

    # Add this method VVV
    def ready(self):
        import community.signals # Or: from . import signals
        print("Community app signals connected.") # Optional

    
