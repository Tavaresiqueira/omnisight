import os
from pathlib import Path

import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-development-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "identity",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "identity.privacy.PrivateApiCacheMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH", BASE_DIR / "db.sqlite3"),
    }
}
if os.environ.get("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.parse(
        os.environ["DATABASE_URL"], conn_max_age=600, conn_health_checks=True
    )

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "identity.User"

REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": ["identity.abuse.ApiBudgetThrottle"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

TRUST_PROXY_CLIENT_IP = os.environ.get('TRUST_PROXY_CLIENT_IP', 'false').lower() == 'true'
AUTH_RATE_LIMITS = {'login': (10, 60), 'register': (5, 3600), 'demo': (10, 60)}
AUTH_RATE_LIMITS['closure'] = (10, 60)
SCAN_RATE_LIMITS = {'user': 10, 'organization': 30, 'domain': 5, 'ip': 30}
SCAN_ACTIVE_ORGANIZATION_LIMIT = 3
SCAN_ACTIVE_GLOBAL_LIMIT = 10
SCAN_RETENTION_DAYS = int(os.environ.get('SCAN_RETENTION_DAYS', '30'))
ABUSE_RETENTION_DAYS = int(os.environ.get('ABUSE_RETENTION_DAYS', '7'))
DELETION_LEDGER_PATH = os.environ.get('DELETION_LEDGER_PATH', '')
DELETION_LEDGER_KEY = os.environ.get('DELETION_LEDGER_KEY', '')
if not 1 <= SCAN_RETENTION_DAYS <= 3650 or not 1 <= ABUSE_RETENTION_DAYS <= 365:
    raise ValueError('Configure retenção de scans entre 1 e 3650 dias e contadores entre 1 e 365 dias.')

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# Health is used only by the private container network / load balancer.
SECURE_REDIRECT_EXEMPT = [r"^api/health/$"]
DEMO_LOGIN_ENABLED = os.environ.get('DEMO_LOGIN_ENABLED', str(DEBUG)).lower() == 'true'
if not DEBUG and (SECRET_KEY == 'unsafe-development-key' or len(SECRET_KEY) < 50):
    raise ValueError('Defina DJANGO_SECRET_KEY de produção com pelo menos 50 caracteres.')
