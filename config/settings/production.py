
import os

from .base import *


DEBUG = False

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY or SECRET_KEY.startswith(
    "replace-with-"
):
    raise RuntimeError(
        "Production requires a valid SECRET_KEY environment variable."
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

if not ALLOWED_HOSTS:
    raise RuntimeError(
        "Production requires ALLOWED_HOSTS to be configured."
    )

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]

if os.getenv("DB_ENGINE", "").lower() != "postgresql":
    raise RuntimeError(
        "Production requires DB_ENGINE=postgresql."
    )

# Require HTTPS in production. Configure the hosting platform
# to terminate HTTPS and forward the original protocol header.
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

# Enable HSTS after confirming HTTPS works on the deployed domain.
SECURE_HSTS_SECONDS = int(
    os.getenv("SECURE_HSTS_SECONDS", "0")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False")
    .lower() in ("true", "1", "yes")
)
SECURE_HSTS_PRELOAD = False

# Allow deployment hosts to supply their own persistent media path.
MEDIA_ROOT = os.getenv(
    "MEDIA_ROOT",
    str(BASE_DIR / "media"),
)

# Do not use SQLite as a production fallback.
if not DATABASES["default"]["ENGINE"].endswith("postgresql"):
    raise RuntimeError(
        "A PostgreSQL database is required in production."
    )
