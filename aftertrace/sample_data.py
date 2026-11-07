FIRST_INCIDENT = {
    "incident_id": "AT-001",
    "title": "OAuth application permission review",
    "timestamp": "2026-11-01T09:00:00Z",
    "severity": "Medium",
    "entity": "Northstar Calendar Connector",
    "actor": "Approved integration service principal",
    "permission_change": "No new permission grant recorded",
    "approval_context": "Verified as an approved integration in this investigation",
    "observations": [
        "Application appeared in a synthetic identity audit event.",
        "The application was verified as an approved integration for this case.",
        "No new permission grant was recorded in this event."
    ],
    "analyst_finding": "Approved integration in this specific investigation.",
    "lesson": "Approval in one investigation does not establish that future permission changes are safe.",
    "outcome": "Resolved after review"
}

FOLLOWUP_INCIDENT = {
    "incident_id": "AT-002",
    "title": "OAuth application permission change",
    "timestamp": "2026-11-04T14:35:00Z",
    "severity": "High",
    "entity": "Northstar Calendar Connector",
    "actor": "Unverified actor context",
    "permission_change": "New permission change observed",
    "approval_context": "Not yet verified for this event",
    "observations": [
        "The same application identifier appears in a new synthetic identity audit event.",
        "A permission change is present in the current event.",
        "The actor context has not yet been verified.",
        "The previous investigation's approval does not cover this new event."
    ],
    "analyst_finding": "",
    "lesson": "",
    "outcome": "Undetermined"
}
