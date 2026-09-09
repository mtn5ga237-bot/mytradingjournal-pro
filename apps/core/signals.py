import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import UserSettings

DEFAULT_ADMIN_USERNAME = os.environ.get('DJANGO_ADMIN_USERNAME', 'admin')
DEFAULT_ADMIN_EMAIL = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@mytradingjournal.local')
DEFAULT_ADMIN_PASSWORD = os.environ.get('DJANGO_ADMIN_PASSWORD', 'ChangeMoi123!')


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSettings.objects.get_or_create(user=instance)


@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    """Ensure a superuser always exists so the app is usable right after
    `migrate`, without a manual `createsuperuser` step. Only fires for this
    app's own migration pass, and only creates an account if none exists —
    it never touches or resets an existing superuser's password.

    Escape hatch: if DJANGO_ADMIN_RESET_PASSWORD is set, force-reset
    DEFAULT_ADMIN_USERNAME's password to it even when that account already
    exists. This is for recovering access to a deployment whose admin
    password was lost/forgotten — unset the env var again afterwards so a
    later redeploy can't silently reset a password you've since changed."""
    if sender.name != 'apps.core':
        return

    User = get_user_model()
    reset_password = os.environ.get('DJANGO_ADMIN_RESET_PASSWORD')

    if User.objects.filter(is_superuser=True).exists():
        if reset_password:
            user, _ = User.objects.get_or_create(
                username=DEFAULT_ADMIN_USERNAME,
                defaults={'email': DEFAULT_ADMIN_EMAIL, 'is_staff': True, 'is_superuser': True},
            )
            user.is_staff = True
            user.is_superuser = True
            user.set_password(reset_password)
            user.save()
            print(
                "\n"
                "==================== MOT DE PASSE ADMIN REINITIALISE ====================\n"
                f"  Identifiant : {DEFAULT_ADMIN_USERNAME}\n"
                f"  Nouveau mot de passe : {reset_password}\n"
                "  -> Retirez DJANGO_ADMIN_RESET_PASSWORD une fois connecte.\n"
                "===========================================================================\n"
            )
        return

    User.objects.create_superuser(
        username=DEFAULT_ADMIN_USERNAME,
        email=DEFAULT_ADMIN_EMAIL,
        password=DEFAULT_ADMIN_PASSWORD,
    )
    print(
        "\n"
        "==================== COMPTE ADMIN CREE AUTOMATIQUEMENT ====================\n"
        f"  Identifiant : {DEFAULT_ADMIN_USERNAME}\n"
        f"  Mot de passe : {DEFAULT_ADMIN_PASSWORD}\n"
        "  -> Changez ce mot de passe une fois connecte (admin/ ou votre profil).\n"
        "=============================================================================\n"
    )
