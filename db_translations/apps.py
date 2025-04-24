from django.apps import AppConfig


class DbTranslationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'db_translations'
    verbose_name = 'Database Translations'

    def ready(self):
        # Import signals
        import db_translations.signals
