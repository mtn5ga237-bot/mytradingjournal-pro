"""Shared statistics engine over a user's trades.

Used by both the dashboard (equity curve, calendar, top-line KPIs) and the
analytics app (expectancy, per-strategy breakdown) so the numbers agree
everywhere in the app. Pure Python over an already-fetched list of Trade
rows — trade counts for a personal journal are small enough that this is
simpler and more flexible than pushing every aggregation into the ORM.
"""
import calendar
from collections import defaultdict
from datetime import date


def _net(trade):
    return float(trade.net_result)


def core_stats(trades, initial_balance):
    """Headline KPIs: balance, winrate, profit factor, expectancy, drawdown."""
    trades = list(trades)
    initial_balance = float(initial_balance)
    n = len(trades)
    if n == 0:
        return {
            'total_trades': 0, 'wins': 0, 'losses': 0, 'winrate': 0.0,
            'profit_factor': 0.0, 'gross_profit': 0.0, 'gross_loss': 0.0,
            'avg_trade': 0.0, 'balance': initial_balance, 'balance_change_pct': 0.0,
            'max_drawdown_pct': 0.0, 'net_pnl': 0.0,
        }

    results = [_net(t) for t in trades]
    wins = [r for r in results if r > 0]
    losses = [r for r in results if r <= 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    net_pnl = sum(results)
    balance = initial_balance + net_pnl

    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (
        float('inf') if gross_profit > 0 else 0.0
    )
    winrate = (len(wins) / n) * 100
    avg_trade = net_pnl / n
    balance_change_pct = (net_pnl / initial_balance) * 100 if initial_balance else 0.0

    # Max drawdown over the equity curve ordered chronologically.
    chronological = sorted(trades, key=lambda t: t.date_ouverture)
    running = initial_balance
    peak = initial_balance
    max_dd = 0.0
    for t in chronological:
        running += _net(t)
        peak = max(peak, running)
        if peak > 0:
            dd = (peak - running) / peak * 100
            max_dd = max(max_dd, dd)

    return {
        'total_trades': n, 'wins': len(wins), 'losses': len(losses), 'winrate': winrate,
        'profit_factor': profit_factor, 'gross_profit': gross_profit, 'gross_loss': gross_loss,
        'avg_trade': avg_trade, 'balance': balance, 'balance_change_pct': balance_change_pct,
        'max_drawdown_pct': max_dd, 'net_pnl': net_pnl,
    }


def rr_stats(trades):
    """Average R:R on wins vs true per-trade expectancy in R, restricted to
    trades where a stop loss was recorded (the only ones with a defined risk unit)."""
    rr_values = []
    win_rr = []
    for t in trades:
        r = t.risk_reward_achieved
        if r is None:
            continue
        rr_values.append(r)
        if r > 0:
            win_rr.append(r)

    avg_rr = sum(win_rr) / len(win_rr) if win_rr else 0.0
    expectancy_r = sum(rr_values) / len(rr_values) if rr_values else 0.0
    return {
        'avg_rr': avg_rr,
        'expectancy_r': expectancy_r,
        'rr_sample_size': len(rr_values),
    }


def equity_curve(trades, initial_balance):
    chronological = sorted(trades, key=lambda t: t.date_ouverture)
    running = float(initial_balance)
    points = [{'label': 'Départ', 'balance': running}]
    for t in chronological:
        running += _net(t)
        points.append({'label': t.date_ouverture.strftime('%d/%m/%y'), 'balance': round(running, 2)})
    return points


def pair_distribution(trades):
    counts = defaultdict(int)
    for t in trades:
        counts[t.paire] += 1
    return [{'pair': k, 'count': v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]


def monthly_performance(trades):
    totals = defaultdict(float)
    for t in trades:
        key = t.date_ouverture.strftime('%Y-%m')
        totals[key] += _net(t)
    ordered = sorted(totals.items())
    return [{'month': k, 'pnl': round(v, 2)} for k, v in ordered]


def winrate_by_pair(trades):
    by_pair = defaultdict(list)
    for t in trades:
        by_pair[t.paire].append(_net(t))
    out = []
    for pair, results in by_pair.items():
        wins = sum(1 for r in results if r > 0)
        out.append({'pair': pair, 'winrate': round((wins / len(results)) * 100, 1), 'count': len(results)})
    return sorted(out, key=lambda x: -x['count'])


def strategy_stats(trades):
    by_strategy = defaultdict(list)
    for t in trades:
        by_strategy[t.strategie].append(t)
    out = []
    for strategie, ts in by_strategy.items():
        results = [_net(t) for t in ts]
        wins = sum(1 for r in results if r > 0)
        out.append({
            'strategie': strategie,
            'count': len(ts),
            'winrate': round((wins / len(ts)) * 100, 1),
            'total_pnl': round(sum(results), 2),
            'avg_pnl': round(sum(results) / len(ts), 2),
        })
    return sorted(out, key=lambda x: -x['total_pnl'])


def calendar_month_grid(trades, year, month):
    """Weeks x days grid (Monday first) with daily P&L for the given month."""
    daily = defaultdict(float)
    for t in trades:
        d = t.date_ouverture.date()
        if d.year == year and d.month == month:
            daily[d.day] += _net(t)

    cal = calendar.Calendar(firstweekday=0)
    weeks = []
    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(None)
            else:
                row.append({'day': day, 'pnl': round(daily.get(day, 0.0), 2), 'has_trades': day in daily})
        weeks.append(row)

    month_total = sum(daily.values())
    return {
        'weeks': weeks,
        'month_total': round(month_total, 2),
        'month_date': date(year, month, 1),
        'prev': (year - 1, 12) if month == 1 else (year, month - 1),
        'next': (year + 1, 1) if month == 12 else (year, month + 1),
    }
