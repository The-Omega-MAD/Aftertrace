import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from streamlit.testing.v1 import AppTest

from aftertrace.engine import (
    evidence_delta,
    incident_memory_text,
    recalled_incident_records,
    recall_incidents,
    retain_incident,
)
from aftertrace.incidents import normalize_incident, validate_incident
from aftertrace.sample_data import FIRST_INCIDENT, FOLLOWUP_INCIDENT
from aftertrace.ui_state import invalidate_incident_results


class IncidentStateTests(unittest.TestCase):
    def test_invalidating_submitted_incident_clears_cached_results(self):
        state = SimpleNamespace(
            analysis=("old recall", "old reflection", dict(FOLLOWUP_INCIDENT)),
            baseline="old baseline",
            last_retained_incident=dict(FOLLOWUP_INCIDENT),
            last_hindsight_retain_response={"status": "success"},
        )
        invalidate_incident_results(state)
        self.assertIsNone(state.analysis)
        self.assertIsNone(state.baseline)
        self.assertIsNone(state.last_retained_incident)
        self.assertIsNone(state.last_hindsight_retain_response)


class IncidentValidationTests(unittest.TestCase):
    def test_valid_sample_incident_passes(self):
        self.assertEqual(validate_incident(dict(FOLLOWUP_INCIDENT)), [])

    def test_required_fields_and_timezone_are_validated(self):
        incident = dict(FOLLOWUP_INCIDENT, incident_id="  ", timestamp="2026-11-04T14:35:00")
        errors = validate_incident(incident)
        self.assertTrue(any(error.startswith("Incident ID is required") for error in errors))
        self.assertTrue(any("include a timezone" in error for error in errors))

    def test_invalid_timestamp_and_oversized_observation_are_rejected(self):
        incident = dict(
            FOLLOWUP_INCIDENT,
            timestamp="not-a-date",
            observations=["x" * 1001],
        )
        errors = validate_incident(incident)
        self.assertTrue(any("valid ISO 8601" in error for error in errors))
        self.assertTrue(any("observations" in error.lower() for error in errors))

    def test_unknown_severity_is_rejected(self):
        errors = validate_incident(dict(FOLLOWUP_INCIDENT, severity="Urgent"))
        self.assertTrue(any("Severity must be" in error for error in errors))

    def test_normalize_trims_fields_and_converts_timestamp_to_utc(self):
        incident = dict(FOLLOWUP_INCIDENT, entity="  Northstar  ", timestamp="2026-11-04T20:05:00+05:30")
        normalized = normalize_incident(incident)
        self.assertEqual(normalized["entity"], "Northstar")
        self.assertEqual(normalized["timestamp"], "2026-11-04T14:35:00Z")

class RecallProvenanceTests(unittest.TestCase):
    def test_summary_only_recall_does_not_create_a_historical_record(self):
        response = SimpleNamespace(results=[SimpleNamespace(text="Northstar was approved previously.")])
        self.assertEqual(recalled_incident_records(response), [])

    def test_complete_recalled_record_can_be_compared(self):
        memory = SimpleNamespace(text=incident_memory_text(FIRST_INCIDENT))
        response = SimpleNamespace(results=[memory])
        records = recalled_incident_records(response)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0][1]["incident_id"], "AT-001")
        delta = evidence_delta(records[0][1], FOLLOWUP_INCIDENT)
        permission = next(row for row in delta if row["dimension"] == "Permission event")
        self.assertEqual(permission["status"], "Changed")

    def test_complete_source_chunk_is_used_when_recalled_text_is_only_a_summary(self):
        memory = SimpleNamespace(text="Previously approved integration.", chunk_id="chunk-1")
        chunk = SimpleNamespace(text=incident_memory_text(FIRST_INCIDENT), truncated=False)
        response = SimpleNamespace(results=[memory], chunks={"chunk-1": chunk})
        records = recalled_incident_records(response)
        self.assertEqual([record[1]["incident_id"] for record in records], ["AT-001"])

    def test_truncated_source_chunk_is_not_treated_as_complete_record(self):
        memory = SimpleNamespace(text="Previously approved integration.", chunk_id="chunk-1")
        chunk = SimpleNamespace(text=incident_memory_text(FIRST_INCIDENT), truncated=True)
        response = SimpleNamespace(results=[memory], chunks={"chunk-1": chunk})
        self.assertEqual(recalled_incident_records(response), [])

    def test_duplicate_recalled_record_is_returned_once(self):
        record_text = incident_memory_text(FIRST_INCIDENT)
        response = SimpleNamespace(results=[SimpleNamespace(text=record_text), SimpleNamespace(text=record_text)])
        self.assertEqual(len(recalled_incident_records(response)), 1)

    def test_current_incident_is_not_offered_as_its_own_historical_comparison(self):
        response = SimpleNamespace(
            results=[SimpleNamespace(text=incident_memory_text(FOLLOWUP_INCIDENT))]
        )
        self.assertEqual(
            recalled_incident_records(response, exclude_incident_id="AT-002"), []
        )

    def test_recall_requests_source_chunks(self):
        client = Mock()
        client.recall.return_value = SimpleNamespace(results=[])
        recall_incidents(client, "bank", FOLLOWUP_INCIDENT)
        self.assertTrue(client.recall.call_args.kwargs["include_chunks"])


class FeedbackPersistenceTests(unittest.TestCase):
    def test_retries_replace_the_same_incident_document(self):
        client = Mock()
        client.retain.return_value = {"status": "success"}
        incident = dict(FOLLOWUP_INCIDENT, analyst_finding="Reviewed", outcome="Undetermined")
        result = retain_incident(client, "bank", incident)
        self.assertEqual(result, {"status": "success"})
        retain_incident(client, "bank", incident)
        self.assertEqual(client.retain.call_count, 2)
        for call in client.retain.call_args_list:
            self.assertEqual(call.kwargs["document_id"], "aftertrace:AT-002")
            self.assertEqual(call.kwargs["update_mode"], "replace")


class IncidentFormTests(unittest.TestCase):
    def make_app(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        return AppTest.from_file(str(app_path)).run()

    def test_saving_changed_incident_clears_stale_analysis_and_baseline(self):
        app = self.make_app()
        app.session_state["analysis"] = ("old recall", "old reflection", {})
        app.session_state["baseline"] = "old baseline"
        app.text_input[0].set_value("AT-003")
        app.button[2].click()
        app.run()
        self.assertIsNone(app.session_state["analysis"])
        self.assertIsNone(app.session_state["baseline"])
        self.assertEqual(app.session_state["incident"]["incident_id"], "AT-003")

    def test_invalid_timestamp_clears_stale_analysis_and_shows_error(self):
        app = self.make_app()
        app.session_state["analysis"] = ("old recall", "old reflection", {})
        app.text_input[4].set_value("yesterday")
        app.button[2].click()
        app.run()
        self.assertIsNone(app.session_state["analysis"])
        self.assertTrue(any("valid ISO 8601" in alert.value for alert in app.error))

    def test_recalled_evidence_delta_renders_without_arrow_table(self):
        app = self.make_app()
        recalled = SimpleNamespace(
            results=[SimpleNamespace(text=incident_memory_text(FIRST_INCIDENT))],
            chunks={},
        )
        app.session_state["analysis"] = (
            recalled,
            SimpleNamespace(text="Synthetic reflection"),
            dict(FOLLOWUP_INCIDENT),
        )
        app.run()
        self.assertFalse(app.exception)
        markup = [element.value for element in app.markdown]
        delta = next(
            (value for value in markup if '<table class="evidence-delta">' in value),
            "",
        )
        self.assertIn("New permission change observed", delta)
        self.assertIn("Changed", delta)


if __name__ == "__main__":
    unittest.main()
