"""App configuration for the core module."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Django AppConfig for the core application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = "core"
