from django.contrib import admin
from django.contrib.admin.models import LogEntry

from .models import UserSettings


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'initial_balance')
    search_fields = ('user__username', 'user__email')
    list_filter = ('currency',)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """Read-only audit trail ('suivi') of every ajout/modification/suppression
    made through the Django admin — by the auto-created admin account or any
    other staff user. Django logs these automatically on every admin CRUD
    action; this just makes the full history browsable and filterable
    instead of only the last few actions on the admin index page."""
    date_hierarchy = 'action_time'
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag_label', 'change_message')
    list_filter = ('action_flag', 'content_type', 'user')
    search_fields = ('object_repr', 'change_message', 'user__username')
    ordering = ('-action_time',)

    ACTION_LABELS = {1: 'Ajout', 2: 'Modification', 3: 'Suppression'}

    @admin.display(description='Action')
    def action_flag_label(self, obj):
        return self.ACTION_LABELS.get(obj.action_flag, obj.action_flag)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
