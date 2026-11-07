import streamlit as st
from dotenv import load_dotenv

from aftertrace.engine import (
    ensure_bank, evidence_delta, get_bank_id, get_client,
    recall_incidents, reflect_on_incident, retain_incident,
)
from aftertrace.sample_data import FIRST_INCIDENT, FOLLOWUP_INCIDENT

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
if "incident" not in st.session_state:
    st.session_state.incident = dict(FOLLOWUP_INCIDENT)

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
        incident_id = st.text_input("Incident ID", "AT-002")
        title = st.text_input("Alert title", "OAuth application permission change")
        entity = st.text_input("Application / entity", "Northstar Calendar Connector")
        actor = st.text_input("Actor context", "Unverified actor context")
    with right:
        severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], index=2)
        permission = st.text_input("Permission event", "New permission change observed")
        approval = st.text_input("Approval context", "Not yet verified for this event")
    obs = st.text_area(
        "Current observations (one per line)",
        "\n".join(FOLLOWUP_INCIDENT["observations"]),
        height=110,
    )
    save = st.form_submit_button("Save current incident details")
    if save:
        st.session_state.incident = {
            "incident_id": incident_id, "title": title,
            "timestamp": FOLLOWUP_INCIDENT["timestamp"], "severity": severity,
            "entity": entity, "actor": actor, "permission_change": permission,
            "approval_context": approval,
            "observations": [x.strip() for x in obs.splitlines() if x.strip()],
            "analyst_finding": "", "lesson": "", "outcome": "Undetermined",
        }
        st.success("Current incident saved.")

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

if st.button("Recall history + generate Evidence Delta", type="primary", use_container_width=True):
    if not st.session_state.ready:
        st.warning("Connect Hindsight first.")
    else:
        try:
            with st.spinner("Recalling prior investigations and reflecting on current evidence..."):
                recalled = recall_incidents(st.session_state.client, get_bank_id(), incident)
                reflected = reflect_on_incident(st.session_state.client, get_bank_id(), incident)
                st.session_state.analysis = (recalled, reflected, incident)
        except Exception as exc:
            st.error(f"Investigation failed: {exc}")

if st.session_state.analysis:
    recalled, reflected, current = st.session_state.analysis
    st.markdown("---")
    st.markdown("### 03 / Evidence Delta")
    st.caption("This field-by-field comparison is deterministic. Hindsight supplies historical context and reflection.")
    st.dataframe(evidence_delta(FIRST_INCIDENT, current), use_container_width=True, hide_index=True)

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
            try:
                retain_incident(st.session_state.client, get_bank_id(), updated)
                st.success("Analyst feedback retained for future investigations.")
            except Exception as exc:
                st.error(f"Feedback retain failed: {exc}")

st.markdown("---")
st.caption("Defensive decision-support prototype. No automated remediation or incident disposition.")
