from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class Trade(models.Model):
    PAIR_CHOICES = [
        ('EUR/USD', 'EUR/USD'), ('GBP/USD', 'GBP/USD'), ('USD/JPY', 'USD/JPY'),
        ('USD/CHF', 'USD/CHF'), ('AUD/USD', 'AUD/USD'), ('USD/CAD', 'USD/CAD'),
        ('NZD/USD', 'NZD/USD'), ('EUR/GBP', 'EUR/GBP'), ('GBP/JPY', 'GBP/JPY'),
        ('XAU/USD', 'XAU/USD (Or)'), ('BTC/USD', 'BTC/USD'), ('ETH/USD', 'ETH/USD'),
    ]
    DIRECTION_CHOICES = [('achat', 'Achat (Long)'), ('vente', 'Vente (Short)')]
    STRATEGY_CHOICES = [
        ('Scalping', 'Scalping'), ('Day Trading', 'Day Trading'), ('Swing Trading', 'Swing Trading'),
        ('Breakout', 'Breakout'), ('Range', 'Range'), ('News Trading', 'News Trading'),
        ('Grid', 'Grid'), ('DCA', 'DCA'),
    ]
    SESSION_CHOICES = [
        ('Asiatique', 'Asiatique'), ('Européenne', 'Européenne'),
        ('Américaine', 'Américaine'), ('Overlap', 'Overlap'),
    ]
    MOOD_BEFORE_CHOICES = [
        ('Confiant', 'Confiant'), ('Stressé', 'Stressé'), ('Neutre', 'Neutre'),
        ('Excited', 'Excité'), ('Fatigué', 'Fatigué'),
    ]
    MOOD_AFTER_CHOICES = [
        ('Satisfait', 'Satisfait'), ('Déçu', 'Déçu'), ('Frustré', 'Frustré'),
        ('Content', 'Content'), ('Indifférent', 'Indifférent'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trades'
    )

    date_ouverture = models.DateTimeField(verbose_name="Date d'ouverture")
    date_fermeture = models.DateTimeField(verbose_name="Date de fermeture")
    paire = models.CharField(max_length=20, choices=PAIR_CHOICES)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    taille = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Taille (lots)")
    strategie = models.CharField(max_length=30, choices=STRATEGY_CHOICES)
    session = models.CharField(max_length=20, choices=SESSION_CHOICES, blank=True)

    prix_entree = models.DecimalField(max_digits=14, decimal_places=5)
    prix_sortie = models.DecimalField(max_digits=14, decimal_places=5)
    stop_loss = models.DecimalField(max_digits=14, decimal_places=5, null=True, blank=True)
    take_profit = models.DecimalField(max_digits=14, decimal_places=5, null=True, blank=True)

    resultat_pips = models.DecimalField(max_digits=10, decimal_places=1, verbose_name="Résultat (pips)")
    resultat_monetaire = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Résultat (devise)")
    commission_swap = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    humeur_avant = models.CharField(max_length=20, choices=MOOD_BEFORE_CHOICES, blank=True)
    humeur_apres = models.CharField(max_length=20, choices=MOOD_AFTER_CHOICES, blank=True)
    respect_plan = models.BooleanField(default=True, verbose_name="Respect du plan")
    commentaires = models.TextField(blank=True)

    screenshot = models.ImageField(
        upload_to='screenshots/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'webp', 'gif'])],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_ouverture', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date_ouverture']),
        ]

    def __str__(self):
        return f"{self.paire} {self.direction} — {self.date_ouverture:%Y-%m-%d}"

    @property
    def is_win(self):
        return self.net_result > 0

    @property
    def net_result(self):
        return self.resultat_monetaire - self.commission_swap

    @property
    def risk_reward_achieved(self):
        """R:R actually achieved, using stop distance as the risk unit (matches the
        Pine strategy's ATR-based initial risk model when stop_loss is filled in)."""
        if not self.stop_loss:
            return None
        risk = abs(self.prix_entree - self.stop_loss)
        if risk == 0:
            return None
        reward = abs(self.prix_sortie - self.prix_entree)
        if self.direction == 'achat' and self.prix_sortie < self.prix_entree:
            reward = -reward
        if self.direction == 'vente' and self.prix_sortie > self.prix_entree:
            reward = -reward
        return float(reward / risk)
