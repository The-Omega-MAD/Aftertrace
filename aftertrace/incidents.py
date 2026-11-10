from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def validate_incident(incident: dict[str, Any]) -> list[str]:
    """Return validation errors for an incident before it is analyzed or retained."""
    required_fields = {
        "incident_id": "Incident ID",
        "title": "Alert title",
        "entity": "Application / entity",
        "actor": "Actor context",
        "permission_change": "Permission event",
        "approval_context": "Approval context",
    }
    limits = {
        "incident_id": 100,
        "title": 300,
        "entity": 300,
        "actor": 500,
        "permission_change": 500,
        "approval_context": 500,
    }
    errors: list[str] = []
    for key, label in required_fields.items():
        value = incident.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label} is required.")
        elif len(value.strip()) > limits[key]:
            errors.append(f"{label} must be {limits[key]} characters or fewer.")

    if incident.get("severity") not in {"Low", "Medium", "High", "Critical"}:
        errors.append("Severity must be Low, Medium, High, or Critical.")

    timestamp = incident.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp.strip():
        errors.append("Timestamp is required.")
    else:
        try:
            parsed = datetime.fromisoformat(timestamp.strip().replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                errors.append("Timestamp must include a timezone, such as Z or +00:00.")
        except ValueError:
            errors.append("Timestamp must be a valid ISO 8601 date and time.")

    observations = incident.get("observations", [])
    if not isinstance(observations, list):
        errors.append("Observations must be a list of text values.")
    elif len(observations) > 50 or any(
        not isinstance(item, str) or len(item.strip()) > 1000 for item in observations
    ):
        errors.append("Use at most 50 observations, each 1,000 characters or fewer.")
    return errors


def normalize_incident(incident: dict[str, Any]) -> dict[str, Any]:
    """Trim text fields and normalize a valid timestamp to UTC ISO 8601."""
    normalized = dict(incident)
    for key in (
        "incident_id", "title", "entity", "actor", "permission_change",
        "approval_context", "severity", "analyst_finding", "lesson", "outcome",
    ):
        if isinstance(normalized.get(key), str):
            normalized[key] = normalized[key].strip()
    if isinstance(normalized.get("observations"), list):
        normalized["observations"] = [
            value.strip() for value in normalized["observations"]
            if isinstance(value, str) and value.strip()
        ]
    parsed = datetime.fromisoformat(normalized["timestamp"].strip().replace("Z", "+00:00"))
    normalized["timestamp"] = parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return normalized
