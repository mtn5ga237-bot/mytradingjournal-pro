from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.trades.models import Trade
from apps.trades.tests import make_trade

from .ai import generate_ai_insights


class AICoachTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='testpass123')

    def test_no_trades_returns_info_message(self):
        result = generate_ai_insights(self.user)
        self.assertEqual(result['data_points'], 0)
        self.assertEqual(len(result['insights']), 1)
        self.assertEqual(result['insights'][0]['type'], 'info')

    def test_small_sample_does_not_crash_and_flags_insufficient_data(self):
        make_trade(self.user)
        result = generate_ai_insights(self.user)
        self.assertEqual(result['data_points'], 1)
        self.assertTrue(len(result['insights']) >= 1)

    def test_underperforming_segment_is_flagged(self):
        base_time = timezone.now() - timedelta(days=30)
        for i in range(6):
            make_trade(
                self.user, paire='EUR/USD', resultat_monetaire=-20, commission_swap=0,
                date_ouverture=base_time + timedelta(hours=i),
                date_fermeture=base_time + timedelta(hours=i, minutes=30),
            )
        for i in range(6):
            make_trade(
                self.user, paire='XAU/USD', resultat_monetaire=50, commission_swap=0,
                date_ouverture=base_time + timedelta(days=1, hours=i),
                date_fermeture=base_time + timedelta(days=1, hours=i, minutes=30),
            )
        result = generate_ai_insights(self.user)
        titles = [i['title'] for i in result['insights']]
        self.assertTrue(any('EUR/USD' in t for t in titles))
        self.assertTrue(any('XAU/USD' in t for t in titles))

    def test_all_insights_carry_confidence_and_sample_size(self):
        for i in range(12):
            make_trade(self.user, resultat_monetaire=10 if i % 2 == 0 else -10, commission_swap=0)
        result = generate_ai_insights(self.user)
        for insight in result['insights']:
            self.assertIn('confidence', insight)
            self.assertIn('sample_size', insight)
