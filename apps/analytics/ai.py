"""Backend AI Coach: studies a user's trade history against the rules of
their validated strategy (Donchian breakout + ADX filter + ATR trailing
stop + partial exit at 1.5R — see the Pine Script strategy this journal was
built around) and returns concrete, data-driven recommendations.

Design principle carried over from that strategy's own validation notes:
never state a strong claim from a small sample. Every insight below is
tagged with a confidence level derived from its sample size, and anything
under MIN_SAMPLE is simply not raised as an insight at all.
"""
from collections import Counter, defaultdict

from apps.trades.models import Trade

MIN_SAMPLE = 5          # below this, a segment is not flagged as an insight
STRATEGY_PARTIAL_R = 1.5  # the validated partial-exit target, in R, from the Pine strategy


def _confidence(n):
    if n < 10:
        return 'faible'
    if n < 30:
        return 'moyenne'
    return 'élevée'


def _net(t):
    return float(t.net_result)


def _winrate_pf(trades):
    results = [_net(t) for t in trades]
    n = len(results)
    if n == 0:
        return 0.0, 0.0
    wins = [r for r in results if r > 0]
    losses = [r for r in results if r <= 0]
    winrate = len(wins) / n * 100
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    pf = (gross_profit / gross_loss) if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)
    return winrate, pf


def _segment_insights(trades, field, label):
    groups = defaultdict(list)
    for t in trades:
        key = getattr(t, field)
        if key:
            groups[key].append(t)

    insights = []
    scored = []
    for key, ts in groups.items():
        if len(ts) < MIN_SAMPLE:
            continue
        winrate, pf = _winrate_pf(ts)
        scored.append((key, len(ts), winrate, pf))

    if not scored:
        return insights

    scored.sort(key=lambda x: x[2])
    worst = scored[0]
    best = scored[-1]

    if worst[2] < 40 and worst[1] >= MIN_SAMPLE:
        insights.append({
            'type': 'warning',
            'title': f'{label} sous-performante : {worst[0]}',
            'message': (
                f"Winrate de {worst[2]:.0f}% sur {worst[1]} trades (profit factor "
                f"{worst[3]:.2f}). Envisagez de réduire l'exposition ou de resserrer les "
                f"critères d'entrée sur ce segment."
            ),
            'confidence': _confidence(worst[1]),
            'sample_size': worst[1],
        })

    if best[2] > 60 and best[1] >= MIN_SAMPLE and best[0] != worst[0]:
        insights.append({
            'type': 'success',
            'title': f'{label} performante : {best[0]}',
            'message': (
                f"Winrate de {best[2]:.0f}% sur {best[1]} trades (profit factor "
                f"{best[3]:.2f}). C'est votre point fort actuel — envisagez d'y allouer "
                f"davantage de capital/risque."
            ),
            'confidence': _confidence(best[1]),
            'sample_size': best[1],
        })
    return insights


def _discipline_insight(trades):
    respected = [t for t in trades if t.respect_plan]
    ignored = [t for t in trades if not t.respect_plan]
    if len(respected) < MIN_SAMPLE or len(ignored) < MIN_SAMPLE:
        return None

    wr_ok, pf_ok = _winrate_pf(respected)
    wr_no, pf_no = _winrate_pf(ignored)
    avg_ok = sum(_net(t) for t in respected) / len(respected)
    avg_no = sum(_net(t) for t in ignored) / len(ignored)
    gap = avg_ok - avg_no
    n = min(len(respected), len(ignored))

    if gap > 0:
        return {
            'type': 'danger' if avg_no < 0 <= avg_ok else 'warning',
            'title': 'La discipline paie',
            'message': (
                f"Quand vous respectez le plan : winrate {wr_ok:.0f}%, PF {pf_ok:.2f}, "
                f"résultat moyen {avg_ok:+.2f}. Quand vous vous en écartez : winrate "
                f"{wr_no:.0f}%, PF {pf_no:.2f}, résultat moyen {avg_no:+.2f}. Chaque écart "
                f"au plan vous coûte en moyenne {gap:.2f} par trade."
            ),
            'confidence': _confidence(n),
            'sample_size': len(respected) + len(ignored),
        }
    return None


def _mood_insight(trades):
    groups = defaultdict(list)
    for t in trades:
        if t.humeur_avant:
            groups[t.humeur_avant].append(_net(t))

    scored = [(mood, len(rs), sum(rs) / len(rs)) for mood, rs in groups.items() if len(rs) >= MIN_SAMPLE]
    if len(scored) < 2:
        return None

    scored.sort(key=lambda x: x[2])
    worst_mood, worst_n, worst_avg = scored[0]
    best_mood, best_n, best_avg = scored[-1]
    if worst_avg >= best_avg:
        return None

    if worst_avg < 0 and best_avg > 0:
        severity = 'danger'
    elif (best_avg - worst_avg) > 0:
        severity = 'info'
    else:
        return None

    return {
        'type': severity,
        'title': "L'état émotionnel influence vos résultats",
        'message': (
            f"Trades pris en étant \"{best_mood}\" : résultat moyen {best_avg:+.2f} "
            f"(n={best_n}). Trades pris en étant \"{worst_mood}\" : résultat moyen "
            f"{worst_avg:+.2f} (n={worst_n}). Évitez de trader dans l'état \"{worst_mood}\"."
        ),
        'confidence': _confidence(min(worst_n, best_n)),
        'sample_size': worst_n + best_n,
    }


def _rr_insight(trades):
    with_stop = [t for t in trades if t.stop_loss]
    wins_with_stop = [t for t in with_stop if t.is_win]
    if len(wins_with_stop) < MIN_SAMPLE:
        return None

    reached_partial = sum(
        1 for t in wins_with_stop
        if t.risk_reward_achieved is not None and t.risk_reward_achieved >= STRATEGY_PARTIAL_R * 0.9
    )
    ratio = reached_partial / len(wins_with_stop) * 100

    if ratio < 40:
        return {
            'type': 'warning',
            'title': 'Sorties probablement trop précoces',
            'message': (
                f"Seulement {ratio:.0f}% de vos trades gagnants (avec SL renseigné) "
                f"atteignent ~{STRATEGY_PARTIAL_R}R, l'objectif de sortie partielle validé "
                f"de votre stratégie. Vous coupez peut-être vos gagnants trop tôt — "
                f"envisagez de laisser courir jusqu'au trailing stop plutôt que de sortir "
                f"manuellement."
            ),
            'confidence': _confidence(len(wins_with_stop)),
            'sample_size': len(wins_with_stop),
        }
    return None


def _losing_streak_insight(trades):
    chronological = sorted(trades, key=lambda t: t.date_ouverture)
    best_streak, current_streak = [], []
    for t in chronological:
        if not t.is_win:
            current_streak.append(t)
            if len(current_streak) > len(best_streak):
                best_streak = list(current_streak)
        else:
            current_streak = []

    if len(best_streak) < 3:
        return None

    pairs = Counter(t.paire for t in best_streak)
    sessions = Counter(t.session for t in best_streak if t.session)
    common_pair, pair_n = pairs.most_common(1)[0]
    note = ''
    if pair_n == len(best_streak):
        note = f" Toutes concernaient la paire {common_pair}."
    elif sessions:
        common_session, session_n = sessions.most_common(1)[0]
        if session_n == len(best_streak):
            note = f" Toutes ont eu lieu pendant la session {common_session}."

    return {
        'type': 'info',
        'title': f'Plus longue série de pertes : {len(best_streak)} trades',
        'message': f"Détectée entre le {best_streak[0].date_ouverture:%d/%m/%y} et le {best_streak[-1].date_ouverture:%d/%m/%y}.{note}",
        'confidence': 'élevée',
        'sample_size': len(best_streak),
    }


def _expectancy_trend_insight(trades):
    chronological = sorted(trades, key=lambda t: t.date_ouverture)
    n = len(chronological)
    if n < 10:
        return None
    mid = n // 2
    first_half = chronological[:mid]
    second_half = chronological[mid:]
    avg_first = sum(_net(t) for t in first_half) / len(first_half)
    avg_second = sum(_net(t) for t in second_half) / len(second_half)
    delta = avg_second - avg_first

    if abs(delta) < 0.01:
        return None

    return {
        'type': 'success' if delta > 0 else 'warning',
        'title': 'Tendance de performance ' + ('en amélioration' if delta > 0 else 'en dégradation'),
        'message': (
            f"Résultat moyen par trade : {avg_first:+.2f} sur la première moitié de "
            f"l'historique, {avg_second:+.2f} sur la seconde (n={n})."
        ),
        'confidence': _confidence(n),
        'sample_size': n,
    }


def _ml_model(trades):
    """The self-improving layer: a logistic regression re-trained from scratch
    on ALL of the user's trades every time this runs (there is no stale saved
    model — each analysis reflects every trade recorded so far). Only
    activates with >=30 trades and only if scikit-learn is installed;
    otherwise the rule-based insights above stand on their own.

    Returns both the feature-importance insight AND a cross-validated
    accuracy figure benchmarked against the naive "always predict the
    majority class" baseline — that accuracy gap is the honest, checkable
    signal that the model is learning something real from the data, and it
    is recomputed (and can improve) every time you add trades."""
    if len(trades) < 30:
        return None
    try:
        from sklearn.feature_extraction import DictVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import StratifiedKFold, cross_val_score
    except ImportError:
        return None

    rows, targets = [], []
    for t in trades:
        rows.append({
            'paire': t.paire,
            'session': t.session or 'inconnue',
            'jour_semaine': t.date_ouverture.strftime('%A'),
            'respect_plan': str(t.respect_plan),
            'humeur_avant': t.humeur_avant or 'inconnue',
        })
        targets.append(1 if t.is_win else 0)

    if len(set(targets)) < 2:
        return None  # can't fit a classifier on a single outcome class

    vec = DictVectorizer(sparse=False)
    X = vec.fit_transform(rows)
    model = LogisticRegression(max_iter=1000)
    model.fit(X, targets)

    coefs = list(zip(vec.get_feature_names_out(), model.coef_[0]))
    coefs.sort(key=lambda x: -abs(x[1]))
    top = coefs[:5]

    lines = []
    for name, weight in top:
        direction = 'associé à plus de gains' if weight > 0 else 'associé à plus de pertes'
        lines.append(f"{name.replace('=', ': ')} → {direction} (poids {weight:+.2f})")

    insight = {
        'type': 'info',
        'title': 'Analyse par régression logistique (facteurs les plus influents)',
        'message': ' | '.join(lines),
        'confidence': _confidence(len(trades)),
        'sample_size': len(trades),
    }

    accuracy = None
    baseline_accuracy = round(max(targets.count(0), targets.count(1)) / len(targets) * 100, 1)
    min_class_count = min(targets.count(0), targets.count(1))
    n_splits = min(5, min_class_count)
    if n_splits >= 2:
        try:
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            scores = cross_val_score(LogisticRegression(max_iter=1000), X, targets, cv=cv)
            accuracy = round(scores.mean() * 100, 1)
        except ValueError:
            accuracy = None

    return {
        'insight': insight,
        'accuracy': accuracy,
        'baseline_accuracy': baseline_accuracy,
        'n_splits': n_splits if accuracy is not None else 0,
    }


def generate_ai_insights(user):
    trades = list(Trade.objects.filter(user=user))
    n = len(trades)

    if n == 0:
        return {
            'insights': [{
                'type': 'info',
                'title': 'Pas encore de données',
                'message': "Ajoutez vos premiers trades pour que le coach IA puisse analyser votre stratégie.",
                'confidence': 'faible',
                'sample_size': 0,
            }],
            'data_points': 0,
            'model_used': 'aucun',
            'model_accuracy': None,
            'model_baseline': None,
            'trades_until_ml': 30,
        }

    insights = []
    insights += _segment_insights(trades, 'paire', 'Paire')
    insights += _segment_insights(trades, 'strategie', 'Stratégie')
    insights += _segment_insights(trades, 'session', 'Session')

    for fn in (_discipline_insight, _mood_insight, _rr_insight, _losing_streak_insight, _expectancy_trend_insight):
        result = fn(trades)
        if result:
            insights.append(result)

    ml = _ml_model(trades)
    model_used = 'règles statistiques'
    model_accuracy = None
    model_baseline = None
    if ml:
        insights.append(ml['insight'])
        model_used = 'règles statistiques + régression logistique (ré-entraînée à chaque analyse)'
        model_accuracy = ml['accuracy']
        model_baseline = ml['baseline_accuracy']

    if not insights:
        insights.append({
            'type': 'info',
            'title': 'Pas encore assez de données pour des recommandations fiables',
            'message': (
                f"{n} trade(s) enregistré(s). Le coach a besoin d'au moins {MIN_SAMPLE} "
                "trades par segment (paire, stratégie, session...) pour émettre une "
                "recommandation statistiquement défendable."
            ),
            'confidence': 'faible',
            'sample_size': n,
        })

    severity_order = {'danger': 0, 'warning': 1, 'success': 2, 'info': 3}
    insights.sort(key=lambda i: severity_order.get(i['type'], 4))

    return {
        'insights': insights,
        'data_points': n,
        'model_used': model_used,
        'model_accuracy': model_accuracy,
        'model_baseline': model_baseline,
        'trades_until_ml': max(0, 30 - n) if not ml else 0,
    }
