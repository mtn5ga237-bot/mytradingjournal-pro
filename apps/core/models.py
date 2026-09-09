from django.conf import settings
from django.db import models


class UserSettings(models.Model):
    CURRENCY_CHOICES = [
        ('EUR', 'EUR (€)'),
        ('USD', 'USD ($)'),
        ('GBP', 'GBP (£)'),
        ('JPY', 'JPY (¥)'),
    ]

    CURRENCY_SYMBOLS = {'EUR': '€', 'USD': '$', 'GBP': '£', 'JPY': '¥'}

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='settings'
    )
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='EUR')
    initial_balance = models.DecimalField(max_digits=14, decimal_places=2, default=10000)

    class Meta:
        verbose_name = 'Paramètres utilisateur'
        verbose_name_plural = 'Paramètres utilisateurs'

    def __str__(self):
        return f"Paramètres de {self.user.username}"

    @property
    def currency_symbol(self):
        return self.CURRENCY_SYMBOLS.get(self.currency, self.currency)
