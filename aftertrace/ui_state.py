from typing import Any


def invalidate_incident_results(session_state: Any) -> None:
    """Clear cached UI results after incident inputs are submitted."""
    session_state.analysis = None
    session_state.baseline = None
    session_state.last_retained_incident = None
    session_state.last_hindsight_retain_response = None
