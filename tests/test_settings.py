DEBUG = True

SECRET_KEY = 'django-insecure-hfa@(@%94!!cp6n49v=1er-8hgzx73vlhqg2taz5dcrj-^1r3m'


# ======================
# Application definition
# ======================

INSTALLED_APPS = [
    'django.contrib.staticfiles',

    'django_secure_media',
]


# ========
# Database
# ========

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}


# ======================================
# Static files (CSS, JavaScript, Images)
# ======================================

STATIC_URL = 'static/'

MEDIA_URL = 'media/'
MEDIA_ROOT = 'media'
