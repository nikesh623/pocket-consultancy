
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env", override=True)

from .base import *  # noqa: E402, F403


DEBUG = os.getenv("DEBUG", "True").lower() in (
    "true",
    "1",
    "yes",
)

if not DEBUG:
    raise RuntimeError(
        "Development settings require DEBUG=True. "
        "Use production settings for deployment."
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if host.strip()
]

if not ALLOWED_HOSTS:
    raise RuntimeError(
        "Configure ALLOWED_HOSTS in your local environment."
    )
