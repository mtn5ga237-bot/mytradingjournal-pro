import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.core import stats as stats_engine
from apps.core.models import UserSettings
from apps.trades.models import Trade


@login_required
def index(request):
    user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
    trades = list(Trade.objects.filter(user=request.user))

    kpis = stats_engine.core_stats(trades, user_settings.initial_balance)
    curve = stats_engine.equity_curve(trades, user_settings.initial_balance)
    pairs = stats_engine.pair_distribution(trades)
    winrate_pairs = stats_engine.winrate_by_pair(trades)

    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    cal = stats_engine.calendar_month_grid(trades, year, month)

    context = {
        'kpis': kpis,
        'equity_labels': json.dumps([p['label'] for p in curve]),
        'equity_data': json.dumps([p['balance'] for p in curve]),
        'pair_labels': json.dumps([p['pair'] for p in pairs]),
        'pair_data': json.dumps([p['count'] for p in pairs]),
        'winrate_pair_labels': json.dumps([p['pair'] for p in winrate_pairs]),
        'winrate_pair_data': json.dumps([p['winrate'] for p in winrate_pairs]),
        'calendar': cal,
        'calendar_year': year,
        'calendar_month': month,
        'last_trades': trades[:5],
        'user_settings': user_settings,
    }
    return render(request, 'dashboard/index.html', context)
