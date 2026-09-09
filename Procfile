web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn trading_journal.wsgi --bind 0.0.0.0:$PORT
