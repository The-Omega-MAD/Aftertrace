from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from hindsight_client import Hindsight


def get_client() -> Hindsight:
    api_key = os.getenv("HINDSIGHT_API_KEY", "").strip()
    base_url = os.getenv(
        "HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io"
    ).strip()
    if not api_key:
        raise RuntimeError("HINDSIGHT_API_KEY is missing. Add it to your .env file.")
    return Hindsight(base_url=base_url, api_key=api_key)


def get_bank_id() -> str:
    return os.getenv("HINDSIGHT_BANK_ID", "aftertrace-exordium").strip()


def ensure_bank(client: Hindsight, bank_id: str) -> None:
    """Create the AFTERTRACE memory bank if it does not already exist."""
    try:
        client.create_bank(
            bank_id=bank_id,
            name="AFTERTRACE | EXORDIUM",
            background=(
                "You are the memory layer for AFTERTRACE, a defensive incident "
                "continuity assistant. Preserve distinctions between observed "
                "facts, analyst findings, hypotheses, and unknowns. A past incident "
                "outcome must never be treated as proof about a new incident. "
                "Prefer cautious, evidence-grounded reasoning."
            ),
            disposition={"skepticism": 4, "literalism": 4, "empathy": 2},
        )
    except Exception as exc:
        # Existing banks may return a conflict. Other failures must remain visible.
        message = str(exc).lower()
        if not any(x in message for x in ("already exists", "409", "conflict")):
            raise


def incident_memory_text(incident: dict[str, Any]) -> str:
    return (
        "AFTERTRACE SYNTHETIC INCIDENT MEMORY\n"
        + json.dumps(incident, indent=2, ensure_ascii=False)
        + "\nThe outcome applies only to this incident. Do not transfer its "
          "disposition to a later incident without checking that event's evidence."
    )


def retain_incident(client: Hindsight, bank_id: str, incident: dict[str, Any]) -> None:
    client.retain(
        bank_id=bank_id,
        content=incident_memory_text(incident),
        context="AFTERTRACE incident investigation and analyst learning",
        metadata={
            "project": "AFTERTRACE",
            "incident_id": incident.get("incident_id", "unknown"),
            "synthetic": True,
            "record_type": "incident_investigation",
        },
        timestamp=(
            datetime.fromisoformat(incident["timestamp"].replace("Z", "+00:00"))
            if incident.get("timestamp") else None
        ),
    )


def recall_incidents(client: Hindsight, bank_id: str, incident: dict[str, Any]):
    query = (
        "Find prior investigations, analyst findings, lessons, and outcomes "
        "relevant to this new incident. Identify similarities and warnings "
        "against reusing an old disposition blindly. Current incident: "
        + json.dumps(incident, ensure_ascii=False)
    )
    return client.recall(bank_id=bank_id, query=query, budget="mid")


def reflect_on_incident(client: Hindsight, bank_id: str, incident: dict[str, Any]):
    query = f"""
You are AFTERTRACE, a defensive incident-continuity assistant.

CURRENT SYNTHETIC INCIDENT:
{json.dumps(incident, indent=2, ensure_ascii=False)}

Use relevant prior investigation memories. Produce these sections:
1. Historical context: what relevant prior investigation was recalled?
2. Matches: what is genuinely shared?
3. Evidence delta: what is materially different in the current event?
4. Unknowns: what has not been verified?
5. Next checks: evidence-gathering questions for a human analyst.
6. Caution: why a prior outcome does not automatically determine this incident.

Rules:
- Separate historical facts from current observations.
- Do not invent telemetry, actors, permissions, or outcomes.
- Do not declare the current incident benign or malicious without sufficient evidence.
- Do not recommend automated containment or remediation.
- If no relevant memory exists, say so explicitly.
"""
    return client.reflect(bank_id=bank_id, query=query, budget="mid")


def evidence_delta(previous: dict[str, Any], current: dict[str, Any]):
    fields = [
        ("entity", "Application / entity"),
        ("actor", "Actor context"),
        ("permission_change", "Permission event"),
        ("approval_context", "Approval context"),
    ]
    return [
        {
            "dimension": label,
            "previous": str(previous.get(key, "Not recorded")),
            "current": str(current.get(key, "Not recorded")),
            "status": (
                "Same" if previous.get(key) == current.get(key) else "Changed"
            ),
        }
        for key, label in fields
    ]
