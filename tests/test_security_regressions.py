"""Regression tests for audit integrity and CSV boolean parsing."""
from agents.base import AuditTrail
from cli import _parse_bool


def test_audit_integrity_recomputes_hmac_and_detects_tampering():
    trail = AuditTrail(secret_key="unit-test-secret")
    trail.log("worker", "test", "CREATED", {"status": "SUCCESS"})
    trail.log("worker", "test", "COMPLETED", {"status": "SUCCESS"})
    assert trail.verify_integrity() is True

    trail.logs[0]["event_type"] = "TAMPERED"
    assert trail.verify_integrity() is False


def test_audit_trail_getter_returns_copies():
    trail = AuditTrail(secret_key="unit-test-secret")
    trail.log("worker", "test", "CREATED", {"status": "SUCCESS"})
    snapshot = trail.get_trail()
    snapshot[0]["event_type"] = "EXTERNAL_MUTATION"
    assert trail.verify_integrity() is True


def test_auxiliary_cli_false_string_is_not_truthy():
    assert _parse_bool("false") is False
    assert _parse_bool("0") is False
    assert _parse_bool("true") is True
    assert _parse_bool("1") is True
