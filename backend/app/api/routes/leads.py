from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user, get_db
from app.db.models import Lead, PipelineEntry, PipelineStage, User
from app.schemas.lead import LeadCreate, LeadResponse, LeadUpdate
from app.services.audit import register_audit_log

router = APIRouter(prefix="/leads", tags=["leads"])


def to_lead_response(lead: Lead) -> LeadResponse:
    current_stage = None
    if lead.pipeline_entry and lead.pipeline_entry.stage:
        current_stage = lead.pipeline_entry.stage.name

    return LeadResponse(
        id=lead.id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        status=lead.status,
        notes=lead.notes,
        broker_id=lead.broker_id,
        current_stage=current_stage,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


@router.get("", response_model=list[LeadResponse])
def list_leads(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[LeadResponse]:
    leads = db.scalars(
        select(Lead)
        .options(
            selectinload(Lead.pipeline_entry).selectinload(PipelineEntry.stage)
        )
        .order_by(Lead.created_at.desc())
    ).all()
    return [to_lead_response(lead) for lead in leads]


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadResponse:
    lead = Lead(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        source=payload.source,
        notes=payload.notes,
        broker_id=payload.broker_id,
    )
    db.add(lead)
    db.flush()

    initial_stage = db.scalar(
        select(PipelineStage).where(PipelineStage.is_active.is_(True)).order_by(
            PipelineStage.position.asc()
        )
    )
    if initial_stage is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nenhuma etapa ativa configurada para o pipeline.",
        )

    db.add(PipelineEntry(lead_id=lead.id, stage_id=initial_stage.id))
    register_audit_log(
        db,
        actor_id=current_user.id,
        entity="lead",
        entity_id=lead.id,
        action="created",
        payload={"source": lead.source, "stage": initial_stage.name},
    )
    db.commit()
    db.refresh(lead)
    db.refresh(lead, attribute_names=["pipeline_entry"])
    return to_lead_response(lead)


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeadResponse:
    lead = db.scalar(
        select(Lead)
        .options(
            selectinload(Lead.pipeline_entry).selectinload(PipelineEntry.stage)
        )
        .where(Lead.id == lead_id)
    )
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead não encontrado."
        )

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(lead, field, value)

    register_audit_log(
        db,
        actor_id=current_user.id,
        entity="lead",
        entity_id=lead.id,
        action="updated",
        payload=changes,
    )
    db.commit()
    db.refresh(lead)
    return to_lead_response(lead)
