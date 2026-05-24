from __future__ import annotations


def get_ha_user() -> str:
    """Standalone app is single-user; always returns 'default'."""
    return "default"
