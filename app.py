from html import escape

import streamlit as st
from dotenv import load_dotenv

from aftertrace.engine import (
    ensure_bank, evidence_delta, get_bank_id, get_client,
    recalled_incident_records, recall_incidents, reflect_on_incident,
    retain_incident,
)
from aftertrace.incidents import normalize_incident, validate_incident
from aftertrace.sample_data import FIRST_INCIDENT, FOLLOWUP_INCIDENT
from aftertrace.ui_state import invalidate_incident_results


load_dotenv()
st.set_page_config(page_title="AFTERTRACE | Incident Continuity", page_icon="◈", layout="wide")

st.markdown("""
<style>
.stApp { background:#0a0f18; }
section[data-testid="stSidebar"] { background:#101827; }
.hero { padding:1.5rem 1.7rem; border:1px solid #26364c; border-radius:18px;
background:linear-gradient(120deg,#101d2e,#111827 65%,#172238); margin-bottom:1.2rem; }
.eyebrow { color:#78d9c5; letter-spacing:.16em; font-size:.72rem; font-weight:700; }
.hero h1 { color:#f4f7fb; font-size:2.65rem; margin:.25rem 0; letter-spacing:-.04em; }
.hero p { color:#a9b8ca; max-width:760px; }
.panel { background:#111a28; border:1px solid #27374d; border-radius:14px; padding:1rem 1.1rem; }
.metric { color:#8fa4bc; font-size:.8rem; }
.value { color:#f5f7fa; font-size:1.15rem; font-weight:650; }
.evidence-delta { width:100%; border-collapse:collapse; color:#dbe6f0; }
.evidence-delta th { text-align:left; color:#78d9c5; font-size:.8rem; padding:.7rem; border-bottom:1px solid #27374d; }
.evidence-delta td { text-align:left; padding:.75rem .7rem; border-bottom:1px solid #27374d; vertical-align:top; }
.evidence-delta tr:last-child td { border-bottom:0; }
.evidence-status { font-weight:700; white-space:nowrap; }
.evidence-status.same { color:#78d9c5; }
.evidence-status.changed { color:#f2c879; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">EXORDIUM PRESENTS</div>
  <h1>AFTERTRACE <span style="color:#78d9c5">◈</span></h1>
  <p><b>Past incidents are context. They are not verdicts.</b><br>
  Persistent incident memory, evidence comparison, and human-led investigation continuity.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ◈ AFTERTRACE")
    st.caption("Incident continuity workspace")
    st.markdown("---")
    st.markdown("**Memory lifecycle**")
    st.markdown("1. Retain an investigation\n2. Recall relevant history\n3. Reflect on new evidence\n4. Retain analyst feedback")
    st.markdown("---")
    st.caption("Synthetic identity-security incidents only. No production systems connected.")

if "client" not in st.session_state:
    st.session_state.client = None
if "ready" not in st.session_state:
    st.session_state.ready = False
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "baseline" not in st.session_state:
    st.session_state.baseline = None
if "incident" not in st.session_state:
    st.session_state.incident = dict(FOLLOWUP_INCIDENT)
if "last_retained_incident" not in st.session_state:
    st.session_state.last_retained_incident = None
if "last_hindsight_retain_response" not in st.session_state:
    st.session_state.last_hindsight_retain_response = None


def evidence_delta_markup(rows):
    """Render the compact Evidence Delta without Streamlit's Arrow data path."""
    body = []
    for row in rows:
        status = str(row.get("status", ""))
        status_class = "same" if status == "Same" else "changed"
        body.append(
            "<tr>"
            f"<td>{escape(str(row.get('dimension', '')))}</td>"
            f"<td>{escape(str(row.get('previous', '')))}</td>"
            f"<td>{escape(str(row.get('current', '')))}</td>"
            f"<td><span class=\"evidence-status {status_class}\">{escape(status)}</span></td>"
            "</tr>"
        )
    return (
        '<div class="panel"><table class="evidence-delta">'
        "<thead><tr><th>Dimension</th><th>Previous</th><th>Current</th><th>Status</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table></div>"
    )

a, b = st.columns([1, 3])
with a:
    if st.button("Connect Hindsight", type="primary", use_container_width=True):
        try:
            client = get_client()
            ensure_bank(client, get_bank_id())
            st.session_state.client = client
            st.session_state.ready = True
            st.success("Hindsight connected.")
        except Exception as exc:
            st.session_state.ready = False
            st.error(f"Connection failed: {exc}")
with b:
    status = "CONNECTED" if st.session_state.ready else "NOT CONNECTED"
    st.markdown(
        f'<div class="panel"><span class="metric">MEMORY STATUS</span><br>'
        f'<span class="value">{status}</span><br>'
        '<span class="metric">Configure your .env file, then connect to enable live memory operations.</span></div>',
        unsafe_allow_html=True,
    )

st.markdown("### 01 / Retain the first investigation")
st.write("Seed the historical case. This stores the finding and the lesson that an old approval must not be reused as a new verdict.")
with st.expander("Preview historical incident · AT-001"):
    st.json(FIRST_INCIDENT)

if st.button("Seed first investigation into Hindsight", use_container_width=True):
    if not st.session_state.ready:
        st.warning("Connect Hindsight first.")
    else:
        try:
            retain_incident(st.session_state.client, get_bank_id(), FIRST_INCIDENT)
            st.success("AT-001 retained in Hindsight.")
        except Exception as exc:
            st.error(f"Retain failed: {exc}")

st.markdown("---")
st.markdown("### 02 / A related alert arrives")
st.write("Same application. New event. The analyst must re-check the evidence.")

with st.form("incident_form"):
    left, right = st.columns(2)
    with left:
        incident_id = st.text_input("Incident ID", st.session_state.incident["incident_id"])
        title = st.text_input("Alert title", st.session_state.incident["title"])
        entity = st.text_input("Application / entity", st.session_state.incident["entity"])
        actor = st.text_input("Actor context", st.session_state.incident["actor"])
    with right:
        timestamp = st.text_input(
            "Event timestamp (ISO 8601)", st.session_state.incident["timestamp"]
        )
        severities = ["Low", "Medium", "High", "Critical"]
        current_severity = st.session_state.incident.get("severity", "High")
        severity = st.selectbox(
            "Severity", severities,
            index=severities.index(current_severity) if current_severity in severities else 2,
        )
        permission = st.text_input(
            "Permission event", st.session_state.incident["permission_change"]
        )
        approval = st.text_input(
            "Approval context", st.session_state.incident["approval_context"]
        )
    obs = st.text_area(
        "Current observations (one per line)",
        "\n".join(st.session_state.incident.get("observations", [])),
        height=110,
    )
    save = st.form_submit_button("Save current incident details")
    if save:
        candidate = {
            "incident_id": incident_id, "title": title,
            "timestamp": timestamp, "severity": severity,
            "entity": entity, "actor": actor, "permission_change": permission,
            "approval_context": approval,
            "observations": [x.strip() for x in obs.splitlines() if x.strip()],
            "analyst_finding": "", "lesson": "", "outcome": "Undetermined",
        }
        # A submitted edit invalidates every result derived from the prior input,
        # including when the new input fails validation.
        invalidate_incident_results(st.session_state)
        errors = validate_incident(candidate)
        if errors:
            st.error("Please fix the incident details: " + " ".join(errors))
        else:
            st.session_state.incident = normalize_incident(candidate)
            st.success("Current incident saved. Previous analysis and baseline cleared.")

incident = st.session_state.incident
c1, c2, c3 = st.columns(3)
for col, label, value in [
    (c1, "INCIDENT", incident["incident_id"]),
    (c2, "SEVERITY", incident["severity"]),
    (c3, "ENTITY", incident["entity"]),
]:
    with col:
        st.markdown(
            f'<div class="panel"><span class="metric">{label}</span><br>'
            f'<span class="value">{value}</span></div>',
            unsafe_allow_html=True,
        )

if st.button("Run without memory (baseline)", use_container_width=True):
    st.session_state.baseline = (
        f"Current alert: {incident['title']} ({incident['severity']}). "
        f"Entity: {incident['entity']}. Permission event: {incident['permission_change']}. "
        "Without persistent incident memory, this view has no verified context from earlier "
        "investigations. It cannot tell whether this entity was previously reviewed or what "
        "the analyst learned. The current event remains undetermined."
    )
    st.info("Baseline generated without querying Hindsight.")

if st.session_state.baseline:
    st.markdown("### Baseline / no memory")
    st.write(st.session_state.baseline)
    st.caption("This baseline uses only the current incident fields. It has no access to retained history.")

if st.button("Recall history + generate Evidence Delta", type="primary", use_container_width=True):
    if not st.session_state.ready:
        st.warning("Connect Hindsight first.")
    else:
        try:
            with st.spinner("Recalling prior investigations and reflecting on current evidence..."):
                recalled = recall_incidents(st.session_state.client, get_bank_id(), incident)
                reflected = reflect_on_incident(st.session_state.client, get_bank_id(), incident)
                st.session_state.analysis = (recalled, reflected, dict(incident))
        except Exception as exc:
            st.error(f"Investigation failed: {exc}")

if st.session_state.analysis:
    recalled, reflected, current = st.session_state.analysis
    historical_records = recalled_incident_records(
        recalled, exclude_incident_id=current.get("incident_id")
    )
    st.markdown("---")
    st.markdown("### 03 / Evidence Delta")
    st.caption("This deterministic comparison uses a complete structured incident record returned by Hindsight recall.")
    if historical_records:
        recalled_ids = [record[1]["incident_id"] for record in historical_records]
        selected_id = st.selectbox(
            "Historical incident to compare",
            recalled_ids,
            format_func=lambda incident_id: (
                f"{incident_id} · "
                f"{next(record[1].get('timestamp', 'date not recorded') for record in historical_records if record[1]['incident_id'] == incident_id)}"
            ),
        )
        previous = next(record[1] for record in historical_records if record[1]["incident_id"] == selected_id)
        st.caption(
            f"Comparing against recalled incident {previous['incident_id']}"
            + (f" · {previous.get('timestamp')}" if previous.get("timestamp") else "")
            + "."
        )
        st.markdown(
            evidence_delta_markup(evidence_delta(previous, current)),
            unsafe_allow_html=True,
        )
    else:
        st.info(
            "No complete historical incident record was returned by recall, so no "
            "Evidence Delta is shown. Recalled memory snippets are available below, "
            "but are not treated as a structured historical incident."
        )

    st.markdown("### 04 / What Hindsight recalled")
    memories = getattr(recalled, "results", []) or []
    if memories:
        for i, memory in enumerate(memories, 1):
            with st.expander(f"Memory {i}", expanded=(i == 1)):
                st.write(getattr(memory, "text", str(memory)))
    else:
        st.info("No matching memories returned. Seed AT-001, then run the analysis again.")

    st.markdown("### 05 / Hindsight reflection")
    st.write(getattr(reflected, "text", str(reflected)))

    st.markdown("### 06 / Analyst feedback")
    with st.form("feedback_form"):
        finding = st.text_area("What did the analyst establish?")
        lesson = st.text_area("What should future investigations remember?")
        outcome = st.selectbox(
            "Final outcome",
            ["Undetermined", "Benign after review", "Escalated for further investigation", "Confirmed security incident"],
        )
        submit_feedback = st.form_submit_button("Retain analyst feedback in Hindsight")
        if submit_feedback:
            updated = dict(current)
            updated.update({"analyst_finding": finding, "lesson": lesson, "outcome": outcome})
            feedback_errors = []
            if len(finding.strip()) > 2000:
                feedback_errors.append("Analyst finding must be 2,000 characters or fewer.")
            if len(lesson.strip()) > 2000:
                feedback_errors.append("Lesson must be 2,000 characters or fewer.")
            if feedback_errors:
                st.error(" ".join(feedback_errors))
            else:
                updated = normalize_incident(updated)
                try:
                    retain_result = retain_incident(
                        st.session_state.client, get_bank_id(), updated
                    )
                    st.session_state.incident = updated
                    st.session_state.analysis = (recalled, reflected, updated)
                    st.session_state.last_retained_incident = updated
                    if hasattr(retain_result, "model_dump"):
                        retain_result = retain_result.model_dump(mode="json")
                    elif not isinstance(
                        retain_result,
                        (dict, list, str, int, float, bool, type(None)),
                    ):
                        retain_result = str(retain_result)
                    st.session_state.last_hindsight_retain_response = retain_result
                    st.success(
                        f"Feedback retained for {updated['incident_id']}. "
                        "Saving again replaces the same Hindsight document."
                    )
                except Exception as exc:
                    st.error(f"Feedback retain failed: {exc}")

    if st.session_state.last_retained_incident:
        st.markdown("#### Retained incident record")
        st.json(st.session_state.last_retained_incident)
        if st.session_state.last_hindsight_retain_response is not None:
            st.caption("Hindsight retain response")
            st.json(st.session_state.last_hindsight_retain_response)

st.markdown("---")
st.caption("Defensive decision-support prototype. No automated remediation or incident disposition.")
