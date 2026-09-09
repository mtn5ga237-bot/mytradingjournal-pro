from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Trade


def make_trade(user, **kwargs):
    defaults = dict(
        user=user,
        date_ouverture=timezone.now() - timedelta(hours=2),
        date_fermeture=timezone.now(),
        paire='XAU/USD',
        direction='achat',
        taille=1,
        strategie='Breakout',
        session='Américaine',
        prix_entree=2000,
        prix_sortie=2010,
        stop_loss=1995,
        take_profit=2015,
        resultat_pips=100,
        resultat_monetaire=100,
        commission_swap=2,
    )
    defaults.update(kwargs)
    return Trade.objects.create(**defaults)


class TradeModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='testpass123')

    def test_net_result_subtracts_commission(self):
        trade = make_trade(self.user, resultat_monetaire=100, commission_swap=5)
        self.assertEqual(trade.net_result, 95)

    def test_is_win(self):
        winner = make_trade(self.user, resultat_monetaire=50, commission_swap=0)
        loser = make_trade(self.user, resultat_monetaire=-20, commission_swap=0)
        self.assertTrue(winner.is_win)
        self.assertFalse(loser.is_win)

    def test_risk_reward_achieved_long(self):
        trade = make_trade(self.user, direction='achat', prix_entree=2000, prix_sortie=2015, stop_loss=1995)
        self.assertAlmostEqual(trade.risk_reward_achieved, 3.0)

    def test_risk_reward_none_without_stop(self):
        trade = make_trade(self.user, stop_loss=None)
        self.assertIsNone(trade.risk_reward_achieved)


class TradeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.client.login(username='alice', password='testpass123')

    def test_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('trades:list'))
        self.assertEqual(response.status_code, 302)

    def test_user_only_sees_own_trades(self):
        mine = make_trade(self.user)
        make_trade(self.other)
        response = self.client.get(reverse('trades:list'))
        self.assertContains(response, mine.paire)
        self.assertEqual(len(response.context['trades']), 1)

    def test_create_trade(self):
        response = self.client.post(reverse('trades:create'), {
            'date_ouverture': '2025-01-01T10:00',
            'date_fermeture': '2025-01-01T12:00',
            'paire': 'XAU/USD',
            'direction': 'achat',
            'taille': '1.00',
            'strategie': 'Breakout',
            'session': 'Américaine',
            'prix_entree': '2000.00000',
            'prix_sortie': '2010.00000',
            'resultat_pips': '100.0',
            'resultat_monetaire': '100.00',
            'commission_swap': '0',
            'respect_plan': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Trade.objects.filter(user=self.user).count(), 1)
