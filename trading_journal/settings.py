"""
Django settings for trading_journal project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# In production, set the DJANGO_SECRET_KEY environment variable instead.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-q&791^a0($m=rl7q3a-*$kjb@&*u4s*7lcp0k=w!)24blya90h',
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Behind Orbit/Flux's reverse proxy, TLS is terminated upstream and the
# request reaches Django as plain HTTP with an X-Forwarded-Proto header —
# without this Django would think every request is insecure (breaks CSRF
# and secure cookies) even though the browser sees HTTPS.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Extra origins allowed to submit cross-site POSTs (needed once the app is
# reachable at a real https:// domain — set to e.g.
# "https://your-app.runonflux.io" via env var). Empty by default so local
# dev over plain http:// is unaffected.
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'apps.core',
    'apps.accounts',
    'apps.trades',
    'apps.dashboard',
    'apps.analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'trading_journal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.user_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'trading_journal.wsgi.application'


# Database
# Defaults to SQLite. Set a DATABASE_URL env var (e.g. postgres://...) to
# switch to a managed database in production — recommended on a
# single-instance free-tier host, where the local disk (and any SQLite file
# on it) is not guaranteed to survive a redeploy.
if os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES = {'default': dj_database_url.parse(os.environ['DATABASE_URL'])}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise serves static files directly from the app process — no need
# for a separate nginx/CDN in front of a single-instance deployment.
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# Media files (screenshots uploaded by users)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth redirects
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Email — console backend in dev (password reset emails print to the runserver console)
EMAIL_BACKEND = os.environ.get(
    'DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend'
)

# Max upload size for trade screenshots (5 MB)
MAX_SCREENSHOT_SIZE = 5 * 1024 * 1024

# Harden automatically once DEBUG is off (i.e. DJANGO_DEBUG=False in the
# deployment's environment variables) — nothing to remember to flip by hand.
#
# SECURE_SSL_REDIRECT is deliberately left off: it redirects any request
# Django itself doesn't see as HTTPS (via SECURE_PROXY_SSL_HEADER) to
# https://<same URL>. On a reverse proxy that doesn't consistently forward
# X-Forwarded-Proto, that redirect target looks exactly like the original
# request, and the browser loops forever. The proxy in front of this app
# already terminates TLS, so Django doesn't need to redirect for it.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
