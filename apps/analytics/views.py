import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.core import stats as stats_engine
from apps.core.models import UserSettings
from apps.trades.models import Trade

from .ai import generate_ai_insights


@login_required
def stats_view(request):
    trades = list(Trade.objects.filter(user=request.user))
    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)

    kpis = stats_engine.core_stats(trades, user_settings.initial_balance)
    rr = stats_engine.rr_stats(trades)
    monthly = stats_engine.monthly_performance(trades)
    winrate_pairs = stats_engine.winrate_by_pair(trades)
    strategies = stats_engine.strategy_stats(trades)

    context = {
        'kpis': kpis,
        'rr': rr,
        'strategies': strategies,
        'monthly_labels': json.dumps([m['month'] for m in monthly]),
        'monthly_data': json.dumps([m['pnl'] for m in monthly]),
        'winrate_pair_labels': json.dumps([p['pair'] for p in winrate_pairs]),
        'winrate_pair_data': json.dumps([p['winrate'] for p in winrate_pairs]),
        'winrate_pairs': winrate_pairs,
    }
    return render(request, 'analytics/stats.html', context)


@login_required
def ai_coach_view(request):
    result = generate_ai_insights(request.user)
    return render(request, 'analytics/ai_coach.html', result)
