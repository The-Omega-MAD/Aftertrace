# AFTERTRACE architecture

## One workflow
Preserve lessons from an incident investigation and bring relevant history into the next related investigation.

## Components
- `app.py`: Streamlit interface and analyst workflow orchestration.
- `aftertrace/engine.py`: Hindsight connection, bank initialisation, retain, recall, reflect, recalled-record extraction, and deterministic field comparison.
- `aftertrace/incidents.py`: Incident input validation and timestamp/text normalization.
- `aftertrace/ui_state.py`: Clears cached analysis and retained-result state after submitted incident edits.
- `aftertrace/sample_data.py`: repeatable synthetic scenario.
- `data/sample_incidents.json`: portable sample records.
- `tests/test_engine.py`: Focused checks for Hindsight-facing behavior, validation, provenance, and Streamlit state.

## Hindsight lifecycle
1. `ensure_bank()` creates the AFTERTRACE memory bank when needed.
2. `retain_incident()` stores structured incident content and metadata.
3. `recall_incidents()` searches for prior investigations relevant to the current alert.
4. `reflect_on_incident()` asks Hindsight to synthesise history while separating current facts, historical facts, and unknowns.
5. Analyst feedback is retained as a new incident record with finding, lesson, and outcome.

## Evidence Delta
The initial implementation compares four explicit fields: entity, actor context, permission event, and approval context. This comparison is deterministic and visible. Hindsight supplies contextual memory and reflection. The UI does not pretend model prose is a verified diff.

## Failure handling
- Missing credentials produce an actionable configuration error.
- Hindsight connection and memory failures are surfaced in the UI.
- Empty recall results are shown explicitly.
- No automated remediation or incident closure is implemented.
