"""
Настройки проекта коптильни.
Все чувствительные данные считываются из .env (python-dotenv).
"""
from pathlib import Path
import os

from dotenv import load_dotenv

# Загружаем переменные из .env (файл лежит рядом с manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


# ---------- Безопасность ----------
SECRET_KEY = os.getenv('SECRET_KEY', 'unsafe-default-key-change-me')

# В проде DEBUG=False; читаем из env, приводим к bool
DEBUG = os.getenv('DEBUG', 'False').lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
    if host.strip()
]

# Для POST-запросов по HTTPS в проде (за прокси/nginx) — включить:
CSRF_TRUSTED_ORIGINS = [
    f'https://{host}' for host in ALLOWED_HOSTS if host not in ('127.0.0.1', 'localhost')
]


# ---------- Приложения ----------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'shop',  # наше приложение
]

MIDDLEWARE = [
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
        'DIRS': [BASE_DIR / 'templates'],  # глобальные шаблоны
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


# ---------- База данных ----------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}


# ---------- Валидация паролей ----------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ---------- Локализация ----------
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True


# ---------- Статика и медиа ----------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'   # куда collectstatic сложит в проде

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'          # сюда грузятся картинки товаров


# ---------- Прочее ----------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------- VK Bot ----------
VK_BOT_TOKEN = os.getenv('VK_BOT_TOKEN', '')
VK_ADMIN_ID = int(os.getenv('VK_ADMIN_ID', '0'))
VK_API_VERSION = '5.199'
# ============================================================================
#  PRODUCTION-НАСТРОЙКИ (активны только при DEBUG=False)
# ============================================================================
if not DEBUG:
    # --- HTTPS и cookies ---
    SECURE_SSL_REDIRECT = True            # все HTTP → HTTPS
    SESSION_COOKIE_SECURE = True          # cookie сессии только по HTTPS
    CSRF_COOKIE_SECURE = True             # CSRF-cookie только по HTTPS
    SECURE_HSTS_SECONDS = 31536000        # HSTS на 1 год (только после успешного HTTPS!)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # --- Защита от MIME-sniffing и clickjacking ---
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True      # устаревшее, но безвредно
    X_FRAME_OPTIONS = 'DENY'

    # --- Работа за nginx/прокси ---
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # --- Куда редиректить при ошибках ---
    # (файлы 404.html / 500.html в templates/)
    # CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'  # по умолчанию


# ============================================================================
#  ЛОГИРОВАНИЕ (и в dev, и в prod)
# ============================================================================
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'shop.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        # Ошибки VK-бота (logger в shop/vk_notify.py)
        'shop': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Логи Django (ошибки вьюх)
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
