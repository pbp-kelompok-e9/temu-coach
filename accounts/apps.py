from django.apps import AppConfig
from django.db.models.signals import post_migrate

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from django.contrib.auth import get_user_model

        def create_default_admin(sender, **kwargs):
            User = get_user_model()
            if not User.objects.filter(username='temuadmin').exists():
                User.objects.create_superuser(
                    username='temuadmin',
                    email='temuadmin@example.com',
                    password='temucoach123'
                )
                print("✅ Default admin created: temuadmin / temucoach123")
            else:
                print("ℹ️ Default admin already exists.")

        post_migrate.connect(create_default_admin, sender=self)
