from django import template

register = template.Library()

SYMBOLS = {'EUR': '€', 'USD': '$', 'GBP': '£', 'JPY': '¥'}


@register.filter
def money(value, currency='EUR'):
    """Format a number as a signed, thousand-separated money string with the right symbol."""
    if value is None:
        value = 0
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    symbol = SYMBOLS.get(currency, currency)
    sign = '+' if value > 0 else ''
    formatted = f"{value:,.2f}".replace(',', ' ').replace('.', ',')
    return f"{sign}{formatted} {symbol}"


@register.filter
def pct(value):
    if value is None:
        return '0%'
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    sign = '+' if value > 0 else ''
    return f"{sign}{value:.1f}%"


@register.filter
def get_item(d, key):
    if not d:
        return None
    return d.get(key)
