"""FastAPI service for CRB-65 scoring and retained auxiliary audit endpoints."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from crb65_score import CRB65Engine, ClinicalValueError
from .base import AuditLogger
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="CRB-65 Pneumonia Severity API",
    description="CRB-65 scoring for adults with community-acquired pneumonia in primary care.",
    version="4.0.0",
)


class CRB65Request(BaseModel):
    patient_id: str = Field(default="ANON", max_length=128)
    confusion: bool = False
    respiratory_rate: int = Field(..., ge=1, le=100)
    systolic_bp: int = Field(..., ge=1, le=300)
    diastolic_bp: int = Field(..., ge=1, le=200)
    age_years: int = Field(..., ge=18, le=120)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "crb65-pneumonia-severity", "version": app.version}


@app.post("/api/crb65")
def api_crb65(payload: CRB65Request):
    """Return a NICE-aligned CRB-65 result. No input data are persisted by this endpoint."""
    try:
        return CRB65Engine.evaluate(
            patient_id=payload.patient_id,
            confusion=payload.confusion,
            respiratory_rate=payload.respiratory_rate,
            systolic_bp=payload.systolic_bp,
            diastolic_bp=payload.diastolic_bp,
            age_years=payload.age_years,
        ).to_dict()
    except ClinicalValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/metrics")
def metrics():
    return {
        "auxiliary_dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
    }


# Retained auxiliary endpoints for backwards compatibility.
@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    return supervisor.process_task(payload).to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Request rejected") from exc


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
