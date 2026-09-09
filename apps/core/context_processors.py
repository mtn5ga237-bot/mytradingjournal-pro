from .models import UserSettings


def user_settings(request):
    """Expose the logged-in user's currency/balance settings to every template."""
    if request.user.is_authenticated:
        settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
        return {'user_settings': settings_obj}
    return {'user_settings': None}
