"""
User Settings Service (Phase 64)
Manages user preferences, notification settings, and UI configuration.
"""

import json
from datetime import datetime
from typing import Any


class UserSettingsService:
    """Manages user settings and preferences."""

    def __init__(self) -> None:
        self._settings: dict[str, Any] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default user settings."""
        self._settings = {
            "profile": {
                "display_name": "Julie Admin",
                "email": "admin@juliecpa.com",
                "timezone": "America/Los_Angeles",
                "language": "en-US",
                "avatar_url": None,
            },
            "notifications": {
                "email_enabled": True,
                "push_enabled": False,
                "alert_threshold": "warning",  # critical, warning, info
                "daily_digest": True,
                "weekly_report": True,
                "tax_deadline_reminders": True,
                "document_updates": True,
                "system_alerts": True,
            },
            "dashboard": {
                "theme": "dark",
                "accent_color": "#3b82f6",
                "sidebar_collapsed": False,
                "default_tab": "dashboard",
                "show_tutorial": False,
                "compact_mode": False,
                "auto_refresh": True,
                "refresh_interval": 30,  # seconds
            },
            "tax": {
                "filing_status": "single",
                "state": "CA",
                "default_income_type": "business",
                "show_quarterly_estimates": True,
                "auto_calculate_qbi": True,
            },
            "security": {
                "two_factor_enabled": False,
                "session_timeout": 30,  # minutes
                "login_notifications": True,
                "api_key_created": datetime.now().isoformat(),
            },
            "integrations": {
                "quickbooks_connected": False,
                "google_drive_connected": True,
                "notebooklm_connected": True,
                "calendar_sync": False,
            },
            "updated_at": datetime.now().isoformat(),
        }

    def get_all_settings(self) -> dict[str, Any]:
        """Get all user settings."""
        return self._settings

    def get_section(self, section: str) -> dict[str, Any] | None:
        """Get a specific settings section."""
        return self._settings.get(section)

    def update_section(self, section: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update a settings section."""
        if section not in self._settings:
            return {"error": f"Unknown section: {section}"}

        # Merge updates
        if isinstance(self._settings[section], dict):
            self._settings[section].update(updates)
        else:
            self._settings[section] = updates

        self._settings["updated_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "section": section,
            "settings": self._settings[section],
            "updated_at": self._settings["updated_at"],
        }

    def update_setting(self, section: str, key: str, value: Any) -> dict[str, Any]:
        """Update a single setting."""
        if section not in self._settings:
            return {"error": f"Unknown section: {section}"}

        if not isinstance(self._settings[section], dict):
            return {"error": f"Section {section} is not a dictionary"}

        self._settings[section][key] = value
        self._settings["updated_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "section": section,
            "key": key,
            "value": value,
            "updated_at": self._settings["updated_at"],
        }

    def get_notification_settings(self) -> dict[str, Any]:
        """Get notification-specific settings."""
        return {
            "notifications": self._settings.get("notifications", {}),
            "alert_levels": ["critical", "warning", "info"],
            "channels": {
                "email": self._settings["notifications"].get("email_enabled", False),
                "push": self._settings["notifications"].get("push_enabled", False),
            },
        }

    def toggle_notification(self, notification_type: str, enabled: bool) -> dict[str, Any]:
        """Toggle a specific notification type."""
        if "notifications" not in self._settings:
            return {"error": "Notifications section not found"}

        if notification_type not in self._settings["notifications"]:
            return {"error": f"Unknown notification type: {notification_type}"}

        self._settings["notifications"][notification_type] = enabled
        self._settings["updated_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "notification_type": notification_type,
            "enabled": enabled,
        }

    def get_theme_settings(self) -> dict[str, Any]:
        """Get dashboard theme settings."""
        dashboard = self._settings.get("dashboard", {})
        return {
            "theme": dashboard.get("theme", "dark"),
            "accent_color": dashboard.get("accent_color", "#3b82f6"),
            "compact_mode": dashboard.get("compact_mode", False),
            "available_themes": ["dark", "light", "system"],
            "available_colors": [
                {"name": "Blue", "value": "#3b82f6"},
                {"name": "Purple", "value": "#8b5cf6"},
                {"name": "Green", "value": "#10b981"},
                {"name": "Orange", "value": "#f59e0b"},
                {"name": "Red", "value": "#ef4444"},
            ],
        }

    def export_settings(self) -> str:
        """Export settings as JSON string."""
        return json.dumps(self._settings, indent=2, default=str)

    def get_settings_summary(self) -> dict[str, Any]:
        """Get a summary of current settings."""
        return {
            "profile": {
                "name": self._settings["profile"].get("display_name"),
                "email": self._settings["profile"].get("email"),
            },
            "theme": self._settings["dashboard"].get("theme"),
            "notifications_enabled": self._settings["notifications"].get("email_enabled"),
            "two_factor": self._settings["security"].get("two_factor_enabled"),
            "integrations_count": sum(
                1 for v in self._settings["integrations"].values() if v is True
            ),
            "last_updated": self._settings.get("updated_at"),
        }


# Singleton instance
_settings_service: UserSettingsService | None = None


def get_settings_service() -> UserSettingsService:
    """Get or create the settings service singleton."""
    global _settings_service
    if _settings_service is None:
        _settings_service = UserSettingsService()
    return _settings_service
