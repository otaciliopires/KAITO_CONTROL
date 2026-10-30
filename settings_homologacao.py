"""Isolated field testing under /homologacao/. Never imports production data."""
from kaito_fuel.settings import *
from decouple import config

AMBIENTE_HOMOLOGACAO = True
DEBUG = False
FORCE_SCRIPT_NAME = '/homologacao'
ALLOWED_HOSTS = [config('HOMOLOG_HOST', default='www.kaitocs.com.br'), '127.0.0.1', 'localhost']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'dados-homologacao' / 'db.sqlite3'}}
STATIC_URL = '/homologacao/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles-homologacao'
MEDIA_URL = '/homologacao/media/'
MEDIA_ROOT = BASE_DIR / 'dados-homologacao' / 'media'
SESSION_COOKIE_NAME = 'kaito_homolog_sessionid'
CSRF_COOKIE_NAME = 'kaito_homolog_csrftoken'
SESSION_COOKIE_PATH = CSRF_COOKIE_PATH = '/homologacao/'
SESSION_COOKIE_DOMAIN = CSRF_COOKIE_DOMAIN = None
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ROOT_URLCONF = 'urls_homologacao'
MIDDLEWARE = ['homologacao.IsolamentoHomologacaoMiddleware'] + MIDDLEWARE
