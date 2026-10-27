
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing. Configure it in your environment."
    )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()

if DB_ENGINE == "postgresql":
    import dj_database_url

    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

    if DATABASE_URL:
        DATABASES = {
            "default": dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=60,
                ssl_require=True,
            )
        }
    else:
        # Keep support for separate database environment variables.
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.getenv("DB_NAME", "pocket_consultancy"),
                "USER": os.getenv("DB_USER", "postgres"),
                "PASSWORD": os.getenv("DB_PASSWORD", ""),
                "HOST": os.getenv("DB_HOST", "127.0.0.1"),
                "PORT": os.getenv("DB_PORT", "5432"),
                "CONN_MAX_AGE": 60,
                "OPTIONS": {"sslmode": "require"},
            }
        }

elif DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

else:
    raise RuntimeError(
        "DB_ENGINE must be either 'sqlite' or 'postgresql'."
    )


AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "core:home"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
