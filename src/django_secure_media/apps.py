from django.apps import AppConfig


class DjangoSecureMediaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    default_registry = "django_secure_media.policies.MediaAccessPolicyRegistry"
    name = "django_secure_media"

    def ready(self):
        super().ready()
        self.module.autodiscover()
