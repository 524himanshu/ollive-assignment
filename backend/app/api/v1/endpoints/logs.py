from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone

from app.db.database import get_db
from app.models.models import InferenceLog
from app.schemas.schemas import InferenceLogCreate, InferenceLogResponse, DashboardStats
from app.services.pii_service import redact_pii

router = APIRouter()


@router.post("/ingest", response_model=InferenceLogResponse, status_code=201)
def ingest_log(payload: InferenceLogCreate, db: Session = Depends(get_db)):
    """
    Receives inference metadata from the SDK.
    Redacts PII from previews before storing.
    """
    # Redact PII from input/output previews
    clean_input, input_pii = redact_pii(payload.input_preview or "")
    clean_output, output_pii = redact_pii(payload.output_preview or "")
    pii_detected = input_pii or output_pii

    log = InferenceLog(
        conversation_id=payload.conversation_id,
        model=payload.model,
        provider=payload.provider,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        latency_ms=payload.latency_ms,
        input_tokens=payload.input_tokens,
        output_tokens=payload.output_tokens,
        total_tokens=payload.total_tokens,
        status=payload.status,
        error_message=payload.error_message,
        input_preview=clean_input[:200] if clean_input else None,
        output_preview=clean_output[:200] if clean_output else None,
        pii_detected=pii_detected,
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Aggregated stats for the dashboard."""
    total = db.query(func.count(InferenceLog.id)).scalar() or 0
    success = db.query(func.count(InferenceLog.id)).filter(
        InferenceLog.status == "success"
    ).scalar() or 0
    avg_latency = db.query(func.avg(InferenceLog.latency_ms)).scalar() or 0
    total_tokens = db.query(func.sum(InferenceLog.total_tokens)).scalar() or 0
    errors = db.query(func.count(InferenceLog.id)).filter(
        InferenceLog.status == "error"
    ).scalar() or 0
    pii_count = db.query(func.count(InferenceLog.id)).filter(
        InferenceLog.pii_detected == True  # noqa: E712
    ).scalar() or 0

    return DashboardStats(
        total_requests=total,
        success_rate=round((success / total * 100), 2) if total > 0 else 0,
        avg_latency_ms=round(float(avg_latency), 2),
        total_tokens=int(total_tokens),
        error_count=errors,
        pii_detected_count=pii_count,
    )


@router.get("/recent", response_model=list[InferenceLogResponse])
def get_recent_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Recent inference logs for the dashboard table."""
    logs = db.query(InferenceLog).order_by(
        desc(InferenceLog.created_at)
    ).limit(limit).all()
    return logs 