"""Security helpers and tamper-evident HMAC-SHA256 audit trail."""
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import warnings
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PHI_PATTERNS = [
    re.compile(r"\b(?:MRN|mrn)[:#\s-]*\d{4,10}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    re.compile(r"\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\b(?:Patient\s+Name|Patient)[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+\b", re.IGNORECASE),
]


class SecurityException(Exception):
    """Raised when outbound text matches configured sensitive-identifier patterns."""


class ResourceLimitExceededException(Exception):
    """Raised when computational parameters exceed safety bounds."""


def assert_no_phi(text: str) -> None:
    if not text:
        return
    for pattern in PHI_PATTERNS:
        if pattern.search(str(text)):
            raise SecurityException("Sensitive identifier detected by outbound data guard")


class PHIGuard:
    @staticmethod
    def assert_no_phi(text: str) -> None:
        assert_no_phi(text)

    @staticmethod
    def redact_phi(text: str) -> str:
        result = str(text)
        for pattern in PHI_PATTERNS:
            result = pattern.sub("[REDACTED_IDENTIFIER]", result)
        return result


class AuditTrail:
    """In-memory HMAC chain whose signatures are recomputed during verification."""

    GENESIS_HASH = "GENESIS_BLOCK_0000000000000000"

    def __init__(self, secret_key: Optional[str] = None):
        resolved_key = secret_key or os.getenv("AUDIT_SECRET_KEY")
        if not resolved_key:
            resolved_key = secrets.token_hex(32)
            warnings.warn(
                "AUDIT_SECRET_KEY not set. Using an ephemeral random key; audit signatures will not persist across restarts.",
                RuntimeWarning,
                stacklevel=2,
            )
        self.secret_key = resolved_key.encode("utf-8") if isinstance(resolved_key, str) else resolved_key
        self.logs: List[Dict[str, Any]] = []

    def _signature(self, entry: Dict[str, Any]) -> str:
        sign_string = "|".join(
            [
                str(entry["audit_id"]),
                str(entry["timestamp"]),
                str(entry["actor"]),
                str(entry["actor_tier"]),
                str(entry["event_type"]),
                str(entry["payload_hash"]),
                str(entry["prev_hash"]),
            ]
        )
        return hmac.new(self.secret_key, sign_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def log(self, actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        payload_str = json.dumps(details, sort_keys=True, separators=(",", ":"), default=str)
        assert_no_phi(payload_str)
        entry: Dict[str, Any] = {
            "audit_id": f"AUDIT-{int(time.time() * 1000)}-{len(self.logs) + 1}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "actor_tier": actor_tier,
            "event_type": event_type,
            "payload_hash": hashlib.sha256(payload_str.encode("utf-8")).hexdigest(),
            "prev_hash": self.logs[-1]["current_hash"] if self.logs else self.GENESIS_HASH,
        }
        entry["current_hash"] = self._signature(entry)
        self.logs.append(entry)
        return dict(entry)

    def verify_integrity(self) -> bool:
        expected_prev = self.GENESIS_HASH
        for entry in self.logs:
            if entry.get("prev_hash") != expected_prev:
                return False
            current_hash = entry.get("current_hash")
            if not isinstance(current_hash, str):
                return False
            if not hmac.compare_digest(current_hash, self._signature(entry)):
                return False
            expected_prev = current_hash
        return True

    def get_trail(self) -> List[Dict[str, Any]]:
        return [dict(entry) for entry in self.logs]


GLOBAL_AUDIT = AuditTrail()


class AuditLogger:
    @staticmethod
    def log(actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        return GLOBAL_AUDIT.log(actor, actor_tier, event_type, details)

    @staticmethod
    def get_trail() -> List[Dict[str, Any]]:
        return GLOBAL_AUDIT.get_trail()

    @staticmethod
    def verify_integrity() -> bool:
        return GLOBAL_AUDIT.verify_integrity()


class ActionExecutor:
    @staticmethod
    def execute_with_audit(actor: str, actor_tier: str, action_type: str, fn, *args, **kwargs):
        result = fn(*args, **kwargs)
        AuditLogger.log(actor, actor_tier, action_type, {"status": "SUCCESS"})
        return result
