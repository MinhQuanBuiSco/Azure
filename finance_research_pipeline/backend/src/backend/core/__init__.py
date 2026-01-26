"""Core module containing configuration, dependencies, and logging."""

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger, setup_logging

__all__ = ["Settings", "get_settings", "get_logger", "setup_logging"]
