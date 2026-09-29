"""Command-line interface for auxiliary audit/API workflows."""
import argparse
import csv
import sys

from agents.base import AuditLogger
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")


def _parse_bool(value) -> bool:
    """Parse common CSV boolean spellings without treating every non-empty string as true."""
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n", ""}:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="crb65-pneumonia-severity", description="CRB-65 auxiliary service CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_audit = subparsers.add_parser("audit", help="Run a single auxiliary audit task")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    p_batch = subparsers.add_parser("batch", help="Batch-process auxiliary audit CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print("CRB65 PNEUMONIA SEVERITY — AUXILIARY AUDIT")
        print(f"Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for alert in dossier.alerts:
            print(f"\n[{alert.urgency.value}] from {alert.origin_worker}:")
            print(f"Summary: {alert.summary}")
            print(f"Details: {alert.technical_details}")
            print(f"Action:  {alert.actionable_remediation}")
        print(f"\nHMAC-SHA256 audit hash: {dossier.audit_hash}")
        return 0

    if args.command == "chat":
        print(supervisor.query_supervisory_chat(" ".join(args.query)))
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0 if valid else 1

    if args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = fieldnames + ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]
        out_rows = []
        for row_number, row in enumerate(rows, start=2):
            try:
                payload = SystemTaskPayload(
                    task_id=row.get("task_id", "TASK-01"),
                    target_identifier=row.get("target_identifier", "TARGET-01"),
                    primary_metric=float(row.get("primary_metric", 15.0)),
                    secondary_metric=float(row.get("secondary_metric", 5.0)),
                    status_descriptor=row.get("status_descriptor", "NOMINAL"),
                    is_critical_flag=_parse_bool(row.get("is_critical_flag", False)),
                )
            except ValueError as exc:
                raise ValueError(f"Invalid CSV data on row {row_number}: {exc}") from exc

            dossier = supervisor.process_task(payload)
            row_dict = dict(row)
            row_dict["overall_urgency"] = dossier.overall_urgency.value
            row_dict["integrity_status"] = dossier.integrity_status.value
            row_dict["total_alerts"] = dossier.total_alerts
            row_dict["audit_hash"] = dossier.audit_hash
            out_rows.append(row_dict)

        with open(args.output, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        import uvicorn
        from agents.api import app

        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
