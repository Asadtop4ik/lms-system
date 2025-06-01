from django.apps import AppConfig

class LmsappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lmsapp'

    def ready(self):
        import lmsapp.templatetags.custom_filters