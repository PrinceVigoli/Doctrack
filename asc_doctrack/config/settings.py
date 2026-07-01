from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_security_settings(django_env, raw_secret_key, raw_debug_env):
    """
    Pure function — validates the environment-supplied security settings and
    returns ``(secret_key: str, debug: bool)``, or raises
    ``ImproperlyConfigured`` if an unsafe combination is detected.

    Extracted from module-level code so the validation logic can be unit-
    tested without reloading the entire settings module (see config/tests.py).
    Called exactly once at module load time; do not call it anywhere else.

    Args:
        django_env:     Value of the DJANGO_ENV env var (default 'development').
        raw_secret_key: Value of the SECRET_KEY env var, or None / '' if unset.
        raw_debug_env:  Value of the DEBUG env var ('True'/'False'), or None.
    """
    is_production = django_env != 'development'

    if not raw_secret_key:
        if is_production:
            raise ImproperlyConfigured(
                "SECRET_KEY is not set. Refusing to start with an insecure "
                "default outside development. Generate one with "
                '`python -c "import secrets; print(secrets.token_hex(50))"` '
                "and set it in the environment (see .env.example)."
            )
        # Dev-only fallback — never reached when DJANGO_ENV != 'development'.
        secret_key = 'django-insecure-local-dev-only-do-not-use-in-production'
    else:
        secret_key = raw_secret_key

    if raw_debug_env is None:
        # Unset: default to the safe value for the environment.
        debug = not is_production
    else:
        debug = raw_debug_env == 'True'
        if is_production and debug:
            raise ImproperlyConfigured(
                "DEBUG=True is set but DJANGO_ENV is not 'development'. "
                "Running with DEBUG enabled outside development is not "
                "allowed — it exposes stack traces, settings, and SQL to "
                "visitors."
            )

    return secret_key, debug


# SECURITY: only 'development' falls back to convenience defaults; everything
# else must be fully configured or the server refuses to start. See the
# docstring of _resolve_security_settings() above.
DJANGO_ENV    = os.getenv('DJANGO_ENV', 'development')
IS_PRODUCTION = DJANGO_ENV != 'development'
SECRET_KEY, DEBUG = _resolve_security_settings(
    DJANGO_ENV,
    os.getenv('SECRET_KEY'),
    os.getenv('DEBUG'),
)
# In development, default to '*' so the server is reachable from a phone on
# the same LAN (e.g. http://192.168.1.7:8000) as well as localhost — Django
# still validates the Host header, so without this a request coming from a
# real device (which sends "192.168.x.x:8000" as Host, not "localhost") is
# rejected with "Invalid HTTP_HOST header" / DisallowedHost, even though the
# exact same backend works fine from a browser on the dev machine itself.
# Production must still explicitly set ALLOWED_HOSTS via the environment.
_allowed_hosts_default = '*' if not IS_PRODUCTION else ''
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', _allowed_hosts_default).split(',')
if IS_PRODUCTION and not os.getenv('ALLOWED_HOSTS'):
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS is not set. Refusing to start outside development "
        "without an explicit ALLOWED_HOSTS (see .env.example)."
    )

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'channels',
    # local
    'accounts',
    'documents',
    'tracking',
    'classifier',
    'dashboard',
    'notifications',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION  = 'config.asgi.application'

# PostgreSQL when DATABASE_URL is set; SQLite fallback for local dev
_db_url = os.getenv('DATABASE_URL', '')
if _db_url:
    import dj_database_url
    DATABASES = {'default': dj_database_url.parse(_db_url, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Manila'
USE_I18N      = True
USE_TZ        = True

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── DRF ───────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon':  '30/min',
        'user':  '300/min',
        'login': '10/min',   # applied per-view on /api/auth/login/
        'scan':  '10/min',   # applied per-view on /api/docs/scan/
    },
}

# ── JWT ───────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES':      ('Bearer',),
}

# ── CORS ──────────────────────────────────────────────────────────────────────
_cors_explicit = os.getenv('CORS_ALLOWED_ORIGINS', '')
if _cors_explicit:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_explicit.split(',') if o.strip()]
    CORS_ALLOW_ALL_ORIGINS = False
elif DEBUG and not IS_PRODUCTION:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:8081',
        'http://localhost:3000',
        f"http://{os.getenv('VPS_IP', 'localhost')}",
        f"https://{os.getenv('DOMAIN', 'localhost')}",
    ]
CORS_ALLOW_CREDENTIALS = True

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')

# ── Django Channels (WebSockets) ──────────────────────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts':    [REDIS_URL],
            'capacity': 1500,
            'expiry':   10,
        },
    },
}

# ── Celery (background tasks) ─────────────────────────────────────────────────
CELERY_BROKER_URL        = REDIS_URL
CELERY_RESULT_BACKEND    = REDIS_URL
CELERY_ACCEPT_CONTENT    = ['json']
CELERY_TASK_SERIALIZER   = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE          = TIME_ZONE
CELERY_TASK_MAX_RETRIES  = 3
CELERY_TASK_ACKS_LATE    = True

# ── Push Notifications ────────────────────────────────────────────────────────
EXPO_ACCESS_TOKEN = os.getenv('EXPO_ACCESS_TOKEN', '')

# FCM HTTP v1 API — requires a Firebase service account
FCM_PROJECT_ID            = os.getenv('FCM_PROJECT_ID', '')
FCM_SERVICE_ACCOUNT_JSON  = os.getenv('FCM_SERVICE_ACCOUNT_JSON', '')  # JSON string or file path

# ── HuggingFace AI (document scanner) ────────────────────────────────────────
HF_API_TOKEN  = os.getenv('HF_API_TOKEN', '')
HF_MODEL      = os.getenv('HF_MODEL', 'Qwen/Qwen2.5-VL-7B-Instruct')
AI_MODEL_PATH = BASE_DIR / 'classifier' / 'models'

# ── Local dev overrides (no Redis required) ───────────────────────────────────
import sys
if 'test' in sys.argv or not os.getenv('REDIS_URL'):
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

if not os.getenv('REDIS_URL'):
    CELERY_TASK_ALWAYS_EAGER     = True
    CELERY_TASK_EAGER_PROPAGATES = True   # surface task errors immediately in dev
    CELERY_BROKER_URL            = 'memory://'
    CELERY_RESULT_BACKEND        = 'cache+memory://'
    CELERY_TASK_STORE_EAGER_RESULT = True
