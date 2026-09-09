from django.contrib import admin

from .models import Trade


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'paire', 'direction', 'date_ouverture', 'resultat_monetaire',
        'strategie', 'session', 'respect_plan',
    )
    list_filter = ('paire', 'direction', 'strategie', 'session', 'respect_plan')
    search_fields = ('user__username', 'paire', 'strategie', 'commentaires')
    date_hierarchy = 'date_ouverture'
