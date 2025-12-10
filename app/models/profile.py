"""
AlertProfile model - re-export for compatibility
"""
from app.models.alert import AlertProfile, Alert, AlertHistory

__all__ = ["AlertProfile", "Alert", "AlertHistory"]
